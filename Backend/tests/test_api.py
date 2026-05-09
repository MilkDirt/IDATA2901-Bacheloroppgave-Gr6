"""
Tester for RAG API.

Dekker:
- Autentisering (registrering, innlogging, validering)
- Prosjekter (opprett, hent, slett)
- Samtaler og meldinger (opprett, hent, slett)
- Bygningsgenerering (parametere fra beskrivelse)
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.db.database import Base, get_db
from src.db.models import User, Project, Conversation, Message
from src.api.auth import hash_password

# ── Test database ─────────────────────────────────────────

TEST_DB_URL = "sqlite:///./test_rag.db"

engine = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# ── Setup / teardown ──────────────────────────────────────

@pytest.fixture(scope="session", autouse=True)
def setup_db():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def db():
    db = TestSessionLocal()
    yield db
    db.close()


@pytest.fixture()
def client():
    from src.api.main import app
    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


@pytest.fixture()
def registered_user(client):
    import uuid
    unique_email = f"test_{uuid.uuid4().hex[:8]}@multiconsult.no"
    res = client.post("/auth/register", json={
        "name": "Test Bruker",
        "email": unique_email,
        "password": "passord123"
    })
    assert res.status_code == 200
    data = res.json()
    data["email"] = unique_email
    return data


@pytest.fixture()
def auth_headers(registered_user):
    return {"Authorization": f"Bearer {registered_user['access_token']}"}


# ── Autentisering ─────────────────────────────────────────

class TestRegistrering:

    def test_registrering_gyldig(self, client):
        res = client.post("/auth/register", json={
            "name": "Ny Bruker",
            "email": "ny@multiconsult.no",
            "password": "passord123"
        })
        assert res.status_code == 200
        assert "access_token" in res.json()
        assert res.json()["user_name"] == "Ny Bruker"

    def test_registrering_duplikat_epost(self, client, registered_user):
        res = client.post("/auth/register", json={
            "name": "Kopi",
            "email": registered_user["email"],
            "password": "passord123"
        })
        assert res.status_code == 400
        assert "allerede registrert" in res.json()["detail"]

    def test_registrering_ugyldig_epost(self, client):
        res = client.post("/auth/register", json={
            "name": "Bruker",
            "email": "ikke-en-epost",
            "password": "passord123"
        })
        assert res.status_code == 400

    def test_registrering_passord_uten_tall(self, client):
        res = client.post("/auth/register", json={
            "name": "Bruker",
            "email": "bruker2@multiconsult.no",
            "password": "ingenTall"
        })
        assert res.status_code == 400
        assert "tall" in res.json()["detail"]


class TestInnlogging:

    def test_innlogging_gyldig(self, client, registered_user):
        res = client.post("/auth/login", json={
            "email": registered_user["email"],
            "password": "passord123"
        })
        assert res.status_code == 200
        assert "access_token" in res.json()

    def test_innlogging_feil_passord(self, client, registered_user):
        res = client.post("/auth/login", json={
            "email": registered_user["email"],
            "password": "feilpassord1"
        })
        assert res.status_code == 401

    def test_innlogging_ukjent_epost(self, client):
        res = client.post("/auth/login", json={
            "email": "finnesikke@multiconsult.no",
            "password": "passord123"
        })
        assert res.status_code == 401

    def test_beskyttet_endepunkt_uten_token(self, client):
        res = client.get("/conversations/")
        assert res.status_code == 401


# ── Prosjekter ────────────────────────────────────────────

class TestProsjekter:

    def test_opprett_prosjekt(self, client, auth_headers):
        res = client.post("/projects/", json={"name": "Testprosjekt"}, headers=auth_headers)
        assert res.status_code == 200
        assert res.json()["name"] == "Testprosjekt"

    def test_hent_prosjekter(self, client, auth_headers):
        client.post("/projects/", json={"name": "Prosjekt A"}, headers=auth_headers)
        res = client.get("/projects/", headers=auth_headers)
        assert res.status_code == 200
        assert isinstance(res.json(), list)
        assert len(res.json()) >= 1

    def test_slett_prosjekt(self, client, auth_headers):
        res = client.post("/projects/", json={"name": "Skal slettes"}, headers=auth_headers)
        project_id = res.json()["id"]
        del_res = client.delete(f"/projects/{project_id}", headers=auth_headers)
        assert del_res.status_code == 200
        assert "slettet" in del_res.json()["message"]

    def test_slett_prosjekt_ikke_funnet(self, client, auth_headers):
        res = client.delete("/projects/99999", headers=auth_headers)
        assert res.status_code == 404


# ── Samtaler ──────────────────────────────────────────────

class TestSamtaler:

    def test_hent_samtaler(self, client, auth_headers):
        res = client.get("/conversations/", headers=auth_headers)
        assert res.status_code == 200
        assert isinstance(res.json(), list)

    def test_slett_samtale(self, client, auth_headers, db):
        user = db.query(User).order_by(User.id.desc()).first()
        conv = Conversation(user_id=user.id, title="Testsamtale")
        db.add(conv)
        db.commit()
        db.refresh(conv)

        res = client.delete(f"/conversations/{conv.id}", headers=auth_headers)
        assert res.status_code == 200
        assert "slettet" in res.json()["message"]

    def test_slett_samtale_ikke_funnet(self, client, auth_headers):
        res = client.delete("/conversations/99999", headers=auth_headers)
        assert res.status_code == 404

    def test_hent_meldinger(self, client, auth_headers, db):
        user = db.query(User).order_by(User.id.desc()).first()
        conv = Conversation(user_id=user.id, title="Meldingstest")
        db.add(conv)
        db.commit()
        db.refresh(conv)

        msg = Message(conversation_id=conv.id, role="user", content="Hei")
        db.add(msg)
        db.commit()

        res = client.get(f"/conversations/{conv.id}/messages", headers=auth_headers)
        assert res.status_code == 200
        assert len(res.json()) >= 1
        assert res.json()[0]["role"] == "user"


# ── Bygningsgenerering ────────────────────────────────────

class TestBygningsgenerering:

    def test_helse_sjekk(self, client):
        res = client.get("/health")
        assert res.status_code == 200
        assert res.json()["status"] == "ok"

    def test_bygningsgenerering_returnerer_parametere(self, client):
        res = client.post("/generate-building", json={
            "description": "Moderne kontorbygg med store vinduer",
            "floors": 3,
            "height": 12.0,
            "footprint_width": 20.0,
            "footprint_depth": 15.0
        })
        assert res.status_code == 200
        data = res.json()
        assert "window_ratio" in data
        assert "wall_thickness" in data
        assert "floor_height" in data
        assert "facade_style" in data
        assert 0.2 <= data["window_ratio"] <= 0.7
        assert data["facade_style"] in ["modern", "classic", "industrial"]

    def test_bygningsgenerering_standard_verdier(self, client):
        res = client.post("/generate-building", json={
            "description": "Enkel hall"
        })
        assert res.status_code == 200