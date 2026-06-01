from idp.common.config import get_settings


def test_config_loads_defaults(mock_env: None) -> None:
    """Test that configuration loads with mock environment variables."""
    settings = get_settings()

    assert settings.minio.endpoint == "localhost:9000"
    assert settings.postgres.host == "localhost"
    assert settings.gemini.api_key == "test_api_key"
    assert settings.duckdb.path == ":memory:"
