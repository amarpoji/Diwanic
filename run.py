"""Main entry point to launch the Diwanic Discovery UI."""

import sys
import os

# Ensure the project root is on the path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from diwanic.app.ui import build_ui


def run():
    """Build and launch the Gradio UI."""
    app = build_ui()
    app.launch(
        server_name="0.0.0.0",
        theme="soft",
        share=False,
    )


if __name__ == "__main__":
    run()
