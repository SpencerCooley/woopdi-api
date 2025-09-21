from sqlalchemy.orm import Session
from typing import List, Optional
from models.user import User
from types_definitions.user import PublicUser

def list_users(db: Session, skip: int = 0, limit: int = 100, role: Optional[str] = None, confirmed: Optional[bool] = None) -> List[PublicUser]:
    """
    List users with pagination support.
    
    Args:
        db: Database session
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return (for pagination)
        role: Optional filter to only return users with this role
        confirmed: Optional filter to only return confirmed or unconfirmed users
        
    Returns:
        List of PublicUser objects
    """
    query = db.query(User)
    
    if role is not None:
        query = query.filter(User.role == role)
        
    if confirmed is not None:
        query = query.filter(User.confirmed == confirmed)
        
    users = query.offset(skip).limit(limit).all()
    return [PublicUser(
        id=user.id,
        email=user.email,
        role=user.role.value
    ) for user in users]
