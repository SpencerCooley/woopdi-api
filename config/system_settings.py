# System settings configuration
# This file defines default system settings for the SaaS platform

class SystemSettings:
    # Setting to determine if all users should be automatically subscribed to a free tier
    AUTO_CREATE_FREE_SUBSCRIPTION = True

    # server side branding colors are mostly for emails, the react client has a nice theme system on the frontend. 
    # these colors are just here to make your emails match your frontend. 

    # Branding settings
    BRANDING_ACCENT_COLOR = "#00a8ea"
    BRANDING_PRIMARY_COLOR = "#00a8ea"  # Primary brand color for buttons and accents (blue)
    BRANDING_SECONDARY_COLOR = "#e3f2fd"  # Secondary color for gradients (light blue)
    BRANDING_LOGO = "https://storage.googleapis.com/woopdi-cloud-assets/woopdi-light-background-dark-logo.png"
    BRANDING_COMPANY_NAME = "Woopdi"
    BRANDING_SUPPORT_EMAIL = "support@woopdi.com"
    BRANDING_FOOTER_TEXT = "&copy; 2025 Woopdi. All rights reserved."

    # logos used in the front end react client 
    # the logo you want used in light mode (dark logo)
    BRANIDING_LOGO_LIGHT_MODE = "https://storage.googleapis.com/woopdi-cloud-assets/company-logo-dark.png" 
    BRANDING_LOGO_DARK_MODE = "https://storage.googleapis.com/woopdi-cloud-assets/company-logo-light.png"
    
    
    # Email template settings
    EMAIL_BACKGROUND_COLOR = "#f0f4f8"
    EMAIL_CONTAINER_MAX_WIDTH = "600px"
    EMAIL_HEADER_PADDING = "40px"
    EMAIL_BODY_PADDING = "40px"
    EMAIL_FOOTER_PADDING = "20px"

    # Other system settings can be added here
