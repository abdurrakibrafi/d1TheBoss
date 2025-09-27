import sib_api_v3_sdk
from sib_api_v3_sdk.rest import ApiException
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class BrevoEmailService:
    def __init__(self):
        configuration = sib_api_v3_sdk.Configuration()
        configuration.api_key['api-key'] = settings.BREVO_API_KEY
        self.api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
            sib_api_v3_sdk.ApiClient(configuration)
        )

    def send_transactional_email(self, to_email, to_name, subject, html_content, text_content=None):
        """Send a single transactional email"""
        try:
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=[{"email": to_email, "name": to_name}],
                sender={"name": settings.BREVO_FROM_NAME, "email": settings.BREVO_FROM_EMAIL},
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )

            api_response = self.api_instance.send_transac_email(send_smtp_email)
            logger.info(f"Email sent successfully to {to_email}")
            return api_response

        except ApiException as e:
            logger.error(f"Exception when sending email: {e}")
            return None

    def create_campaign(self, name, subject, html_content, list_ids=None, scheduled_at=None):
        """Create an email campaign"""
        try:
            campaign_api = sib_api_v3_sdk.EmailCampaignsApi(
                sib_api_v3_sdk.ApiClient(sib_api_v3_sdk.Configuration())
            )

            email_campaigns = sib_api_v3_sdk.CreateEmailCampaign(
                name=name,
                subject=subject,
                sender={
                    "name": settings.BREVO_FROM_NAME,
                    "email": settings.BREVO_FROM_EMAIL
                },
                type="classic",
                html_content=html_content,
                recipients={"listIds": list_ids or []},
                scheduled_at=scheduled_at
            )

            api_response = campaign_api.create_email_campaign(email_campaigns)
            logger.info(f"Campaign '{name}' created successfully")
            return api_response

        except ApiException as e:
            logger.error(f"Exception when creating campaign: {e}")
            return None