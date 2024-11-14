from typing import List, Dict, Optional
from pydantic import BaseModel


class RealmAccess(BaseModel):
    roles: List[str]

class Account(BaseModel):
    roles: List[str]

class ResourceAccess(BaseModel):
    account: Account

class BearerToken(BaseModel):
    exp: int
    iat: int
    jti: str
    iss: str
    aud: str
    sub: str
    typ: str
    azp: str
    session_state: str
    acr: str
    realm_access: RealmAccess
    resource_access: ResourceAccess
    scope: str
    sid: str
    email_verified: bool
    group_names: List[str] = []
    name: str
    preferred_username: str
    given_name: str
    family_name: str
    email: str

class Group(BaseModel):
    id: Optional[str] = None
    name: str
    path: str
    subGroups: Optional[List[str]] = None
    attributes: Optional[Dict[str, List]] = None

class Role(BaseModel):
    id: str
    name: str
    composite: bool
    clientRole: bool
    containerId: str
    attributes: Optional[Dict[str, List]] = None


class Access(BaseModel):
    # manageGroupMembership: Optional[bool]
    # view: Optional[bool]
    # mapRoles: Optional[bool]
    # impersonate: Optional[bool]
    # manage: Optional[bool]
    manageGroupMembership: bool = False
    view: bool = False
    mapRoles: bool = False
    impersonate: bool = False
    manage: bool = False


class UserData(BaseModel):
    id: str
    createdTimestamp: int
    username: str
    enabled: bool
    totp: bool
    emailVerified: bool
    firstName: str
    lastName: str
    email: str
    disableableCredentialTypes: List
    requiredActions: List
    notBefore: int
    # access: Optional[Access]
    access: Access = Access()
    attributes: Optional[Dict[str, list]] = None


class Credentials(BaseModel):
    type: str = "password"
    value: str
    temporary: bool = False


class UserRegistration(BaseModel):
    username: str
    enabled: bool = True
    emailVerified: bool = True
    firstName: str
    lastName: str
    email: str
    credentials: List[Credentials]
    # requiredActions: List
    attributes: Dict[str, str]

class LoginParams(BaseModel):
    grant_type: Optional[str] = ""
    client_id: Optional[str] = ""
    client_secret: Optional[str] = ""
    username: str
    password: str
