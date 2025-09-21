import os
import json
from jinja2 import Environment, FileSystemLoader
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from config.system_settings import SystemSettings

class EmailService:
    def __init__(self, template_dir: str):
        self.template_dir = template_dir
        self.jinja_env = Environment(loader=FileSystemLoader(template_dir))
        self.sendgrid_client = SendGridAPIClient(os.environ.get('SENDGRID_API_KEY'))
        self.from_email = os.environ.get("SENDGRID_FROM_EMAIL")

        if not self.from_email:
            raise ValueError("SENDGRID_FROM_EMAIL environment variable not set.")

    def _load_manifest(self, template_name: str) -> dict:
        manifest_path = os.path.join(self.template_dir, f"{template_name}.json")
        with open(manifest_path, 'r') as f:
            return json.load(f)

    def _validate_params(self, required_params: list, provided_params: dict):
        for param in required_params:
            if param not in provided_params:
                raise ValueError(f"Missing required parameter: {param}")

    def notify(self, template_name: str, recipient_email: str, params: dict):
        try:
            manifest = self._load_manifest(template_name)
            self._validate_params(manifest['required_params'], params)

            # Inject system settings into template parameters
            template_params = {
                'subject': manifest['subject'],
                **params,
                # Inject all system settings for branding
                'branding': {
                    'accent_color': SystemSettings.BRANDING_ACCENT_COLOR,
                    'primary_color': SystemSettings.BRANDING_PRIMARY_COLOR,
                    'secondary_color': SystemSettings.BRANDING_SECONDARY_COLOR,
                    'logo': SystemSettings.BRANDING_LOGO,
                    'company_name': SystemSettings.BRANDING_COMPANY_NAME,
                    'support_email': SystemSettings.BRANDING_SUPPORT_EMAIL,
                    'footer_text': SystemSettings.BRANDING_FOOTER_TEXT,
                },
                'email_styling': {
                    'background_color': SystemSettings.EMAIL_BACKGROUND_COLOR,
                    'container_max_width': SystemSettings.EMAIL_CONTAINER_MAX_WIDTH,
                    'header_padding': SystemSettings.EMAIL_HEADER_PADDING,
                    'body_padding': SystemSettings.EMAIL_BODY_PADDING,
                    'footer_padding': SystemSettings.EMAIL_FOOTER_PADDING,
                }
            }

            template = self.jinja_env.get_template(f"{template_name}.html")
            html_content = template.render(**template_params)

            message = Mail(
                from_email=self.from_email,
                to_emails=recipient_email,
                subject=manifest['subject'],
                html_content=html_content
            )
            
            response = self.sendgrid_client.send(message)
            print(f"Email sent to {recipient_email} using template '{template_name}'. Status: {response.status_code}")

        except Exception as e:
            print(f"Failed to send email: {e}")
            # In a production app, you'd likely have more robust error handling here
            raise

# Create a single, globally accessible instance of the EmailService
template_path = os.path.join(os.path.dirname(__file__), '..', 'templates', 'emails')
woopdi_mail = EmailService(template_dir=template_path)
