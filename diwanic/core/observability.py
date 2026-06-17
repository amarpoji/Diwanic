"""Centralized Logfire Observability Setup.
Call setup_observability() once at application startup, before any other imports.
All instrumentation is configured inside the function, not at module level.
"""

import os
import logfire
from diwanic.core.config import settings

def setup_observability() -> None:
    """Initialize Logfire observability for the application.

    Must be called before any database or network operations.
    """
    # Allow disabling Logfire entirely via environment variable
    if os.getenv("LOGFIRE_DISABLED", "0") == "1":
        return

    token = settings.logfire_token
    try:
        if token:
            logfire.configure(token=token)
            logfire.instrument_pydantic()
            logfire.instrument_sqlalchemy()
            logfire.instrument_requests()
            logfire.info("Observability initialized")
        # Without a token, observability is a no-op to avoid crashing
    except Exception as e:
        # Prevent Logfire connection issues from crashing the app
        print(f"Warning: Failed to initialize Logfire: {e}")
