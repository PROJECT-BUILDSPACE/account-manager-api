from typing import List, Dict, Optional
from pydantic import BaseModel

class ErrorReport(BaseModel):
    internal_status: str
    status: int
    message: str
    reason: str

class RoleUpdate(BaseModel):
    attributes: Dict[str, List]

class Administrator(BaseModel):
    admin: bool
class JoinGroupBody(BaseModel):
    users: List[Dict[str, Administrator]]

class UserAttrs(BaseModel):
    occupation: Optional[List[str]] = None
    affiliation: Optional[List[str]] = None
    country: Optional[List[str]] = None
    city: Optional[List[str]] = None
    editor_in_user_attr: Optional[List[str]] = None
    viewer_in_user_attr: Optional[List[str]] = None


class SharingInput(BaseModel):
    folder_id: str
    target_organization_name: str
    rights: Optional[str] = None
