"""Custom exceptions for the Substack scraper."""

class SubstackError(Exception):
    """Base exception for all Substack scraper errors."""
    pass

class NetworkError(SubstackError):
    """Raised when there are network-related issues."""
    pass

class ContentError(SubstackError):
    """Raised when there are issues with content processing."""
    pass

class CacheError(SubstackError):
    """Raised when there are issues with caching."""
    pass

class FileSystemError(SubstackError):
    """Raised when there are issues with file system operations."""
    pass

class ConfigurationError(SubstackError):
    """Raised when there are issues with configuration."""
    pass

class ValidationError(SubstackError):
    """Raised when input validation fails."""
    pass 