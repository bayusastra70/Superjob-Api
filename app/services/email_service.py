from loguru import logger
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from jinja2 import Environment, FileSystemLoader
from brevo_python import ApiClient, Configuration
from brevo_python.api.transactional_emails_api import TransactionalEmailsApi
from brevo_python.models.send_smtp_email import SendSmtpEmail
from brevo_python.models.send_smtp_email_to import SendSmtpEmailTo
from brevo_python.models.send_smtp_email_sender import SendSmtpEmailSender

from app.core.config import settings

class EmailService:
    def __init__(self):
        self.api_key = settings.BREVO_API_KEY
        self.sender_email = settings.SENDER_EMAIL
        self.sender_name = settings.SENDER_NAME
        self.support_email = settings.SUPPORT_EMAIL
        
        # Initialize Jinja2 Env
        template_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "templates")
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))

        # Initialize Brevo API
        if self.api_key:
            config = Configuration()
            config.api_key['api-key'] = self.api_key
            self.api_client = ApiClient(config)
            self.api_instance = TransactionalEmailsApi(self.api_client)
        else:
            logger.warning("BREVO_API_KEY not set. Email service will not send actual emails.")
            self.api_instance = None

    def render_template(self, template_name: str, context: Dict[str, Any]) -> str:
        """Render HTML template with context variables"""
        try:
            template = self.jinja_env.get_template(template_name)
            return template.render(**context)
        except Exception as e:
            logger.error(f"Error rendering template {template_name}: {e}")
            raise

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        to_name: Optional[str] = None
    ) -> bool:
        """Send email using Brevo"""
        if not self.api_instance:
            logger.info(f"[MOCK EMAIL] To: {to_email}, Subject: {subject}")
            return True

        try:
            sender = SendSmtpEmailSender(name=self.sender_name, email=self.sender_email)
            to = [SendSmtpEmailTo(email=to_email, name=to_name)]
            
            send_smtp_email = SendSmtpEmail(
                to=to,
                sender=sender,
                subject=subject,
                html_content=html_content
            )

            api_response = self.api_instance.send_transac_email(send_smtp_email)
            logger.info(f"Email sent to {to_email}. Message ID: {api_response.message_id}")
            return True

        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {e}")
            return False

    def send_otp_email(self, to_email: str, otp_code: str, name: str = ""):
        """Send OTP verification email"""
        try:
            # Prepare context for template
            context = {
                "otp_code": otp_code,
                "expire_minutes": 5, # As per plan
                "support_url": f"mailto:{self.support_email}",
                "support_email": self.support_email,
                "current_year": datetime.now().year,
                "name": name
            }
            
            # Render template
            html_content = self.render_template("registration.html", context)
            
            # Send
            return self.send_email(
                to_email=to_email,
                subject="Verifikasi Email Anda - SuperJob",
                html_content=html_content,
                to_name=name
            )
            
        except Exception as e:
            logger.error(f"Failed to send OTP email: {e}")
            return False
            
    def send_success_registration_email(self, to_email: str, name: str = ""):
        """
        Send success registration email after verification
        """
        try:
            # Prepare context for template
            context = {
                "support_url": f"mailto:{self.support_email}",
                "support_email": self.support_email,
                "current_year": datetime.now().year,
                "name": name,
            }
            
            # Render template
            html_content = self.render_template("success_registration.html", context)
            
            # Send
            return self.send_email(
                to_email=to_email,
                subject="Registrasi Berhasil - SuperJob",
                html_content=html_content,
                to_name=name
            )
            
        except Exception as e:
            logger.error(f"Failed to send success registration email: {e}")
            return False

    def send_reset_password_email(self, to_email: str, name: str, reset_link: str):
        """
        Send password reset email
        """
        try:
            # Prepare context for template
            context = {
                "support_url": f"mailto:{self.support_email}",
                "support_email": self.support_email,
                "name": name,
                "reset_link": reset_link
            }
            
            # Render template
            html_content = self.render_template("reset_password.html", context)
            
            # Send
            return self.send_email(
                to_email=to_email,
                subject="Atur Ulang Kata Sandi - SuperJob",
                html_content=html_content,
                to_name=name
            )
            
            
        except Exception as e:
            logger.error(f"Failed to send reset password email: {e}")
            return False

    def send_corporate_registration_email(self, to_email: str, name: str, company_name: str):
        """
        Send corporate registration success email
        """
        try:
            # Prepare context for template
            context = {
                "support_url": f"mailto:{self.support_email}",
                "support_email": self.support_email,
                "current_year": datetime.now().year,
                "name": name,
                "company_name": company_name
            }

            # Render template
            html_content = self.render_template("registration_corporate.html", context)

            # Send
            return self.send_email(
                to_email=to_email,
                subject="Pendaftaran Rekruter Berhasil - SuperJob",
                html_content=html_content,
                to_name=name
            )

        except Exception as e:
            logger.error(f"Failed to send corporate registration email: {e}")
            return False

    def send_company_verified_email(self, to_email: str, name: str, company_name: str):
        """Send company verification success email"""
        try:
            context = {
                "support_url": f"mailto:{self.support_email}",
                "support_email": self.support_email,
                "current_year": datetime.now().year,
                "name": name,
                "company_name": company_name
            }
            html_content = self.render_template("company_verified.html", context)
            return self.send_email(
                to_email=to_email,
                subject="Perusahaan Terverifikasi - SuperJob",
                html_content=html_content,
                to_name=name
            )
        except Exception as e:
            logger.error(f"Failed to send company verified email: {e}")
            return False

email_service = EmailService()
