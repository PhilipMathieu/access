"""Custom exception hierarchy for the Access project.

This module defines custom exceptions to provide better error categorization
and more informative error messages throughout the codebase.
"""


class AccessError(Exception):
    """Base exception for all Access project errors."""

    pass


class DataError(AccessError):
    """Raised when there are issues with data files or data quality.

    Examples:
        - Missing required data files
        - Invalid data format
        - Schema mismatches
        - Data corruption
    """

    pass


class ValidationError(DataError):
    """Raised when data validation fails.

    Examples:
        - Missing required columns
        - Invalid geometry
        - Value out of expected range
        - Schema validation failure
    """

    pass


class ConfigurationError(AccessError):
    """Raised when there are configuration issues.

    Examples:
        - Missing required configuration
        - Invalid configuration values
        - Region configuration not found
    """

    pass


class NetworkError(AccessError):
    """Raised when network operations fail.

    Examples:
        - API request failures
        - Timeout errors
        - Connection errors
        - Rate limiting
    """

    pass


class ProcessingError(AccessError):
    """Raised when data processing operations fail.

    Examples:
        - Walk time calculation failures
        - Graph processing errors
        - Merge operation failures
    """

    pass


class GraphError(ProcessingError):
    """Raised when graph operations fail.

    Examples:
        - Graph download failures
        - Graph loading errors
        - Node/edge lookup failures
    """

    pass


class CensusAPIError(NetworkError):
    """Raised when Census API operations fail.

    Examples:
        - API key invalid
        - Rate limit exceeded
        - API request timeout
        - Invalid query parameters
    """

    pass
