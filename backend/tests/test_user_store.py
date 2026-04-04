"""Tests for UserStore."""

import json
import tempfile
from pathlib import Path
from uuid import uuid4

import pytest

from app.gateway.auth.models import UserRole
from app.gateway.users.store import UserStore


@pytest.fixture
def store(tmp_path):
    """Create a UserStore with a temporary directory."""
    return UserStore(base_dir=tmp_path)


class TestUserStoreCreate:
    def test_create_user(self, store):
        """Test creating a new user."""
        user_id = uuid4()
        user = store.create(
            user_id=user_id,
            email="test@example.com",
            hashed_password="hashed_pw",
        )
        assert user["user_id"] == str(user_id)
        assert user["email"] == "test@example.com"
        assert user["role"] == UserRole.USER
        assert "quota_limits" in user

    def test_create_user_with_role(self, store):
        """Test creating a user with a specific role."""
        user_id = uuid4()
        user = store.create(
            user_id=user_id,
            email="admin@example.com",
            hashed_password="hashed_pw",
            role=UserRole.ADMIN,
        )
        assert user["role"] == UserRole.ADMIN

    def test_create_user_duplicate_id(self, store):
        """Test that duplicate user_id raises ValueError."""
        user_id = uuid4()
        store.create(user_id=user_id, email="a@example.com", hashed_password="pw")
        with pytest.raises(ValueError, match="already exists"):
            store.create(user_id=user_id, email="b@example.com", hashed_password="pw")

    def test_create_user_duplicate_email(self, store):
        """Test that duplicate email raises ValueError."""
        user_id_1 = uuid4()
        user_id_2 = uuid4()
        store.create(user_id=user_id_1, email="dup@example.com", hashed_password="pw")
        with pytest.raises(ValueError, match="already registered"):
            store.create(user_id=user_id_2, email="dup@example.com", hashed_password="pw")

    def test_create_user_default_quotas(self, store):
        """Test that default quotas are applied."""
        user_id = uuid4()
        user = store.create(user_id=user_id, email="q@example.com", hashed_password="pw")
        assert "max_threads" in user["quota_limits"]
        assert "max_sandboxes" in user["quota_limits"]
        assert "max_storage_mb" in user["quota_limits"]

    def test_create_user_custom_quotas(self, store):
        """Test that custom quotas override defaults."""
        user_id = uuid4()
        custom_quotas = {"max_threads": 5, "max_sandboxes": 2, "max_storage_mb": 512}
        user = store.create(
            user_id=user_id,
            email="cq@example.com",
            hashed_password="pw",
            quota_limits=custom_quotas,
        )
        assert user["quota_limits"] == custom_quotas


class TestUserStoreGet:
    def test_get_by_id(self, store):
        """Test getting user by ID."""
        user_id = uuid4()
        store.create(user_id=user_id, email="get@example.com", hashed_password="pw")
        user = store.get_by_id(user_id)
        assert user is not None
        assert user["email"] == "get@example.com"

    def test_get_by_id_string(self, store):
        """Test getting user by string ID."""
        user_id = uuid4()
        store.create(user_id=user_id, email="gs@example.com", hashed_password="pw")
        user = store.get_by_id(str(user_id))
        assert user is not None
        assert user["email"] == "gs@example.com"

    def test_get_by_id_not_found(self, store):
        """Test getting non-existent user by ID."""
        user = store.get_by_id(uuid4())
        assert user is None

    def test_get_by_email(self, store):
        """Test getting user by email."""
        user_id = uuid4()
        store.create(user_id=user_id, email="ge@example.com", hashed_password="pw")
        user = store.get_by_email("ge@example.com")
        assert user is not None
        assert user["user_id"] == str(user_id)

    def test_get_by_email_not_found(self, store):
        """Test getting non-existent user by email."""
        user = store.get_by_email("nonexistent@example.com")
        assert user is None


class TestUserStoreUpdate:
    def test_update_email(self, store):
        """Test updating user email."""
        user_id = uuid4()
        store.create(user_id=user_id, email="old@example.com", hashed_password="pw")
        updated = store.update(user_id, email="new@example.com")
        assert updated["email"] == "new@example.com"

        # Verify old email is gone
        assert store.get_by_email("old@example.com") is None
        # Verify new email works
        assert store.get_by_email("new@example.com") is not None

    def test_update_role(self, store):
        """Test updating user role."""
        user_id = uuid4()
        store.create(user_id=user_id, email="role@example.com", hashed_password="pw")
        updated = store.update(user_id, role=UserRole.ADMIN)
        assert updated["role"] == UserRole.ADMIN

    def test_update_not_found(self, store):
        """Test updating non-existent user raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            store.update(uuid4(), email="new@example.com")

    def test_update_email_duplicate(self, store):
        """Test updating email to an already-registered email raises ValueError."""
        user_id_1 = uuid4()
        user_id_2 = uuid4()
        store.create(user_id=user_id_1, email="a@example.com", hashed_password="pw")
        store.create(user_id=user_id_2, email="b@example.com", hashed_password="pw")
        with pytest.raises(ValueError, match="already registered"):
            store.update(user_id_1, email="b@example.com")


class TestUserStoreDelete:
    def test_delete_user(self, store):
        """Test deleting a user."""
        user_id = uuid4()
        store.create(user_id=user_id, email="del@example.com", hashed_password="pw")
        store.delete(user_id)
        assert store.get_by_id(user_id) is None
        assert store.get_by_email("del@example.com") is None

    def test_delete_not_found(self, store):
        """Test deleting non-existent user raises ValueError."""
        with pytest.raises(ValueError, match="not found"):
            store.delete(uuid4())


class TestUserStoreList:
    def test_list_users(self, store):
        """Test listing users."""
        for i in range(5):
            store.create(user_id=uuid4(), email=f"u{i}@example.com", hashed_password="pw")
        users = store.list_users()
        assert len(users) == 5

    def test_list_users_pagination(self, store):
        """Test listing users with pagination."""
        for i in range(10):
            store.create(user_id=uuid4(), email=f"p{i}@example.com", hashed_password="pw")
        users = store.list_users(limit=3, offset=2)
        assert len(users) == 3

    def test_list_users_empty(self, store):
        """Test listing users when store is empty."""
        users = store.list_users()
        assert users == []


class TestUserStorePersistence:
    def test_data_persists_across_instances(self, tmp_path):
        """Test that data persists when creating a new UserStore instance."""
        store1 = UserStore(base_dir=tmp_path)
        user_id = uuid4()
        store1.create(user_id=user_id, email="persist@example.com", hashed_password="pw")

        store2 = UserStore(base_dir=tmp_path)
        user = store2.get_by_id(user_id)
        assert user is not None
        assert user["email"] == "persist@example.com"

    def test_corrupt_file_starts_fresh(self, tmp_path):
        """Test that corrupt JSON file starts fresh."""
        data_path = tmp_path / "users.json"
        data_path.parent.mkdir(parents=True, exist_ok=True)
        data_path.write_text("{invalid json", encoding="utf-8")

        store = UserStore(base_dir=tmp_path)
        users = store.list_users()
        assert users == []
