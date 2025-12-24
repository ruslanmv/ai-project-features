"""Tests for configuration management."""
import pytest
from pydantic import ValidationError
from aurora.core.config import Settings, get_settings


class TestSettings:
    """Test suite for Settings configuration."""

    def test_should_load_settings_from_env(self, monkeypatch):
        """Settings should load from environment variables."""
        monkeypatch.setenv("WATSONX_API_KEY", "test_key_123456")
        monkeypatch.setenv("WATSONX_PROJECT_ID", "test_project_123")
        
        settings = Settings()
        
        assert settings.watsonx_api_key == "test_key_123456"
        assert settings.watsonx_project_id == "test_project_123"

    def test_should_use_default_values(self, monkeypatch):
        """Settings should use default values for optional fields."""
        monkeypatch.setenv("WATSONX_API_KEY", "test_key_123456")
        monkeypatch.setenv("WATSONX_PROJECT_ID", "test_project_123")
        
        settings = Settings()
        
        assert settings.llm_temperature == 0.2
        assert settings.log_level == "INFO"
        assert settings.max_code_gen_attempts == 4

    def test_should_validate_url_format(self, monkeypatch):
        """Settings should reject URLs not starting with https://."""
        monkeypatch.setenv("WATSONX_API_KEY", "test_key_123456")
        monkeypatch.setenv("WATSONX_PROJECT_ID", "test_project_123")
        
        with pytest.raises(ValidationError, match="must start with 'https://'"):
            Settings(watsonx_url="http://invalid.com")

    def test_should_validate_temperature_range(self, monkeypatch):
        """Settings should reject temperature outside 0.0-1.0 range."""
        monkeypatch.setenv("WATSONX_API_KEY", "test_key_123456")
        monkeypatch.setenv("WATSONX_PROJECT_ID", "test_project_123")
        
        with pytest.raises(ValidationError):
            Settings(llm_temperature=1.5)

    def test_should_mask_api_key_in_repr(self, monkeypatch):
        """Settings repr should mask the API key."""
        monkeypatch.setenv("WATSONX_API_KEY", "secret_key_12345")
        monkeypatch.setenv("WATSONX_PROJECT_ID", "test_project_123")
        
        settings = Settings()
        repr_str = repr(settings)
        
        assert "secret_key_12345" not in repr_str
        assert "secr...2345" in repr_str


class TestGetSettings:
    """Test suite for get_settings() function."""

    def test_should_return_same_instance(self, monkeypatch):
        """get_settings should return cached singleton."""
        monkeypatch.setenv("WATSONX_API_KEY", "test_key_123456")
        monkeypatch.setenv("WATSONX_PROJECT_ID", "test_project_123")
        
        # Clear the cache first
        get_settings.cache_clear()
        
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2
