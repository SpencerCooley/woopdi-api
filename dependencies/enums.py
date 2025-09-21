from enum import Enum

class RoleEnum(str, Enum):
    superadmin = "superadmin"
    admin = "admin"
    user = "user"