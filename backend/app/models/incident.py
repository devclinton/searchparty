from datetime import datetime
from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class IncidentStatus(StrEnum):
    PLANNING = "planning"
    ACTIVE = "active"
    SUSPENDED = "suspended"
    CLOSED = "closed"


VALID_STATUS_TRANSITIONS: dict[IncidentStatus, list[IncidentStatus]] = {
    IncidentStatus.PLANNING: [IncidentStatus.ACTIVE, IncidentStatus.CLOSED],
    IncidentStatus.ACTIVE: [IncidentStatus.SUSPENDED, IncidentStatus.CLOSED],
    IncidentStatus.SUSPENDED: [IncidentStatus.ACTIVE, IncidentStatus.CLOSED],
    IncidentStatus.CLOSED: [],
}


class SubjectAgeCategory(StrEnum):
    CHILD_1_3 = "child_1_3"
    CHILD_4_6 = "child_4_6"
    CHILD_7_12 = "child_7_12"
    CHILD_13_15 = "child_13_15"
    ADULT = "adult"
    ELDERLY = "elderly"


class SubjectActivity(StrEnum):
    HIKER = "hiker"
    HUNTER = "hunter"
    BERRY_PICKER = "berry_picker"
    FISHER = "fisher"
    CLIMBER = "climber"
    SKIER = "skier"
    RUNNER = "runner"
    DEMENTIA = "dementia"
    DESPONDENT = "despondent"
    OTHER = "other"


class IncidentCreate(BaseModel):
    name: str
    description: str | None = None
    subject_name: str | None = None
    subject_age_category: SubjectAgeCategory | None = None
    subject_activity: SubjectActivity | None = None
    subject_condition: str | None = None
    subject_clothing: str | None = None
    subject_medical_needs: str | None = None
    ipp_lat: float | None = None
    ipp_lon: float | None = None
    terrain_type: str | None = None
    data_retention_days: int = 90


class IncidentUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    subject_name: str | None = None
    subject_age_category: SubjectAgeCategory | None = None
    subject_activity: SubjectActivity | None = None
    subject_condition: str | None = None
    subject_clothing: str | None = None
    subject_medical_needs: str | None = None
    ipp_lat: float | None = None
    ipp_lon: float | None = None
    terrain_type: str | None = None
    data_retention_days: int | None = None


class IncidentStatusUpdate(BaseModel):
    status: IncidentStatus


class IncidentResponse(BaseModel):
    id: UUID
    name: str
    status: IncidentStatus
    description: str | None = None
    subject_name: str | None = None
    subject_age_category: SubjectAgeCategory | None = None
    subject_activity: SubjectActivity | None = None
    subject_condition: str | None = None
    subject_clothing: str | None = None
    subject_medical_needs: str | None = None
    ipp_lat: float | None = None
    ipp_lon: float | None = None
    terrain_type: str | None = None
    incident_commander_id: UUID | None = None
    data_retention_days: int = 90
    created_at: datetime
    updated_at: datetime
    closed_at: datetime | None = None
