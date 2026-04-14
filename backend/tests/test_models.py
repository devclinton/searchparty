"""Tests for Pydantic models and ICS role hierarchy."""

from app.models.user import ICS_ROLE_HIERARCHY, ICSRole


def test_ics_role_hierarchy_ordering():
    assert ICS_ROLE_HIERARCHY[ICSRole.SEARCHER] < ICS_ROLE_HIERARCHY[ICSRole.TEAM_LEADER]
    assert ICS_ROLE_HIERARCHY[ICSRole.TEAM_LEADER] < ICS_ROLE_HIERARCHY[ICSRole.OPERATIONS_CHIEF]
    assert (
        ICS_ROLE_HIERARCHY[ICSRole.OPERATIONS_CHIEF]
        < ICS_ROLE_HIERARCHY[ICSRole.INCIDENT_COMMANDER]
    )


def test_safety_officer_same_level_as_division_supervisor():
    assert (
        ICS_ROLE_HIERARCHY[ICSRole.SAFETY_OFFICER]
        == ICS_ROLE_HIERARCHY[ICSRole.DIVISION_SUPERVISOR]
    )


def test_incident_commander_is_highest():
    max_level = max(ICS_ROLE_HIERARCHY.values())
    assert ICS_ROLE_HIERARCHY[ICSRole.INCIDENT_COMMANDER] == max_level


def test_all_roles_in_hierarchy():
    for role in ICSRole:
        assert role in ICS_ROLE_HIERARCHY
