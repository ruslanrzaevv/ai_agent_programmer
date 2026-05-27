"""
OpsMind test suite.
Run: pytest tests/ -v --asyncio-mode=auto
"""
import uuid
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.security import create_access_token, hash_password
from app.db.session import Base, get_db
from app.main import app
from app.models.models import (
    AuthProvider, ExplainMode, Incident, IncidentSeverity,
    IncidentStatus, LogEntry, LogLevel, LogSource, Project, User,
)

# ── Test DB ────────────────────────────────────────────────────────────────────
TEST_DB_URL = "postgresql+asyncpg://opsmind:opsmind@localhost:5432/opsmind_test"

test_engine = create_async_engine(TEST_DB_URL, echo=False)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def create_tables():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def db():
    async with TestSession() as session:
        yield session
        await session.rollback()


@pytest_asyncio.fixture
async def client(db: AsyncSession):
    async def override_db():
        yield db

    app.dependency_overrides[get_db] = override_db

    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as c:
        yield c

    app.dependency_overrides.clear()


# ── Fixtures ───────────────────────────────────────────────────────────────────

@pytest_asyncio.fixture
async def user(db: AsyncSession) -> User:
    u = User(
        email="test@opsmind.io",
        username="testuser",
        hashed_password=hash_password("password123"),
        auth_provider=AuthProvider.EMAIL,
        is_active=True,
        is_verified=True,
        explain_mode=ExplainMode.SENIOR,
        notify_channels=["email"],
    )
    db.add(u)
    await db.commit()
    await db.refresh(u)
    return u


@pytest_asyncio.fixture
def auth_headers(user: User) -> dict:
    token = create_access_token(str(user.id))
    return {"Authorization": f"Bearer {token}"}


@pytest_asyncio.fixture
async def project(db: AsyncSession, user: User) -> Project:
    p = Project(
        owner_id=user.id,
        name="Test Project",
        environment="production",
        docker_engine_url="unix:///var/run/docker.sock",
        docker_tls_enabled=False,
        gitlab_url="https://gitlab.com",
        gitlab_token="glpat-test",
        gitlab_project_id="12345",
        gitlab_branches=["main"],
        error_threshold_per_minute=5,
        log_level_filter=["error", "critical"],
        notify_channels=["email"],
        timezone="UTC",
    )
    db.add(p)
    await db.commit()
    await db.refresh(p)
    return p


@pytest_asyncio.fixture
async def incident(db: AsyncSession, project: Project) -> Incident:
    now = datetime.now(timezone.utc)
    inc = Incident(
        project_id=project.id,
        title="Database connection pool exhausted",
        severity=IncidentSeverity.HIGH,
        status=IncidentStatus.OPEN,
        error_count=23,
        affected_containers=["api-server", "worker"],
        ai_explanation_senior="Connection pool exhausted due to long-running queries.",
        ai_explanation_junior="Too many connections were opened at once and none were being closed.",
        ai_explanation_ceo="What happened: The website slowed down for 12 minutes. Business impact: ~$200 revenue loss.",
        ai_fix_suggestion="Increase pool size or reduce query timeout.",
        ai_auto_fix_script="docker exec api-server kill -SIGUSR1 1",
        timeline=[
            {"minute": 0, "ts": now.isoformat(), "event": "First error", "error_count": 3, "cpu_percent": 45.2},
            {"minute": 1, "ts": now.isoformat(), "event": "Error spike", "error_count": 20, "cpu_percent": 88.1},
        ],
        started_at=now,
    )
    db.add(inc)
    await db.commit()
    await db.refresh(inc)
    return inc


# ── Auth tests ─────────────────────────────────────────────────────────────────

class TestAuth:
    async def test_register_email(self, client: AsyncClient, db: AsyncSession):
        resp = await client.post("/api/v1/auth/register", json={
            "email": "new@opsmind.io",
            "password": "strongpass123",
            "auth_provider": "email",
        })
        assert resp.status_code == 201
        data = resp.json()
        assert "access_token" in data
        assert "refresh_token" in data

    async def test_register_duplicate_email(self, client: AsyncClient, user: User):
        resp = await client.post("/api/v1/auth/register", json={
            "email": "test@opsmind.io",
            "password": "strongpass123",
            "auth_provider": "email",
        })
        assert resp.status_code == 400

    async def test_login_success(self, client: AsyncClient, user: User):
        resp = await client.post("/api/v1/auth/login", json={
            "identifier": "test@opsmind.io",
            "password": "password123",
        })
        assert resp.status_code == 200
        assert "access_token" in resp.json()

    async def test_login_wrong_password(self, client: AsyncClient, user: User):
        resp = await client.post("/api/v1/auth/login", json={
            "identifier": "test@opsmind.io",
            "password": "wrongpass",
        })
        assert resp.status_code == 401

    async def test_login_by_username(self, client: AsyncClient, user: User):
        resp = await client.post("/api/v1/auth/login", json={
            "identifier": "testuser",
            "password": "password123",
        })
        assert resp.status_code == 200

    async def test_me_authenticated(self, client: AsyncClient, user: User, auth_headers: dict):
        resp = await client.get("/api/v1/auth/me", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["email"] == "test@opsmind.io"

    async def test_me_unauthenticated(self, client: AsyncClient):
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 403  # No credentials


# ── Project tests ──────────────────────────────────────────────────────────────

class TestProjects:
    async def test_create_project(self, client: AsyncClient, auth_headers: dict):
        with patch("app.api.v1.endpoints.projects.monitoring_manager") as mock_mm:
            mock_mm.start_project = AsyncMock()
            resp = await client.post(
                "/api/v1/projects/",
                headers=auth_headers,
                json={
                    "name": "My App",
                    "environment": "production",
                    "docker_engine_url": "tcp://host:2376",
                    "docker_tls_enabled": False,
                    "gitlab_url": "https://gitlab.com",
                    "gitlab_token": "glpat-xxx",
                    "gitlab_project_id": "42",
                    "error_threshold_per_minute": 10,
                    "notify_channels": ["email"],
                },
            )
        assert resp.status_code == 201
        data = resp.json()
        assert data["name"] == "My App"
        assert data["monitoring_enabled"] is True

    async def test_list_projects(self, client: AsyncClient, auth_headers: dict, project: Project):
        resp = await client.get("/api/v1/projects/", headers=auth_headers)
        assert resp.status_code == 200
        assert len(resp.json()) >= 1

    async def test_get_project(self, client: AsyncClient, auth_headers: dict, project: Project):
        resp = await client.get(f"/api/v1/projects/{project.id}", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["id"] == str(project.id)

    async def test_get_project_not_owner(self, client: AsyncClient, project: Project, db: AsyncSession):
        other = User(
            email="other@opsmind.io",
            hashed_password=hash_password("pass"),
            auth_provider=AuthProvider.EMAIL,
            is_active=True,
            is_verified=True,
        )
        db.add(other)
        await db.commit()
        token = create_access_token(str(other.id))
        resp = await client.get(
            f"/api/v1/projects/{project.id}",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 404


# ── Incident tests ─────────────────────────────────────────────────────────────

class TestIncidents:
    async def test_list_incidents(self, client: AsyncClient, auth_headers: dict, project: Project, incident: Incident):
        resp = await client.get(
            f"/api/v1/incidents/?project_id={project.id}",
            headers=auth_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] >= 0

    async def test_get_incident(self, client: AsyncClient, auth_headers: dict, incident: Incident):
        resp = await client.get(f"/api/v1/incidents/{incident.id}", headers=auth_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == incident.title
        assert data["severity"] == "high"

    async def test_acknowledge_incident(self, client: AsyncClient, auth_headers: dict, incident: Incident):
        resp = await client.post(f"/api/v1/incidents/{incident.id}/acknowledge", headers=auth_headers)
        assert resp.status_code == 200
        assert resp.json()["status"] == "acknowledged"

    async def test_resolve_incident(self, client: AsyncClient, auth_headers: dict, incident: Incident):
        resp = await client.post(
            f"/api/v1/incidents/{incident.id}/resolve",
            headers=auth_headers,
            json={},
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "resolved"

    async def test_get_replay_timeline(self, client: AsyncClient, auth_headers: dict, incident: Incident):
        resp = await client.get(f"/api/v1/incidents/{incident.id}/replay", headers=auth_headers)
        assert resp.status_code == 200
        timeline = resp.json()
        assert isinstance(timeline, list)
        assert len(timeline) == 2
        assert timeline[0]["minute"] == 0
        assert timeline[1]["cpu_percent"] == 88.1

    async def test_explain_senior_cached(self, client: AsyncClient, auth_headers: dict, incident: Incident):
        resp = await client.post(
            f"/api/v1/incidents/{incident.id}/explain",
            headers=auth_headers,
            json={"mode": "senior", "incident_id": str(incident.id)},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "pool" in data["content"].lower()

    async def test_explain_ceo_cached(self, client: AsyncClient, auth_headers: dict, incident: Incident):
        resp = await client.post(
            f"/api/v1/incidents/{incident.id}/explain",
            headers=auth_headers,
            json={"mode": "ceo", "incident_id": str(incident.id)},
        )
        assert resp.status_code == 200
        assert "revenue" in resp.json()["content"].lower()

    async def test_apply_fix_requires_confirmation(self, client: AsyncClient, auth_headers: dict, incident: Incident):
        resp = await client.post(
            f"/api/v1/incidents/{incident.id}/apply-fix",
            headers=auth_headers,
            json={"confirmed": False},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is False
        assert "script_preview" in resp.json()

    async def test_apply_fix_confirmed(self, client: AsyncClient, auth_headers: dict, incident: Incident):
        resp = await client.post(
            f"/api/v1/incidents/{incident.id}/apply-fix",
            headers=auth_headers,
            json={"confirmed": True},
        )
        assert resp.status_code == 200
        assert resp.json()["success"] is True


# ── AI Service unit tests ──────────────────────────────────────────────────────

class TestAIService:
    async def test_explain_all_modes(self, incident: Incident):
        from app.services.ai_service import AIService

        logs = [
            LogEntry(
                project_id=incident.project_id,
                source=LogSource.DOCKER,
                level=LogLevel.ERROR,
                message="Connection pool exhausted: timeout after 30s",
                container_name="api-server",
                raw={},
                timestamp=datetime.now(timezone.utc),
            )
        ]

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="Mocked AI explanation")]

        ai = AIService()
        with patch.object(ai.client.messages, "create", new_callable=AsyncMock, return_value=mock_response):
            results = await ai.explain_all_modes(incident, logs)

        assert "junior" in results
        assert "senior" in results
        assert "ceo" in results
        assert results["junior"] == "Mocked AI explanation"

    async def test_suggest_fix(self, incident: Incident):
        from app.services.ai_service import AIService

        mock_response = MagicMock()
        mock_response.content = [MagicMock(text="DESCRIPTION:\nRestart the service\n\nSCRIPT:\ndocker restart api")]

        ai = AIService()
        with patch.object(ai.client.messages, "create", new_callable=AsyncMock, return_value=mock_response):
            result = await ai.suggest_fix(incident, [])

        assert "Restart" in result["description"]
        assert "docker restart" in result["script"]


# ── Incident Detector unit tests ───────────────────────────────────────────────

class TestIncidentDetector:
    async def test_error_window_counting(self):
        from app.workers.incident_detector import ErrorWindow

        window = ErrorWindow(window_seconds=60)
        import asyncio
        now = asyncio.get_event_loop().time()

        window.add(now, "error")
        window.add(now, "error")
        window.add(now, "critical")
        window.add(now, "info")

        assert window.error_count() == 3
        assert window.critical_count() == 1

    async def test_threshold_not_triggered_below(self, project: Project, user: User):
        from app.workers.incident_detector import IncidentDetector

        async def fake_db_factory():
            yield MagicMock()

        detector = IncidentDetector(project, fake_db_factory, user)
        detector._last_incident_at = None

        # Below threshold (project threshold = 5)
        import asyncio
        now = asyncio.get_event_loop().time()
        for _ in range(3):
            detector._window.add(now, "error")

        # Should NOT create incident
        with patch.object(detector, "_create_incident", new_callable=AsyncMock) as mock_create:
            await detector._check_threshold()
            mock_create.assert_not_called()

    async def test_threshold_triggered_above(self, project: Project, user: User):
        from app.workers.incident_detector import IncidentDetector

        detector = IncidentDetector(project, MagicMock(), user)

        import asyncio
        now = asyncio.get_event_loop().time()
        for _ in range(10):  # above threshold of 5
            detector._window.add(now, "error")

        with patch.object(detector, "_create_incident", new_callable=AsyncMock) as mock_create:
            await detector._check_threshold()
            mock_create.assert_called_once()


# ── Health check ───────────────────────────────────────────────────────────────

class TestHealth:
    async def test_health_ok(self, client: AsyncClient):
        with patch("app.api.v1.endpoints.health.get_redis") as mock_redis:
            mock_r = AsyncMock()
            mock_r.ping = AsyncMock()
            mock_redis.return_value = mock_r
            resp = await client.get("/api/v1/health")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"