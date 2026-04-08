"""Tests for auth router endpoints."""


import pytest
from fastapi.testclient import TestClient

from deerflow.config.multi_tenant_config import reset_multi_tenant_config


@pytest.fixture(autouse=True)
def reset_config():
    """Reset multi-tenant config before and after each test."""
    reset_multi_tenant_config()
    yield
    reset_multi_tenant_config()


@pytest.fixture
def client():
    """Create a test client with auth router."""
    from fastapi import FastAPI

    from app.gateway.routers.auth import router

    app = FastAPI()
    app.include_router(router)
    return TestClient(app)


@pytest.fixture
def mock_store(tmp_path):
    """Create a mock UserStore with temp directory."""
    from app.gateway.routers import auth as auth_module
    from app.gateway.users.store import UserStore

    store = UserStore(base_dir=tmp_path)
    auth_module._user_store = store
    return store


class TestRegisterEndpoint:
    def test_register_success(self, client, mock_store):
        """Test successful user registration."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "password": "securepassword123",
            },
        )
        assert response.status_code == 201
        data = response.json()
        assert "access_token" in data
        assert data["email"] == "newuser@example.com"
        assert data["role"] == "user"

    def test_register_duplicate_email(self, client, mock_store):
        """Test registration with duplicate email."""
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "dup@example.com",
                "password": "securepassword123",
            },
        )
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "dup@example.com",
                "password": "securepassword123",
            },
        )
        assert response.status_code == 400
        assert "already registered" in response.json()["detail"]

    def test_register_short_password(self, client, mock_store):
        """Test registration with short password."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "short@example.com",
                "password": "short",
            },
        )
        assert response.status_code == 422

    def test_register_invalid_email(self, client, mock_store):
        """Test registration with invalid email."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "not-an-email",
                "password": "securepassword123",
            },
        )
        assert response.status_code == 422

    def test_register_with_admin_role(self, client, mock_store):
        """Test registration with admin role."""
        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "admin@example.com",
                "password": "securepassword123",
                "role": "admin",
            },
        )
        assert response.status_code == 201
        assert response.json()["role"] == "admin"


class TestLoginEndpoint:
    def test_login_success(self, client, mock_store):
        """Test successful login."""
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "login@example.com",
                "password": "securepassword123",
            },
        )
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "login@example.com",
                "password": "securepassword123",
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["email"] == "login@example.com"

    def test_login_wrong_password(self, client, mock_store):
        """Test login with wrong password."""
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "wrong@example.com",
                "password": "correctpassword",
            },
        )
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "wrong@example.com",
                "password": "wrongpassword",
            },
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client, mock_store):
        """Test login with non-existent user."""
        response = client.post(
            "/api/v1/auth/login",
            json={
                "email": "nonexistent@example.com",
                "password": "anypassword",
            },
        )
        assert response.status_code == 401


class TestMeEndpoint:
    def test_get_me_unauthenticated(self, client, mock_store):
        """Test /me endpoint without authentication returns default user."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 200
        data = response.json()
        assert "user_id" in data
        assert "role" in data

    def test_get_me_authenticated(self, client, mock_store):
        """Test /me endpoint with authentication."""
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "me@example.com",
                "password": "securepassword123",
            },
        )
        login_resp = client.post(
            "/api/v1/auth/login",
            json={
                "email": "me@example.com",
                "password": "securepassword123",
            },
        )
        token = login_resp.json()["access_token"]

        response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "me@example.com"


class TestLogoutEndpoint:
    def test_logout_clears_cookie(self, client, mock_store):
        """Test logout clears the access_token cookie."""
        client.post(
            "/api/v1/auth/register",
            json={
                "email": "logout@example.com",
                "password": "securepassword123",
            },
        )
        response = client.post("/api/v1/auth/logout")
        assert response.status_code == 200
        assert response.json()["message"] == "Successfully logged out"
