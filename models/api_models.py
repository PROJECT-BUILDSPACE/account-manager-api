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
    occupation: Optional[List[str]]
    affiliation: Optional[List[str]]
    country: Optional[List[str]]
    city: Optional[List[str]]
