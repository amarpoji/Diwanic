"""Centralized Logfire Observability Setup.
Call setup_observability() once at application startup, before any other imports.
All instrumentation is configured inside the function, not at module level.
"""

import logfire
from diwanic.core.config import settings


def setup_observability():
    """Initialize Logfire observability for the application.
    Must be called before any database or network operations.
    """
    # 1. Configure FIRST (before any instrumentation)
    token = settings.logfire_token
    
    if token:
        logfire.configure(token=token)
        # 2. Then instrument (these must happen AFTER configure)
        logfire.instrument_pydantic()
        logfire.instrument_sqlalchemy()
        logfire.instrument_requests()
        logfire.info("Observability initialized")
    else:
        # Without a token, observability is a no-op to avoid crashing in Docker
        pass
