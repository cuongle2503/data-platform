"""Unit tests for config module."""

from idp.common.config import (
    COUNTRIES,
    INDICATORS,
    WorldBankConfig,
    get_settings,
    get_wb_countries,
    get_wb_indicators,
)


def test_world_bank_config_defaults():
    """Test WorldBankConfig default values."""
    # Act
    config = WorldBankConfig()

    # Assert
    assert config.api_url == "https://api.worldbank.org/v2"
    assert config.wds_url == "https://search.worldbank.org/api/v3/wds"
    assert config.per_page == 1000
    assert config.batch_size == 10
    assert config.default_start_year == 2010


def test_world_bank_config_custom():
    """Test WorldBankConfig with custom values."""
    # Act
    config = WorldBankConfig(
        api_url="http://custom-api:8080",
        per_page=500,
        batch_size=5,
        default_start_year=2000,
    )

    # Assert
    assert config.api_url == "http://custom-api:8080"
    assert config.per_page == 500
    assert config.default_start_year == 2000


def test_indicators_list_not_empty():
    """Test that default indicators list contains expected count."""
    # Assert
    assert len(INDICATORS) > 0
    # Verify expected key indicators exist
    indicator_codes = [i["code"] for i in INDICATORS]
    assert "NY.GDP.MKTP.CD" in indicator_codes  # GDP
    assert "SP.POP.TOTL" in indicator_codes  # Population


def test_indicators_have_required_fields():
    """Test that all indicators have required fields."""
    # Assert
    for indicator in INDICATORS:
        assert "code" in indicator, f"Missing 'code' in indicator: {indicator}"
        assert "name" in indicator, f"Missing 'name' in indicator: {indicator}"
        assert "source" in indicator, f"Missing 'source' in indicator: {indicator}"


def test_countries_list_not_empty():
    """Test that default countries list has expected entries."""
    # Assert
    assert len(COUNTRIES) > 0
    country_codes = [c["code"] for c in COUNTRIES]
    assert "VNM" in country_codes  # Vietnam
    assert "CN" in country_codes  # China


def test_countries_have_required_fields():
    """Test that all countries have required fields."""
    # Assert
    for country in COUNTRIES:
        assert "code" in country, f"Missing 'code' in country: {country}"
        assert "name" in country, f"Missing 'name' in country: {country}"


def test_get_wb_indicators_default():
    """Test get_wb_indicators returns default list."""
    # Act
    result = get_wb_indicators()

    # Assert
    assert len(result) == len(INDICATORS)


def test_get_wb_indicators_filtered():
    """Test get_wb_indicators with code filtering."""
    # Act
    result = get_wb_indicators(["NY.GDP.MKTP.CD", "SP.POP.TOTL"])

    # Assert
    assert len(result) == 2
    codes = [i["code"] for i in result]
    assert "NY.GDP.MKTP.CD" in codes
    assert "SP.POP.TOTL" in codes


def test_get_wb_countries_default():
    """Test get_wb_countries returns default list."""
    # Act
    result = get_wb_countries()

    # Assert
    assert len(result) == len(COUNTRIES)


def test_get_wb_countries_filtered():
    """Test get_wb_countries with code filtering."""
    # Act
    result = get_wb_countries(["VN", "CN"])

    # Assert
    assert len(result) == 2


def test_get_settings_is_cached():
    """Test that get_settings returns same instance (LRU cache)."""
    # Act
    s1 = get_settings()
    s2 = get_settings()

    # Assert
    assert s1 is s2
