from sqlalchemy.orm import Session
from typing import List, Optional
from models.organization import Organization
from types_definitions.organization import OrganizationRead

def list_organizations(db: Session, skip: int = 0, limit: int = 100, is_solo: Optional[bool] = None) -> List[OrganizationRead]:
    """
    List organizations with pagination support.
    
    Args:
        db: Database session
        skip: Number of records to skip (for pagination)
        limit: Maximum number of records to return (for pagination)
        is_solo: Optional filter to only return organizations where is_solo equals this value
        
    Returns:
        List of OrganizationRead objects
    """
    query = db.query(Organization)
    
    if is_solo is not None:
        query = query.filter(Organization.is_solo == is_solo)
        
    organizations = query.offset(skip).limit(limit).all()
    return organizations
