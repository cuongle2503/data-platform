from idp.common.exceptions import (
    ApiError,
    ConfigurationError,
    IdpError,
    IngestionError,
    IntelligenceError,
    StorageError,
    TransformationError,
)


def test_base_exception() -> None:
    """Test base IDP exception."""
    exc = IdpError("test error")
    assert str(exc) == "test error"
    assert isinstance(exc, Exception)


def test_configuration_error() -> None:
    """Test configuration error."""
    exc = ConfigurationError("config missing")
    assert isinstance(exc, IdpError)


def test_ingestion_error() -> None:
    """Test ingestion error."""
    exc = IngestionError("ingestion failed")
    assert isinstance(exc, IdpError)


def test_transformation_error() -> None:
    """Test transformation error."""
    exc = TransformationError("transform failed")
    assert isinstance(exc, IdpError)


def test_storage_error() -> None:
    """Test storage error."""
    exc = StorageError("storage failed")
    assert isinstance(exc, IdpError)


def test_intelligence_error() -> None:
    """Test intelligence error."""
    exc = IntelligenceError("intelligence failed")
    assert isinstance(exc, IdpError)


def test_api_error() -> None:
    """Test API error."""
    exc = ApiError("api failed")
    assert isinstance(exc, IdpError)
