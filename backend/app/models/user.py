from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel, EmailStr


class ICSRole(StrEnum):
    INCIDENT_COMMANDER = "incident_commander"
    OPERATIONS_CHIEF = "operations_chief"
    DIVISION_SUPERVISOR = "division_supervisor"
    TEAM_LEADER = "team_leader"
    SEARCHER = "searcher"
    SAFETY_OFFICER = "safety_officer"


# ICS role hierarchy — higher index means more authority
ICS_ROLE_HIERARCHY: dict[ICSRole, int] = {
    ICSRole.SEARCHER: 0,
    ICSRole.TEAM_LEADER: 1,
    ICSRole.DIVISION_SUPERVISOR: 2,
    ICSRole.SAFETY_OFFICER: 2,
    ICSRole.OPERATIONS_CHIEF: 3,
    ICSRole.INCIDENT_COMMANDER: 4,
}


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    display_name: str
    preferred_locale: str = "en"


class UserLogin(BaseModel):
    email: EmailStr
    password: str


class UserResponse(BaseModel):
    id: UUID
    email: str
    display_name: str
    contact_phone: str | None = None
    sar_qualifications: list[str] = []
    preferred_locale: str = "en"
    is_active: bool = True
    created_at: datetime


class UserProfileUpdate(BaseModel):
    display_name: str | None = None
    contact_phone: str | None = None
    sar_qualifications: list[str] | None = None
    preferred_locale: str | None = None


class TokenPair(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"  # noqa: S105


class TokenRefresh(BaseModel):
    refresh_token: str
