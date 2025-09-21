from fastapi import APIRouter
from config.system_settings import SystemSettings
from types_definitions.system_settings import SystemSettingsResponse

router = APIRouter(
    prefix="/system-settings",
    tags=["System Settings"],
    responses={404: {"description": "Not found"}},
)

@router.get("/", response_model=SystemSettingsResponse)
async def get_system_settings():
    """
    Get the current system settings.
    """
    return SystemSettingsResponse(
        auto_create_free_subscription=SystemSettings.AUTO_CREATE_FREE_SUBSCRIPTION
    )