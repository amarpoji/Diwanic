"""Main entry point to launch the Diwanic REST API."""

import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from diwanic.api.main import app
import uvicorn


def run():
    """Launch the FastAPI REST API."""
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
    )


if __name__ == "__main__":
    run()