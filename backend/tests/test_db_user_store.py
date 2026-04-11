"""Tests for DBUserStore database-backed user store."""

from uuid import uuid4

import pytest

from app.gateway.auth.models import UserRole
from app.gateway.users.db_store import DBUserStore
from deerflow.config.checkpointer_config import CheckpointerConfig, set_checkpointer_config


@pytest.fixture
def db_user_store():
    """Create a DBUserStore with in-memory checkpointer."""
    set_checkpointer_config(CheckpointerConfig(type="memory"))
    store = DBUserStore()
    yield store
    store.close()


class TestDBUserStore:
    """Test DBUserStore basic functionality."""

    def test_create_user(self, db_user_store):
        """Test creating a new user."""
        user_id = uuid4()
        email = "test@example.com"
        password_hash = "hashed_password_here"

        user = db_user_store.create(user_id, email, password_hash, UserRole.USER)

        assert user["user_id"] == str(user_id)
        assert user["email"] == email
        assert user["hashed_password"] == password_hash
        assert user["role"] == UserRole.USER

    def test_create_duplicate_user_id(self, db_user_store):
        """Test creating user with duplicate user_id raises error."""
        user_id = uuid4()
        email1 = "first@example.com"
        email2 = "second@example.com"
        password_hash = "hashed_password"

        db_user_store.create(user_id, email1, password_hash)

        with pytest.raises(ValueError, match="already exists"):
            db_user_store.create(user_id, email2, password_hash)

    def test_create_duplicate_email(self, db_user_store):
        """Test creating user with duplicate email raises error."""
        user_id1 = uuid4()
        user_id2 = uuid4()
        email = "same@example.com"
        password_hash = "hashed_password"

        db_user_store.create(user_id1, email, password_hash)

        with pytest.raises(ValueError, match="already registered"):
            db_user_store.create(user_id2, email, password_hash)

    def test_get_by_id(self, db_user_store):
        """Test getting user by ID."""
        user_id = uuid4()
        email = "getbyid@example.com"
        password_hash = "hashed"

        db_user_store.create(user_id, email, password_hash)
        fetched = db_user_store.get_by_id(user_id)

        assert fetched is not None
        assert fetched["user_id"] == str(user_id)
        assert fetched["email"] == email
        assert fetched["hashed_password"] == password_hash

    def test_get_by_id_nonexistent(self, db_user_store):
        """Test getting non-existent user returns None."""
        fetched = db_user_store.get_by_id(uuid4())
        assert fetched is None

    def test_get_by_email(self, db_user_store):
        """Test getting user by email."""
        user_id = uuid4()
        email = "getbyemail@example.com"
        password_hash = "hashed_email"

        db_user_store.create(user_id, email, password_hash)
        fetched = db_user_store.get_by_email(email)

        assert fetched is not None
        assert fetched["user_id"] == str(user_id)
        assert fetched["email"] == email

    def test_get_by_email_nonexistent(self, db_user_store):
        """Test getting non-existent email returns None."""
        fetched = db_user_store.get_by_email("nonexistent@example.com")
        assert fetched is None

    def test_update_user(self, db_user_store):
        """Test updating user fields."""
        user_id = uuid4()
        email = "original@example.com"
        password_hash = "original_hash"

        db_user_store.create(user_id, email, password_hash)
        updated = db_user_store.update(user_id, email="updated@example.com")

        assert updated["email"] == "updated@example.com"
        assert updated["hashed_password"] == password_hash

        # Check changes are persisted
        fetched = db_user_store.get_by_email("updated@example.com")
        assert fetched is not None
        assert fetched["email"] == "updated@example.com"

        # Old email should not exist anymore
        old_fetched = db_user_store.get_by_email("original@example.com")
        assert old_fetched is None

    def test_update_email_duplicate(self, db_user_store):
        """Test updating email to existing email raises error."""
        user_id1 = uuid4()
        user_id2 = uuid4()
        email1 = "user1@example.com"
        email2 = "user2@example.com"

        db_user_store.create(user_id1, email1, "hash1")
        db_user_store.create(user_id2, email2, "hash2")

        with pytest.raises(ValueError, match="already registered"):
            db_user_store.update(user_id1, email=email2)

    def test_delete_user(self, db_user_store):
        """Test deleting a user."""
        user_id = uuid4()
        email = "todelete@example.com"
        password_hash = "hash"

        db_user_store.create(user_id, email, password_hash)

        # Verify exists
        assert db_user_store.get_by_email(email) is not None

        # Delete
        db_user_store.delete(user_id)

        # Verify gone
        assert db_user_store.get_by_email(email) is None
        assert db_user_store.get_by_id(user_id) is None

    def test_delete_nonexistent(self, db_user_store):
        """Test deleting non-existent user raises error."""
        with pytest.raises(ValueError, match="not found"):
            db_user_store.delete(uuid4())

    def test_list_users(self, db_user_store):
        """Test listing users with pagination."""
        # Create 3 users
        for i in range(3):
            user_id = uuid4()
            email = f"list{i}@example.com"
            db_user_store.create(user_id, email, f"hash{i}")

        users = db_user_store.list_users(limit=2, offset=0)
        assert len(users) == 2

        users_all = db_user_store.list_users(limit=10, offset=0)
        assert len(users_all) >= 3

    def test_create_with_admin_role(self, db_user_store):
        """Test creating admin user."""
        user_id = uuid4()
        email = "admin@example.com"
        password_hash = "adminhash"

        user = db_user_store.create(user_id, email, password_hash, UserRole.ADMIN)

        assert user["role"] == UserRole.ADMIN
        fetched = db_user_store.get_by_id(user_id)
        assert fetched["role"] == UserRole.ADMIN

    def test_default_quotas_are_set(self, db_user_store):
        """Test default quotas are set when not provided."""
        user_id = uuid4()
        email = "quotas@example.com"
        password_hash = "hash"

        user = db_user_store.create(user_id, email, password_hash)

        assert "quota_limits" in user
        assert "max_threads" in user["quota_limits"]
        assert user["quota_limits"]["max_threads"] == 10


class TestDBUserStoreConcurrency:
    """Test concurrent access to DBUserStore.

    This tests that concurrent reads don't cause race conditions,
    which was the original issue with JSON file storage.
    """

    def test_concurrent_reads_same_user(self, db_user_store):
        """Test multiple concurrent reads to the same user don't cause issues."""
        import threading

        user_id = uuid4()
        email = "concurrent@example.com"
        password_hash = "concurrenthash"

        db_user_store.create(user_id, email, password_hash)

        results = []

        def read_worker():
            user = db_user_store.get_by_email(email)
            results.append(user)

        # Simulate multiple concurrent logins (reads)
        threads = [threading.Thread(target=read_worker) for _ in range(10)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # All reads should find the user
        assert len(results) == 10
        for result in results:
            assert result is not None
            assert result["email"] == email
            assert result["hashed_password"] == password_hash
