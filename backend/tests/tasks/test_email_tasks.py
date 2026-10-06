from unittest.mock import MagicMock, patch

import pytest


class TestSendOTPEmail:
    def test_send_otp_email_success(self):
        from app.tasks.email_tasks import send_otp_email

        with patch("smtplib.SMTP") as mock_smtp:
            send_otp_email("test@example.com", "123456")
            mock_smtp.return_value.send_message.assert_called_once()

    def test_send_otp_email_content(self):
        from app.tasks.email_tasks import send_otp_email

        with patch("smtplib.SMTP") as mock_smtp:
            send_otp_email("user@example.com", "654321")
            call_args = mock_smtp.return_value.send_message.call_args
            msg = call_args[0][0]
            assert msg["To"] == "user@example.com"
            assert "654321" in msg.as_string()

    def test_send_otp_smtp_failure(self):
        from app.tasks.email_tasks import send_otp_email

        with patch("smtplib.SMTP", side_effect=ConnectionRefusedError):
            with pytest.raises(Exception):
                send_otp_email("test@example.com", "123456")

    def test_send_otp_invalid_email(self):
        from app.tasks.email_tasks import send_otp_email

        with patch("smtplib.SMTP", side_effect=Exception("Invalid email")):
            with pytest.raises(Exception):
                send_otp_email("invalid", "123456")
