"""Tests for JWT authentication utilities."""

import os
import uuid
from unittest.mock import patch

import pytest

from app.gateway.auth.jwt import (
    create_access_token,
    decode_access_token,
    get_jwt_secret,
    hash_password,
    reset_jwt_secret_cache,
    verify_password,
)
from app.gateway.auth.models import AuthenticationError, TokenData, UserRole
from deerflow.config.multi_tenant_config import load_multi_tenant_config_from_dict, reset_multi_tenant_config


@pytest.fixture(autouse=True)
def reset_config():
    """Reset multi-tenant config and JWT secret cache before each test."""
    reset_multi_tenant_config()
    reset_jwt_secret_cache()
    yield
    reset_multi_tenant_config()
    reset_jwt_secret_cache()


class TestCreateAccessToken:
    def test_create_token_with_user_id(self):
        """Test creating a token with user_id."""
        token = create_access_token(data={"sub": "user-123"})
        assert isinstance(token, str)
        assert len(token) > 0

    def test_create_token_with_extra_data(self):
        """Test creating a token with extra payload data."""
        token = create_access_token(data={"sub": "user-456", "email": "test@example.com", "role": "admin"})
        assert isinstance(token, str)

    def test_create_token_custom_secret(self):
        """Test creating a token with a custom secret key."""
        token = create_access_token(data={"sub": "user-789"}, secret_key="custom-secret")
        assert isinstance(token, str)

    def test_create_token_custom_expiry(self):
        """Test creating a token with custom expiration."""
        from datetime import timedelta

        token = create_access_token(data={"sub": "user-123"}, expires_delta=timedelta(minutes=30))
        assert isinstance(token, str)


class TestDecodeAccessToken:
    def test_decode_valid_token(self):
        """Test decoding a valid token."""
        token = create_access_token(data={"sub": "user-123"})
        decoded = decode_access_token(token)
        assert decoded.user_id == "user-123"
        assert decoded.role == UserRole.USER

    def test_decode_token_with_role(self):
        """Test decoding a token with role information."""
        token = create_access_token(data={"sub": "user-456", "role": "admin"})
        decoded = decode_access_token(token)
        assert decoded.user_id == "user-456"
        assert decoded.role == UserRole.ADMIN

    def test_decode_token_with_email(self):
        """Test decoding a token with email."""
        token = create_access_token(data={"sub": "user-789", "email": "test@example.com"})
        decoded = decode_access_token(token)
        assert decoded.email == "test@example.com"

    def test_decode_invalid_token_raises(self):
        """Test decoding an invalid token raises AuthenticationError."""
        with pytest.raises(AuthenticationError):
            decode_access_token("invalid-token-string")

    def test_decode_token_with_wrong_secret_raises(self):
        """Test decoding a token with wrong secret raises AuthenticationError."""
        token = create_access_token(data={"sub": "user-123"}, secret_key="secret-a")
        with pytest.raises(AuthenticationError):
            decode_access_token(token, secret_key="secret-b")

    def test_decode_missing_sub_raises(self):
        """Test decoding a token without 'sub' claim raises AuthenticationError."""
        token = create_access_token(data={"email": "test@example.com"})
        with pytest.raises(AuthenticationError):
            decode_access_token(token)


class TestPasswordHashing:
    def test_hash_password_returns_string(self):
        """Test that hash_password returns a string."""
        hashed = hash_password("my_secure_password")
        assert isinstance(hashed, str)
        assert len(hashed) > 0

    def test_verify_password_correct(self):
        """Test verifying a correct password."""
        password = "my_secure_password"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Test verifying an incorrect password."""
        hashed = hash_password("correct_password")
        assert verify_password("wrong_password", hashed) is False

    def test_different_passwords_different_hashes(self):
        """Test that different passwords produce different hashes."""
        hash1 = hash_password("password1")
        hash2 = hash_password("password2")
        assert hash1 != hash2

    def test_same_password_different_hashes(self):
        """Test that same password produces different hashes (bcrypt salt)."""
        hash1 = hash_password("same_password")
        hash2 = hash_password("same_password")
        assert hash1 != hash2

    def test_password_with_special_characters(self):
        """Test password with special characters."""
        password = "P@$$w0rd!#$%^&*()"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True


class TestJwtSecret:
    def test_get_jwt_secret_default(self):
        """Test getting default JWT secret."""
        reset_jwt_secret_cache()
        secret = get_jwt_secret()
        assert isinstance(secret, str)
        assert len(secret) > 0

    def test_get_jwt_secret_from_config(self):
        """Test getting JWT secret from config."""
        load_multi_tenant_config_from_dict({"jwt_secret": "config-secret"})
        reset_jwt_secret_cache()
        secret = get_jwt_secret()
        assert secret == "config-secret"

    def test_get_jwt_secret_from_env(self):
        """Test getting JWT secret from environment variable."""
        with patch.dict(os.environ, {"DEER_FLOW_JWT_SECRET": "env-secret"}, clear=False):
            reset_jwt_secret_cache()
            secret = get_jwt_secret()
            assert secret == "env-secret"

    def test_jwt_secret_is_cached(self):
        """Test that JWT secret is cached."""
        load_multi_tenant_config_from_dict({"jwt_secret": "cached-secret"})
        reset_jwt_secret_cache()
        secret1 = get_jwt_secret()
        secret2 = get_jwt_secret()
        assert secret1 == secret2

    def test_reset_jwt_secret_cache(self):
        """Test resetting JWT secret cache."""
        load_multi_tenant_config_from_dict({"jwt_secret": "secret-a"})
        reset_jwt_secret_cache()
        get_jwt_secret()
        load_multi_tenant_config_from_dict({"jwt_secret": "secret-b"})
        reset_jwt_secret_cache()
        secret = get_jwt_secret()
        assert secret == "secret-b"


class TestTokenRoundTrip:
    def test_roundtrip_user_id(self):
        """Test that user_id survives token creation and decoding."""
        original_user_id = str(uuid.uuid4())
        token = create_access_token(data={"sub": original_user_id})
        decoded = decode_access_token(token)
        assert decoded.user_id == original_user_id

    def test_roundtrip_all_fields(self):
        """Test that all fields survive token creation and decoding."""
        token = create_access_token(
            data={
                "sub": "user-123",
                "email": "test@example.com",
                "role": "admin",
            }
        )
        decoded = decode_access_token(token)
        assert decoded.user_id == "user-123"
        assert decoded.email == "test@example.com"
        assert decoded.role == UserRole.ADMIN
