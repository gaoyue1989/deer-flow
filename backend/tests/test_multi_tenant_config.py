"""Tests for multi-tenant configuration."""

import os
from unittest.mock import patch

import pytest

from deerflow.config.multi_tenant_config import (
    MultiTenantConfig,
    get_multi_tenant_config,
    load_multi_tenant_config_from_dict,
    reset_multi_tenant_config,
)


@pytest.fixture(autouse=True)
def reset_config():
    """Reset multi-tenant config before and after each test."""
    reset_multi_tenant_config()
    yield
    reset_multi_tenant_config()


class TestMultiTenantConfigDefaults:
    def test_default_enabled_is_false(self):
        """Default multi-tenant mode should be disabled."""
        config = MultiTenantConfig()
        assert config.enabled is False

    def test_default_jwt_secret_is_none(self):
        """Default JWT secret should be None."""
        config = MultiTenantConfig()
        assert config.jwt_secret is None

    def test_default_token_expire_minutes(self):
        """Default token expiration should be 7 days."""
        config = MultiTenantConfig()
        assert config.token_expire_minutes == 60 * 24 * 7

    def test_default_algorithm(self):
        """Default algorithm should be HS256."""
        config = MultiTenantConfig()
        assert config.algorithm == "HS256"

    def test_default_user_id(self):
        """Default user ID should be 'default'."""
        config = MultiTenantConfig()
        assert config.default_user_id == "default"


class TestMultiTenantConfigValidation:
    def test_invalid_algorithm_raises(self):
        """Invalid algorithm should raise ValueError."""
        with pytest.raises(ValueError, match="JWT algorithm must be one of"):
            MultiTenantConfig(algorithm="invalid")

    def test_valid_hs256(self):
        """HS256 should be accepted."""
        config = MultiTenantConfig(algorithm="HS256")
        assert config.algorithm == "HS256"

    def test_valid_rs256(self):
        """RS256 should be accepted."""
        config = MultiTenantConfig(algorithm="RS256")
        assert config.algorithm == "RS256"

    def test_jwt_secret_from_env(self):
        """JWT secret should be resolved from environment variable."""
        with patch.dict(os.environ, {"DEER_FLOW_JWT_SECRET": "env-secret"}, clear=False):
            config = MultiTenantConfig.model_validate({"jwt_secret": None})
            assert config.jwt_secret == "env-secret"

    def test_jwt_secret_from_value(self):
        """JWT secret from value should take precedence."""
        config = MultiTenantConfig(jwt_secret="direct-secret")
        assert config.jwt_secret == "direct-secret"


class TestMultiTenantConfigLoader:
    def test_load_from_dict(self):
        """Test loading config from dictionary."""
        config = load_multi_tenant_config_from_dict(
            {
                "enabled": True,
                "jwt_secret": "test-secret",
                "token_expire_minutes": 1440,
                "default_user_id": "custom-default",
            }
        )
        assert config.enabled is True
        assert config.jwt_secret == "test-secret"
        assert config.token_expire_minutes == 1440
        assert config.default_user_id == "custom-default"

    def test_load_none_uses_defaults(self):
        """Test loading None config uses defaults."""
        config = load_multi_tenant_config_from_dict(None)
        assert config.enabled is False
        assert config.default_user_id == "default"

    def test_load_empty_dict_uses_defaults(self):
        """Test loading empty dict uses defaults."""
        config = load_multi_tenant_config_from_dict({})
        assert config.enabled is False

    def test_get_multi_tenant_config_returns_cached(self):
        """Test get_multi_tenant_config returns cached instance."""
        loaded = load_multi_tenant_config_from_dict({"enabled": True})
        cached = get_multi_tenant_config()
        assert cached is loaded

    def test_get_multi_tenant_config_returns_default_when_not_loaded(self):
        """Test get_multi_tenant_config returns default when not loaded."""
        reset_multi_tenant_config()
        config = get_multi_tenant_config()
        assert config.enabled is False

    def test_reset_clears_cache(self):
        """Test reset_multi_tenant_config clears cache."""
        load_multi_tenant_config_from_dict({"enabled": True})
        reset_multi_tenant_config()
        config = get_multi_tenant_config()
        assert config.enabled is False
