import io
import uuid
from unittest.mock import patch

import pytest
from httpx import AsyncClient


class TestInterviewUpload:
    @pytest.mark.asyncio
    async def test_upload_without_auth(self, async_client: AsyncClient):
        response = await async_client.post(
            "/interviews/upload",
            files={"file": ("test.mp4", b"fake video content", "video/mp4")},
        )
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_upload_without_file(self, async_client: AsyncClient, auth_cookies):
        response = await async_client.post("/interviews/upload", cookies=auth_cookies)
        assert response.status_code == 422

    @pytest.mark.asyncio
    async def test_upload_success(self, async_client: AsyncClient, auth_cookies):
        cookies = auth_cookies

        with patch("app.modules.interview.service.save_video_file", return_value="/tmp/test.mp4"):
            with patch("app.modules.interview.service.create_interview") as mock_create:
                mock_interview = MagicMock()
                mock_interview.id = uuid.uuid4()
                mock_interview.status = MagicMock()
                mock_interview.status.value = "UPLOADED"
                mock_create.return_value = mock_interview

                with patch("app.tasks.video_tasks.process_video_to_audio.delay"):
                    response = await async_client.post(
                        "/interviews/upload",
                        cookies=cookies,
                        files={"file": ("test.mp4", b"fake video content", "video/mp4")},
                    )
                    assert response.status_code == 200
                    data = response.json()
                    assert data["success"] is True
                    assert data["message"] == "Interview uploaded successfully"
                    assert "interview_id" in data["data"]
                    assert data["data"]["status"] == "UPLOADED"


class TestInterviewCancel:
    @pytest.mark.asyncio
    async def test_cancel_without_auth(self, async_client: AsyncClient):
        response = await async_client.post(f"/interviews/{uuid.uuid4()}/cancel")
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_interview(self, async_client: AsyncClient, auth_cookies):
        cookies = auth_cookies

        with patch("app.modules.interview.service.cancel_interview") as mock_cancel:
            from app.shared.exceptions.custom_exceptions import ResourceNotFoundException

            mock_cancel.side_effect = ResourceNotFoundException("Not found")
            response = await async_client.post(
                f"/interviews/{uuid.uuid4()}/cancel",
                cookies=cookies,
            )
            assert response.status_code == 404


class TestInterviewStatus:
    @pytest.mark.asyncio
    async def test_status_endpoint_exists(self, async_client: AsyncClient):
        response = await async_client.get(f"/interviews/{uuid.uuid4()}/status")
        assert response.status_code in (401, 403)


class TestInterviewList:
    @pytest.mark.asyncio
    async def test_list_without_auth(self, async_client: AsyncClient):
        response = await async_client.get("/interviews/list")
        assert response.status_code in (401, 403)

    @pytest.mark.asyncio
    async def test_list_success(self, async_client: AsyncClient, auth_cookies):
        response = await async_client.get("/interviews/list", cookies=auth_cookies)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_with_status_filter(self, async_client: AsyncClient, auth_cookies):
        response = await async_client.get("/interviews/list?status=COMPLETED", cookies=auth_cookies)
        assert response.status_code == 200

    @pytest.mark.asyncio
    async def test_list_pagination(self, async_client: AsyncClient, auth_cookies):
        response = await async_client.get("/interviews/list?page=1&page_size=10", cookies=auth_cookies)
        assert response.status_code == 200


class TestInterviewDetail:
    @pytest.mark.asyncio
    async def test_detail_nonexistent(self, async_client: AsyncClient, auth_cookies):
        response = await async_client.get(f"/interviews/{uuid.uuid4()}", cookies=auth_cookies)
        assert response.status_code == 404


class TestInterviewReport:
    @pytest.mark.asyncio
    async def test_report_nonexistent(self, async_client: AsyncClient, auth_cookies):
        response = await async_client.get(f"/interviews/{uuid.uuid4()}/report", cookies=auth_cookies)
        assert response.status_code in (400, 404)


def MagicMock():
    from unittest.mock import MagicMock as MM

    return MM()
