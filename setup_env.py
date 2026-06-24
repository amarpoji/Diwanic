#!/usr/bin/env python3
"""Configuration wizard for Diwanic.

This script creates or updates a .env file. If a .env already exists,
its current values are used as the defaults so you can safely refresh
credentials without retyping everything.
"""

from __future__ import annotations

from pathlib import Path

ENV_PATH = Path(".env")

DEFAULT_ENV_VARS = {
    "DATABASE__URL": "postgresql://user:password@localhost:5432/diwanic",
    "QDRANT__URL": "http://localhost:6333",
    "QDRANT__API_KEY": "",
    "ROUTER__BASE_URL": "https://api.deepseek.com",
    "ROUTER__API_KEY": "",
    "ROUTER__MODEL": "deepseek-chat",
    "LOGFIRE_TOKEN": "",
    "PREFECT_ACCOUNT_ID": "",
    "PREFECT_WORKSPACE_ID": "",
}


def _load_existing_env(path: Path) -> dict[str, str]:
    """Load key=value pairs from an existing .env file."""
    values: dict[str, str] = {}
    if not path.exists():
        return values

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        values[key.strip()] = value.strip()
    return values


def create_env() -> None:
    print("--- Diwanic Configuration Wizard ---")
    print("This script will create or update a .env file.\n")

    existing = _load_existing_env(ENV_PATH)
    final_vars = {}

    for key, default in DEFAULT_ENV_VARS.items():
        current_default = existing.get(key, default)
        val = input(f"Enter {key} [{current_default}]: ").strip()
        final_vars[key] = val if val else current_default

    with ENV_PATH.open("w", encoding="utf-8") as f:
        for k, v in final_vars.items():
            f.write(f"{k}={v}\n")

    print("\n✅ .env file created successfully!")
    print(f"Saved to: {ENV_PATH.resolve()}")
    print("You are ready to run: make run-flow")


if __name__ == "__main__":
    create_env()
