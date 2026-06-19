#!/usr/bin/env python3
"""
Configuration Wizard for Diwanic
Generates a .env file from user input to make the project plug-and-play.
"""
import os

def create_env():
    print("--- Diwanic Configuration Wizard ---")
    print("This script will create a .env file for you.\n")

    env_vars = {
        "DATABASE__URL": "postgresql://user:password@localhost:5432/diwanic",
        "QDRANT__URL": "http://localhost:6333",
        "QDRANT__API_KEY": "",
        "ROUTER__BASE_URL": "https://api.deepseek.com",
        "ROUTER__API_KEY": "",
        "ROUTER__MODEL": "deepseek-chat"
    }

    final_vars = {}
    for key, default in env_vars.items():
        val = input(f"Enter {key} [{default}]: ").strip()
        final_vars[key] = val if val else default

    with open(".env", "w") as f:
        for k, v in final_vars.items():
            f.write(f"{k}={v}\n")

    print("\n✅ .env file created successfully!")
    print("You are ready to run: make run-flow")

if __name__ == "__main__":
    create_env()
