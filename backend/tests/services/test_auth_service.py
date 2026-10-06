from unittest.mock import MagicMock, patch

import pytest

from app.core.security import validated_Pass
from app.modules.auth.authSchema import RegisterRequest, ResetPasswordSchema


class TestRegisterRequestValidation:
    def test_valid_register_request(self):
        data = RegisterRequest(name="Test", email="test@example.com", password="Strong@Pass1")
        assert data.name == "Test"
        assert data.email == "test@example.com"

    def test_invalid_email_raises(self):
        with pytest.raises(Exception):
            RegisterRequest(name="Test", email="not-email", password="Strong@Pass1")

    def test_weak_password_is_rejected(self):
        with pytest.raises(ValueError):
            RegisterRequest(name="Test", email="test@example.com", password="weak")


class TestResetPasswordSchema:
    def test_passwords_match(self):
        data = ResetPasswordSchema(new_password="Strong@Pass1", confirm_password="Strong@Pass1")
        assert data.new_password == data.confirm_password

    def test_passwords_mismatch_raises(self):
        with pytest.raises(ValueError, match="do not match"):
            ResetPasswordSchema(new_password="Strong@Pass1", confirm_password="Diff@Pass1")

    def test_weak_new_password_raises(self):
        with pytest.raises(Exception):
            ResetPasswordSchema(new_password="weak", confirm_password="weak")


class TestAuthService:
    @pytest.mark.asyncio
    async def test_register_service_creates_user(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        with patch("app.modules.auth.authService.User") as MockUser:
            mock_user = MagicMock()
            mock_user.id = "test-user-id"
            mock_user.name = "Test"
            mock_user.email = "new@example.com"
            MockUser.return_value = mock_user

            from app.modules.auth.authService import register_service

            data = RegisterRequest(name="Test", email="new@example.com", password="Strong@Pass1")
            result = register_service(mock_db, data)
            assert result is not None
            mock_db.add.assert_called()
            mock_db.commit.assert_called()

    @pytest.mark.asyncio
    async def test_register_service_duplicate_email(self):
        mock_db = MagicMock()
        existing_user = MagicMock()
        existing_user.email = "existing@example.com"
        mock_db.query.return_value.filter.return_value.first.return_value = existing_user

        from app.modules.auth.authService import register_service

        data = RegisterRequest(name="Test", email="existing@example.com", password="Strong@Pass1")
        with pytest.raises(Exception):
            register_service(mock_db, data)

    @pytest.mark.asyncio
    async def test_login_service_success(self):
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.email = "test@example.com"
        mock_user.name = "Test"
        mock_user.password_hash = "$2b$12$" + "a" * 53
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_user

        with patch("app.modules.auth.authService.password_hasher.verify", return_value=True):
            with patch("app.modules.auth.authService.generate_token", return_value="fake-token"):
                from app.modules.auth.authSchema import LoginRequest
                from app.modules.auth.authService import login_service

                data = LoginRequest(email="test@example.com", password="Strong@Pass1")
                result = login_service(mock_db, data)
                assert result is not None
                assert "access_token" in result or "refresh_token" in result

    @pytest.mark.asyncio
    async def test_login_service_wrong_password(self):
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.password_hash = "$2b$12$" + "a" * 53
        mock_db.query.return_value.filter.return_value.first.return_value = mock_user

        with patch("app.modules.auth.authService.password_hasher.verify", return_value=False):
            from app.modules.auth.authSchema import LoginRequest
            from app.modules.auth.authService import login_service

            data = LoginRequest(email="test@example.com", password="WrongPass@1")
            with pytest.raises(Exception):
                login_service(mock_db, data)

    @pytest.mark.asyncio
    async def test_login_service_user_not_found(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        from app.modules.auth.authSchema import LoginRequest
        from app.modules.auth.authService import login_service

        data = LoginRequest(email="nobody@example.com", password="Strong@Pass1")
        with pytest.raises(Exception):
            login_service(mock_db, data)

    @pytest.mark.asyncio
    async def test_refresh_access_token_invalid(self):
        from app.modules.auth.authService import refresh_access_token_service

        with pytest.raises(Exception):
            refresh_access_token_service("invalid-token")

    @pytest.mark.asyncio
    async def test_resend_otp_success(self, mock_redis):
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = MagicMock()

        mock_redis.get.return_value = None

        from app.modules.auth.authSchema import SendEmailSchema
        from app.modules.auth.authService import resend_otp_service

        data = SendEmailSchema(email="test@example.com")
        result = await resend_otp_service(data, mock_db)
        assert result["message"] == "OTP resent successfully"
        mock_redis.set.assert_awaited()

    @pytest.mark.asyncio
    async def test_resend_otp_user_not_found(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        from app.modules.auth.authSchema import SendEmailSchema
        from app.modules.auth.authService import resend_otp_service

        data = SendEmailSchema(email="nobody@example.com")
        with pytest.raises(Exception):
            await resend_otp_service(data, mock_db)

    @pytest.mark.asyncio
    async def test_resend_otp_cooldown(self, mock_redis):
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = MagicMock()

        mock_redis.get.return_value = "1"

        from app.modules.auth.authSchema import SendEmailSchema
        from app.modules.auth.authService import resend_otp_service

        data = SendEmailSchema(email="test@example.com")
        with pytest.raises(Exception, match=r"please wait|Please wait"):
            await resend_otp_service(data, mock_db)

    @pytest.mark.asyncio
    async def test_send_verification_email_user_not_found(self):
        mock_db = MagicMock()
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        from app.modules.auth.authSchema import SendEmailSchema
        from app.modules.auth.authService import send_verification_email_service

        data = SendEmailSchema(email="nobody@example.com")
        with pytest.raises(Exception):
            await send_verification_email_service(data, mock_db)
