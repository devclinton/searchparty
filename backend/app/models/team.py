from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel

from app.models.user import ICSRole


class TeamStatus(StrEnum):
    STANDBY = "standby"
    DEPLOYED = "deployed"
    RETURNING = "returning"
    OVERDUE = "overdue"
    STOOD_DOWN = "stood_down"


class SearchType(StrEnum):
    HASTY = "hasty"
    GRID = "grid"
    LINE = "line"
    ATTRACTION = "attraction"


class TeamCreate(BaseModel):
    name: str
    search_type: SearchType | None = None
    check_in_interval_minutes: int = 30


class TeamUpdate(BaseModel):
    name: str | None = None
    search_type: SearchType | None = None
    check_in_interval_minutes: int | None = None
    turnaround_time: datetime | None = None


class TeamStatusUpdate(BaseModel):
    status: TeamStatus


class TeamResponse(BaseModel):
    id: UUID
    incident_id: UUID
    name: str
    status: TeamStatus
    leader_id: UUID | None = None
    search_type: SearchType | None = None
    check_in_interval_minutes: int = 30
    last_check_in_at: datetime | None = None
    deployed_at: datetime | None = None
    turnaround_time: datetime | None = None
    created_at: datetime
    updated_at: datetime


class TeamMemberAdd(BaseModel):
    user_id: UUID
    role: ICSRole = ICSRole.SEARCHER


class TeamMemberResponse(BaseModel):
    id: UUID
    team_id: UUID
    user_id: UUID
    role: ICSRole
    signed_in_at: datetime
    signed_out_at: datetime | None = None


class AssignmentDispatch(BaseModel):
    search_type: SearchType | None = None
    sector_description: str | None = None
    turnaround_time: datetime | None = None


class CheckInRecord(BaseModel):
    team_id: UUID
    checked_in_at: datetime
    notes: str | None = None


class AccountabilityEntry(BaseModel):
    user_id: UUID
    display_name: str
    team_name: str | None = None
    role: ICSRole
    signed_in_at: datetime
    signed_out_at: datetime | None = None
