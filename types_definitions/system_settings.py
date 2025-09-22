# define your pydantic models here for request and response.
from pydantic import BaseModel, ConfigDict
from typing import Optional


class SystemSettingsResponse(BaseModel):
    auto_create_free_subscription: bool
    branding_logo_light_mode: Optional[str] = None
    branding_logo_dark_mode: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
