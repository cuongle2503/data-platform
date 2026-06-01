"""Tests for REST endpoint routers (countries, indicators, timeseries)."""

from unittest.mock import Mock, sentinel

import pytest
from fastapi.testclient import TestClient

from idp.api.main import app
from idp.api.schemas.country import CountryResponse
from idp.api.schemas.indicator import IndicatorResponse, TimeseriesData


@pytest.fixture
def mock_repo():
    """Create a mock repository."""
    mock = Mock()
    mock.get_countries.return_value = [
        {
            "country_code": "VNM",
            "country_name": "Vietnam",
            "region": "East Asia & Pacific",
            "income_group": "Lower middle income",
            "is_asean": True,
            "is_primary": True,
        },
        {
            "country_code": "THA",
            "country_name": "Thailand",
            "region": "East Asia & Pacific",
            "income_group": "Upper middle income",
            "is_asean": True,
            "is_primary": False,
        },
    ]
    mock.get_country.return_value = {
        "country_code": "VNM",
        "country_name": "Vietnam",
        "region": "East Asia & Pacific",
        "income_group": "Lower middle income",
        "is_asean": True,
        "is_primary": True,
    }
    mock.get_indicators.return_value = [
        {
            "indicator_code": "NY.GDP.MKTP.CD",
            "indicator_name": "GDP (current US$)",
            "category": "Economic Policy & Debt",
            "unit": "current US$",
            "description": "GDP at purchaser's prices",
        },
        {
            "indicator_code": "SP.POP.TOTL",
            "indicator_name": "Population, total",
            "category": "Health",
            "unit": "people",
            "description": "Total population",
        },
    ]
    mock.get_indicator.return_value = {
        "indicator_code": "NY.GDP.MKTP.CD",
        "indicator_name": "GDP (current US$)",
        "category": "Economic Policy & Debt",
        "unit": "current US$",
        "description": "GDP at purchaser's prices",
    }
    mock.get_timeseries.return_value = [
        {
            "country_code": "VNM",
            "indicator_code": "NY.GDP.MKTP.CD",
            "year": 2023,
            "value": 429.7,
            "source": "World Bank",
        },
    ]
    return mock


class TestCountriesRouter:
    """Integration tests for countries endpoints."""

    @pytest.fixture(autouse=True)
    def setup_router(self, mock_repo):
        """Register mock router before each test; remove after."""
        from idp.api.routers.countries import create_router

        router = create_router(mock_repo)
        app.include_router(router, prefix="/api/v1")
        yield
        # Cleanup: remove all routes added by the router
        idx = next(
            (
                i
                for i, r in enumerate(app.router.routes)
                if hasattr(r, "name") and r.name == "list_countries"
            ),
            None,
        )
        if idx is not None:
            app.router.routes[:] = [
                r for r in app.router.routes if r.name not in ("list_countries", "get_country")
            ]

    def test_list_countries(self, mock_repo):
        """Should return paginated list of countries."""
        # Act
        response = TestClient(app).get("/api/v1/countries?page=1&page_size=20")

        # Assert
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 2
        assert data[0]["country_code"] == "VNM"
        assert data[1]["country_code"] == "THA"

    def test_get_country_by_code(self, mock_repo):
        """Should return country details by code."""
        # Act
        response = TestClient(app).get("/api/v1/countries/VNM")

        # Assert
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["country_code"] == "VNM"
        assert data["country_name"] == "Vietnam"

    def test_get_country_not_found(self, mock_repo):
        """Should return 404 when country not found."""
        mock_repo.get_country.return_value = None

        # Act
        response = TestClient(app).get("/api/v1/countries/XXX")

        # Assert
        assert response.status_code == 404
        assert response.json()["error"]["code"] == "NOT_FOUND"


class TestIndicatorsRouter:
    """Integration tests for indicators endpoints."""

    @pytest.fixture(autouse=True)
    def setup_router(self, mock_repo):
        """Register mock router before each test; remove after."""
        from idp.api.routers.indicators import create_router

        router = create_router(mock_repo)
        app.include_router(router, prefix="/api/v1")
        yield
        app.router.routes[:] = [
            r
            for r in app.router.routes
            if r.name not in ("list_indicators", "get_indicator_metadata")
        ]

    def test_list_indicators(self, mock_repo):
        """Should return paginated list of indicators."""
        # Act
        response = TestClient(app).get("/api/v1/indicators/catalog?page=1&page_size=20")

        # Assert
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 2
        assert data[0]["indicator_code"] == "NY.GDP.MKTP.CD"

    def test_get_indicator_metadata(self, mock_repo):
        """Should return indicator metadata by code."""
        # Act
        response = TestClient(app).get("/api/v1/indicators/NY.GDP.MKTP.CD/metadata")

        # Assert
        assert response.status_code == 200
        data = response.json()["data"]
        assert data["indicator_code"] == "NY.GDP.MKTP.CD"

    def test_get_indicator_not_found(self, mock_repo):
        """Should return 404 when indicator not found."""
        mock_repo.get_indicator.return_value = None

        # Act
        response = TestClient(app).get("/api/v1/indicators/XXX/metadata")

        # Assert
        assert response.status_code == 404


class TestTimeseriesRouter:
    """Integration tests for timeseries endpoints."""

    @pytest.fixture(autouse=True)
    def setup_router(self, mock_repo):
        """Register mock router before each test; remove after."""
        from idp.api.routers.timeseries import create_router

        router = create_router(mock_repo)
        app.include_router(router, prefix="/api/v1")
        yield
        app.router.routes[:] = [r for r in app.router.routes if r.name != "get_timeseries"]

    def test_get_timeseries(self, mock_repo):
        """Should return timeseries data."""
        # Act
        response = TestClient(app).get(
            "/api/v1/timeseries",
            params={
                "country_code": "VNM",
                "indicator_codes": ["NY.GDP.MKTP.CD"],
                "years": [2023],
            },
        )

        # Assert
        assert response.status_code == 200
        data = response.json()["data"]
        assert len(data) == 1
        assert data[0]["value"] == 429.7

    def test_get_timeseries_missing_params(self):
        """Should return 422 when required params are missing."""
        # Act
        response = TestClient(app).get("/api/v1/timeseries")

        # Assert
        assert response.status_code == 422
