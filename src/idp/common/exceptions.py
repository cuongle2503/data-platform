"""Custom exception types for the IDP application."""


class IdpError(Exception):
    """Base exception for all IDP errors."""

    pass


class ConfigurationError(IdpError):
    """Raised when configuration is invalid or missing."""

    pass


class IngestionError(IdpError):
    """Raised when data ingestion fails."""

    pass


class TransformationError(IdpError):
    """Raised when data transformation fails."""

    pass


class StorageError(IdpError):
    """Raised when storage operations fail."""

    pass


class IntelligenceError(IdpError):
    """Raised when intelligence layer operations fail."""

    pass


class ApiError(IdpError):
    """Raised when API operations fail."""

    pass
