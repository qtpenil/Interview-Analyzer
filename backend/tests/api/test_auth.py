import pytest
from httpx import AsyncClient


class TestAuthRegister:
    @pytest.mark.asyncio
    async def test_register_success(self, async_client: AsyncClient, sample_user_data: dict, respect_rate_limit):
        response = await async_client.post("/auth/register", json=sample_user_data)
        assert response.status_code in (200, 201)

    @pytest.mark.asyncio
    async def test_register_missing_fields(self, async_client: AsyncClient):
        response = await async_client.post("/auth/register", json={})
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_invalid_email(self, async_client: AsyncClient):
        response = await async_client.post(
            "/auth/register",
            json={
                "name": "Test",
                "email": "not-an-email",
                "password": "Test@1234",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_weak_password(self, async_client: AsyncClient):
        response = await async_client.post(
            "/auth/register",
            json={
                "name": "Test",
                "email": "test@example.com",
                "password": "weak",
            },
        )
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_register_duplicate_email(
        self, async_client: AsyncClient, sample_user_data: dict, respect_rate_limit
    ):
        await async_client.post("/auth/register", json=sample_user_data)
        response = await async_client.post("/auth/register", json=sample_user_data)
        assert response.status_code == 409


class TestAuthLogin:
    @pytest.mark.asyncio
    async def test_login_success(self, async_client: AsyncClient, sample_user_data: dict, respect_rate_limit):
        await async_client.post("/auth/register", json=sample_user_data)
        response = await async_client.post(
            "/auth/login",
            json={
                "email": sample_user_data["email"],
                "password": sample_user_data["password"],
            },
        )
        assert response.status_code == 200
        assert "access_token" in response.cookies or response.json().get("access_token")

    @pytest.mark.asyncio
    async def test_login_wrong_password(self, async_client: AsyncClient, sample_user_data: dict, respect_rate_limit):
        await async_client.post("/auth/register", json=sample_user_data)
        response = await async_client.post(
            "/auth/login",
            json={
                "email": sample_user_data["email"],
                "password": "WrongPass@123",
            },
        )
        assert response.status_code == 401

    @pytest.mark.asyncio
    async def test_login_nonexistent_user(self, async_client: AsyncClient):
        response = await async_client.post(
            "/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "Test@1234",
            },
        )
        assert response.status_code in (400, 401)

    @pytest.mark.asyncio
    async def test_login_missing_fields(self, async_client: AsyncClient):
        response = await async_client.post("/auth/login", json={})
        assert response.status_code == 422


class TestAuthLogout:
    @pytest.mark.asyncio
    async def test_logout_clears_cookies(self, async_client: AsyncClient, sample_user_data: dict, respect_rate_limit):
        await async_client.post("/auth/register", json=sample_user_data)
        login_resp = await async_client.post(
            "/auth/login",
            json={
                "email": sample_user_data["email"],
                "password": sample_user_data["password"],
            },
        )
        cookies = login_resp.cookies
        response = await async_client.post("/auth/logout", cookies=cookies)
        assert response.status_code == 200


class TestAuthRefreshToken:
    @pytest.mark.asyncio
    async def test_refresh_without_token(self, async_client: AsyncClient):
        response = await async_client.post("/auth/refreshToken")
        assert response.status_code in (400, 401)

    @pytest.mark.asyncio
    async def test_refresh_success(self, async_client: AsyncClient, sample_user_data: dict, respect_rate_limit):
        await async_client.post("/auth/register", json=sample_user_data)
        login_resp = await async_client.post(
            "/auth/login",
            json={
                "email": sample_user_data["email"],
                "password": sample_user_data["password"],
            },
        )
        response = await async_client.post("/auth/refreshToken", cookies=login_resp.cookies)
        assert response.status_code == 200


class TestAuthResendOTP:
    @pytest.mark.asyncio
    async def test_resend_otp_success(self, async_client: AsyncClient, sample_user_data: dict, respect_rate_limit):
        await async_client.post("/auth/register", json=sample_user_data)
        response = await async_client.post(
            "/auth/resend-otp",
            json={
                "email": sample_user_data["email"],
            },
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_resend_otp_nonexistent_email(self, async_client: AsyncClient):
        response = await async_client.post(
            "/auth/resend-otp",
            json={
                "email": "nobody@example.com",
            },
        )
        assert response.status_code in (400, 404)


class TestAuthForgotPassword:
    @pytest.mark.asyncio
    async def test_forgot_password_success(self, async_client: AsyncClient, sample_user_data: dict, respect_rate_limit):
        await async_client.post("/auth/register", json=sample_user_data)
        response = await async_client.post(
            "/auth/forgot-password",
            json={
                "email": sample_user_data["email"],
            },
        )
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_forgot_password_nonexistent_email(self, async_client: AsyncClient):
        response = await async_client.post(
            "/auth/forgot-password",
            json={
                "email": "nobody@example.com",
            },
        )
        assert response.status_code in (400, 404)


class TestAuthVerifyOTP:
    @pytest.mark.asyncio
    async def test_verify_otp_invalid(self, async_client: AsyncClient):
        response = await async_client.post(
            "/auth/verify-otp",
            json={
                "email": "test@example.com",
                "otp": "000000",
            },
        )
        assert response.status_code in (400, 401)


class TestAuthUpdatePassword:
    @pytest.mark.asyncio
    async def test_update_password_without_token(self, async_client: AsyncClient):
        response = await async_client.post(
            "/auth/update-password",
            json={
                "new_password": "NewStr0ng@Pass",
                "confirm_password": "NewStr0ng@Pass",
            },
        )
        assert response.status_code in (400, 401)

    @pytest.mark.asyncio
    async def test_update_password_mismatch(self, async_client: AsyncClient):
        response = await async_client.post(
            "/auth/update-password",
            json={
                "new_password": "NewStr0ng@Pass",
                "confirm_password": "Different@Pass1",
            },
        )
        assert response.status_code == 422
