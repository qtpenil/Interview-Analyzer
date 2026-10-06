from unittest.mock import MagicMock

from app.shared.response_handler.response_cookie_setter import (
    clear_auth_cookie,
    set_auth_cookie,
)


class TestSetAuthCookie:
    def test_set_access_token_cookie(self):
        response = MagicMock()
        set_auth_cookie(response, "test-token", "access")
        response.set_cookie.assert_called_once()
        call_kwargs = response.set_cookie.call_args[1]
        assert call_kwargs["value"] == "test-token"
        assert call_kwargs["httponly"] is True

    def test_set_refresh_token_cookie(self):
        response = MagicMock()
        set_auth_cookie(response, "refresh-token", "refresh")
        response.set_cookie.assert_called_once()
        call_kwargs = response.set_cookie.call_args[1]
        assert call_kwargs["value"] == "refresh-token"


class TestClearAuthCookie:
    def test_clear_access_token(self):
        response = MagicMock()
        clear_auth_cookie(response, "access")
        response.delete_cookie.assert_called_once()

    def test_clear_refresh_token(self):
        response = MagicMock()
        clear_auth_cookie(response, "refresh")
        response.delete_cookie.assert_called_once()
