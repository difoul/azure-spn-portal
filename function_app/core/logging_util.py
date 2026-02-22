import logging
import uuid


def get_logger(name: str) -> logging.Logger:
    """Get a logger configured for the portal."""
    return logging.getLogger(f"spn_portal.{name}")


def generate_correlation_id() -> str:
    """Generate a unique correlation ID for request tracing."""
    return str(uuid.uuid4())
