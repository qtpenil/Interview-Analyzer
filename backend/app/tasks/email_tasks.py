import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from app.celery_app import celery_app
from app.core.config import settings
from app.shared.logger.logger import get_logger

logger = get_logger(__name__)


@celery_app.task(bind=True, max_retries=5, default_retry_delay=30)
def send_otp_email(self, to_email: str, otp_code: str):
    if not settings.SMTP_USER or not settings.SMTP_PASSWORD:
        return

    subject = "Your Password Reset OTP"

    # Plaintext fallback for clients that don't render HTML
    plain_body = f"""Hello,

Your One-Time Password (OTP) for resetting your password is: {otp_code}

This OTP is valid for 10 minutes.

If you did not request this, please ignore this email."""

    html_body = f"""
    <!DOCTYPE html>
    <html>
    <body style="margin:0; padding:0; background-color:#F5F9FF; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif;">
      <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="background-color:#F5F9FF; padding:40px 20px;">
        <tr>
          <td align="center">
            <table role="presentation" width="480" cellpadding="0" cellspacing="0" style="max-width:480px; width:100%; background:#FFFFFF; border-radius:12px; overflow:hidden; box-shadow:0 20px 50px -18px rgba(15,23,42,0.08); border:1px solid rgba(56,98,180,0.10);">

              <!-- Header -->
              <tr>
                <td style="padding:32px 40px; text-align:center; border-bottom:1px solid rgba(56,98,180,0.10);">
                  <div style="width:48px; height:48px; background:linear-gradient(135deg, #7C3AED, #22D3EE); border-radius:12px; margin:0 auto 12px auto;"></div>
                  <h1 style="margin:0; color:#0F172A; font-size:20px; font-weight:700; letter-spacing:-0.3px;">Interview AI</h1>
                </td>
              </tr>

              <!-- Body -->
              <tr>
                <td style="padding:36px 40px 20px 40px;">
                  <h2 style="margin:0 0 8px 0; color:#0F172A; font-size:19px; font-weight:600;">Password Reset OTP</h2>
                  <p style="margin:0 0 24px 0; color:#64748B; font-size:14px; line-height:1.6;">
                    Use the One-Time Password below to reset your password. Don't share this code with anyone.
                  </p>

                  <!-- OTP box -->
                  <table role="presentation" width="100%" cellpadding="0" cellspacing="0" style="margin:0 0 24px 0;">
                    <tr>
                      <td align="center" style="background-color:#F5F9FF; border:1px solid rgba(79,70,229,0.18); border-radius:10px; padding:20px 0;">
                        <span style="color:#4F46E5; font-size:32px; font-weight:700; letter-spacing:10px; font-family: 'Courier New', monospace;">
                          {otp_code}
                        </span>
                      </td>
                    </tr>
                  </table>

                  <!-- Expiry notice -->
                  <table role="presentation" width="100%" cellpadding="0" cellspacing="0">
                    <tr>
                      <td style="padding:12px 16px; background-color:rgba(245,158,11,0.10); border-left:3px solid #F59E0B; border-radius:6px; color:#64748B; font-size:13px; text-align:left; line-height:1.5;">
                        This code expires in <strong style="color:#0F172A;">10 minutes</strong>.
                      </td>
                    </tr>
                  </table>
                </td>
              </tr>

              <!-- Footer -->
              <tr>
                <td style="padding:24px 40px 32px 40px; border-top:1px solid rgba(56,98,180,0.10);">
                  <p style="margin:0 0 8px 0; color:#64748B; font-size:12px; text-align:center; line-height:1.6;">
                    If you didn't request this, you can safely ignore this email — your account is still secure.
                  </p>
                  <p style="margin:0; color:#94A3B8; font-size:12px; text-align:center;">
                    — The Interview AI Team
                  </p>
                </td>
              </tr>

              <!-- Spacer for email client safety -->
              <tr>
                <td style="height:8px; background:#FFFFFF;"></td>
              </tr>

            </table>
          </td>
        </tr>
      </table>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["From"] = settings.FROM_EMAIL or settings.SMTP_USER
    msg["To"] = to_email
    msg["Subject"] = subject

    # Attach plain text first, then HTML — clients render the last part they support
    msg.attach(MIMEText(plain_body, "plain"))
    msg.attach(MIMEText(html_body, "html"))

    try:
        server = smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT, timeout=10)
        server.starttls()
        server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
        server.send_message(msg)
        server.quit()
        logger.info("Successfully sent OTP email to %s", to_email)
    except Exception as e:
        logger.error("Failed to send email to %s: %s", to_email, e)
        raise self.retry(exc=e, countdown=30)
