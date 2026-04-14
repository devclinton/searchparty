"""Shared test fixtures with a FakePool that routes SQL queries to in-memory data."""

from datetime import UTC, datetime
from uuid import UUID, uuid4

import pytest
from httpx import ASGITransport, AsyncClient

from app.auth.jwt import create_access_token
from app.auth.password import hash_password
from app.db.connection import get_pool
from app.main import app

TEST_USER_ID = uuid4()
TEST_USER_2_ID = uuid4()
TEST_EMAIL = "test@example.com"
TEST_PASSWORD = "secure-password-123"
TEST_HASH = hash_password(TEST_PASSWORD)


def _make_user(
    user_id: UUID = TEST_USER_ID,
    email: str = TEST_EMAIL,
    password_hash: str = TEST_HASH,
    display_name: str = "Test User",
) -> dict:
    return {
        "id": user_id,
        "email": email,
        "display_name": display_name,
        "password_hash": password_hash,
        "oauth_provider": None,
        "oauth_id": None,
        "contact_phone": None,
        "sar_qualifications": [],
        "preferred_locale": "en",
        "is_active": True,
        "created_at": datetime.now(UTC),
        "updated_at": datetime.now(UTC),
    }


class FakePool:
    """In-memory mock of asyncpg.Pool for testing without a database."""

    def __init__(self):
        self.users: dict[str, dict] = {}
        self.incidents: dict[str, dict] = {}
        self.teams: dict[str, dict] = {}
        self.team_members: dict[str, dict] = {}

    async def fetchrow(self, query: str, *args):
        q = query.strip().lower()

        # Users
        if "from users where id" in q:
            return self.users.get(str(args[0]))
        if "from users where email" in q:
            for u in self.users.values():
                if u["email"] == args[0]:
                    return u
            return None
        if "insert into users" in q:
            user = _make_user(
                user_id=uuid4(), email=args[0], password_hash=args[2], display_name=args[1]
            )
            self.users[str(user["id"])] = user
            return user

        # Incidents
        if "insert into incidents" in q:
            inc = {
                "id": uuid4(),
                "name": args[0],
                "description": args[1],
                "incident_commander_id": args[2],
                "status": "planning",
                "subject_name": args[3],
                "subject_age_category": args[4],
                "subject_activity": args[5],
                "subject_condition": args[6],
                "subject_clothing": args[7],
                "subject_medical_needs": args[8],
                "ipp_lat": args[9],
                "ipp_lon": args[10],
                "ipp_point": None,
                "terrain_type": args[11],
                "data_retention_days": args[12],
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
                "closed_at": None,
            }
            self.incidents[str(inc["id"])] = inc
            return inc
        if "from incidents where id" in q:
            return self.incidents.get(str(args[0]))
        if "update incidents set status" in q:
            inc = self.incidents.get(str(args[1]))
            if inc:
                inc["status"] = args[0]
                inc["updated_at"] = datetime.now(UTC)
                if args[0] == "closed":
                    inc["closed_at"] = datetime.now(UTC)
                return inc
            return None
        if "update incidents set" in q:
            inc = self.incidents.get(str(args[0]))
            if inc:
                inc["updated_at"] = datetime.now(UTC)
                return inc
            return None

        # Teams
        if "insert into teams" in q:
            team = {
                "id": uuid4(),
                "incident_id": args[0],
                "name": args[1],
                "search_type": args[2],
                "status": "standby",
                "leader_id": None,
                "check_in_interval_minutes": args[3],
                "last_check_in_at": None,
                "deployed_at": None,
                "turnaround_time": None,
                "created_at": datetime.now(UTC),
                "updated_at": datetime.now(UTC),
            }
            self.teams[str(team["id"])] = team
            return team
        if "from teams where id" in q:
            return self.teams.get(str(args[0]))
        if "update teams set status = $1" in q:
            # update_team_status: args = (status, team_id)
            team = self.teams.get(str(args[1]))
            if team:
                team["status"] = args[0]
                team["updated_at"] = datetime.now(UTC)
                if args[0] == "deployed":
                    team["deployed_at"] = datetime.now(UTC)
                return team
            return None
        if "update teams set last_check_in_at" in q:
            team = self.teams.get(str(args[0]))
            if team:
                team["last_check_in_at"] = datetime.now(UTC)
                team["updated_at"] = datetime.now(UTC)
                return team
            return None
        if "update teams set" in q and "'deployed'" in q:
            # dispatch_assignment: args = (team_id, ...)
            team = self.teams.get(str(args[0]))
            if team:
                team["status"] = "deployed"
                team["deployed_at"] = datetime.now(UTC)
                team["updated_at"] = datetime.now(UTC)
                return team
            return None

        # Team members
        if "insert into team_members" in q:
            member = {
                "id": uuid4(),
                "team_id": args[0],
                "user_id": args[1],
                "role": args[2],
                "signed_in_at": datetime.now(UTC),
                "signed_out_at": None,
            }
            key = f"{args[0]}_{args[1]}"
            self.team_members[key] = member
            return member

        # Team member role check (used by require_role)
        if "from team_members tm" in q and "join teams t" in q:
            for m in self.team_members.values():
                t = self.teams.get(str(m["team_id"]))
                if (
                    t
                    and str(m["user_id"]) == str(args[0])
                    and len(args) > 1
                    and str(t["incident_id"]) == str(args[1])
                ):
                    return m
            return None

        # Incident commander check
        if "incident_commander_id" in q and "from incidents" in q:
            inc = self.incidents.get(str(args[0]))
            if inc:
                return {"incident_commander_id": inc["incident_commander_id"]}
            return None

        return None

    async def fetch(self, query: str, *args):
        q = query.strip().lower()

        if "from incidents" in q and "order by" in q:
            results = list(self.incidents.values())
            if (
                args
                and isinstance(args[0], str)
                and args[0]
                in (
                    "planning",
                    "active",
                    "suspended",
                    "closed",
                )
            ):
                results = [r for r in results if r["status"] == args[0]]
            return results

        if "from teams where incident_id" in q:
            return [t for t in self.teams.values() if str(t["incident_id"]) == str(args[0])]

        if "from team_members tm" in q and "tm.team_id" in q:
            members = []
            for m in self.team_members.values():
                if str(m["team_id"]) == str(args[0]) and m["signed_out_at"] is None:
                    m_with_user = {**m}
                    user = self.users.get(str(m["user_id"]))
                    if user:
                        m_with_user["display_name"] = user["display_name"]
                        m_with_user["email"] = user["email"]
                    members.append(m_with_user)
            return members

        if "from teams" in q and "status = 'deployed'" in q:
            return []  # No overdue teams in mock

        if "from team_members tm" in q and "t.incident_id" in q:
            entries = []
            for m in self.team_members.values():
                team = self.teams.get(str(m["team_id"]))
                user = self.users.get(str(m["user_id"]))
                if team and user and str(team["incident_id"]) == str(args[0]):
                    entries.append(
                        {
                            **m,
                            "display_name": user["display_name"],
                            "team_name": team["name"],
                        }
                    )
            return entries

        return []

    async def execute(self, query: str, *args):
        q = query.strip().lower()
        if "update team_members set signed_out_at" in q:
            key = f"{args[0]}_{args[1]}"
            if key in self.team_members:
                self.team_members[key]["signed_out_at"] = datetime.now(UTC)
                return "UPDATE 1"
            return "UPDATE 0"
        if "delete from incidents" in q:
            return "DELETE 0"
        return "UPDATE 1"


@pytest.fixture
def fake_pool():
    pool = FakePool()
    pool.users[str(TEST_USER_ID)] = _make_user()
    pool.users[str(TEST_USER_2_ID)] = _make_user(
        user_id=TEST_USER_2_ID, email="user2@example.com", display_name="User Two"
    )
    return pool


@pytest.fixture
async def client(fake_pool):
    async def override_get_pool():
        return fake_pool

    app.dependency_overrides[get_pool] = override_get_pool
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac
    app.dependency_overrides.clear()


@pytest.fixture
def auth_headers():
    token = create_access_token(TEST_USER_ID)
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def auth_headers_user2():
    token = create_access_token(TEST_USER_2_ID)
    return {"Authorization": f"Bearer {token}"}
