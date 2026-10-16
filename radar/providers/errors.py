class ProviderError(RuntimeError):
    """Sanitized provider failure. Never include credentials or response bodies."""
