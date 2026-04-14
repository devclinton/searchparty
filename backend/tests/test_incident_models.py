"""Tests for incident models and status transitions."""

from app.models.incident import VALID_STATUS_TRANSITIONS, IncidentStatus


def test_planning_can_go_to_active():
    assert IncidentStatus.ACTIVE in VALID_STATUS_TRANSITIONS[IncidentStatus.PLANNING]


def test_planning_can_go_to_closed():
    assert IncidentStatus.CLOSED in VALID_STATUS_TRANSITIONS[IncidentStatus.PLANNING]


def test_planning_cannot_go_to_suspended():
    assert IncidentStatus.SUSPENDED not in VALID_STATUS_TRANSITIONS[IncidentStatus.PLANNING]


def test_active_can_go_to_suspended():
    assert IncidentStatus.SUSPENDED in VALID_STATUS_TRANSITIONS[IncidentStatus.ACTIVE]


def test_active_can_go_to_closed():
    assert IncidentStatus.CLOSED in VALID_STATUS_TRANSITIONS[IncidentStatus.ACTIVE]


def test_suspended_can_resume_to_active():
    assert IncidentStatus.ACTIVE in VALID_STATUS_TRANSITIONS[IncidentStatus.SUSPENDED]


def test_closed_has_no_transitions():
    assert VALID_STATUS_TRANSITIONS[IncidentStatus.CLOSED] == []
