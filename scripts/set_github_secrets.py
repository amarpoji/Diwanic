#!/usr/bin/env python3
"""
Set Diwanic GitHub Secrets via the GitHub REST API.

Usage:
  1. Generate a GitHub Personal Access Token with 'repo' scope:
     https://github.com/settings/tokens/new
  2. Run: python scripts/set_github_secrets.py <YOUR_GITHUB_TOKEN>

This will read your .env file and push each variable as a GitHub Action secret.
"""

import os
import sys
import json
import urllib.request

REPO = "amarpoji/Diwanic"

# Secrets to push from .env (map env var -> GitHub secret name)
SECRETS_MAP = {
    "DATABASE__URL": "DATABASE__URL",
    "QDRANT__URL": "QDRANT__URL",
    "QDRANT__API_KEY": "QDRANT__API_KEY",
    "ROUTER__BASE_URL": "ROUTER__BASE_URL",
    "ROUTER__API_KEY": "ROUTER__API_KEY",
}


def load_dotenv(path: str) -> dict[str, str]:
    """Simple .env parser — no pip dependency needed."""
    env = {}
    if not os.path.exists(path):
        print(f"Warning: {path} not found — skipping local env load")
        return env
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            if "=" in line:
                key, _, value = line.partition("=")
                # strip quotes
                value = value.strip().strip('"').strip("'")
                env[key.strip()] = value
    return env


def get_public_key(token: str) -> tuple[str, str]:
    """Get the repo's public key for encrypting secrets."""
    url = f"https://api.github.com/repos/{REPO}/actions/secrets/public-key"
    req = urllib.request.Request(url)
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("User-Agent", "Diwanic-CI-Setup/1.0")

    with urllib.request.urlopen(req) as resp:
        data = json.loads(resp.read())
    return data["key_id"], data["key"]


def encrypt_secret(public_key: str, plaintext: str) -> str:
    """Encrypt a secret using the repo's public key via libsodium."""
    # We use nacl which is commonly available
    try:
        from nacl import encoding, public
    except ImportError:
        print("Error: PyNaCl is required. Install with: pip install pynacl")
        sys.exit(1)

    pk = public.PublicKey(public_key.encode("utf-8"), encoding.Base64Encoder())
    sealed_box = public.SealedBox(pk)
    encrypted = sealed_box.encrypt(plaintext.encode("utf-8"))
    return encrypted.hex()


def set_secret(token: str, key_id: str, encrypted_value: str, name: str):
    """Upsert a secret into the repo."""
    url = f"https://api.github.com/repos/{REPO}/actions/secrets/{name}"
    body = json.dumps({
        "encrypted_value": encrypted_value,
        "key_id": key_id,
    }).encode("utf-8")

    req = urllib.request.Request(url, data=body, method="PUT")
    req.add_header("Authorization", f"Bearer {token}")
    req.add_header("Accept", "application/vnd.github.v3+json")
    req.add_header("User-Agent", "Diwanic-CI-Setup/1.0")

    try:
        with urllib.request.urlopen(req) as resp:
            if resp.status in (201, 204):
                print(f"  ✅ {name} set")
            else:
                print(f"  ⚠️  {name} — HTTP {resp.status}")
    except urllib.error.HTTPError as e:
        print(f"  ❌ {name} — {e.code} {e.reason}")
        if e.code == 404:
            print("     Does the token have 'repo' scope? Is the repo private?")


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    token = sys.argv[1]

    # Load local .env (but secrets can also be passed manually)
    local_env = load_dotenv(".env")

    # Get public key
    print("Fetching repo public key...")
    key_id, public_key = get_public_key(token)
    print(f"  key_id: {key_id}\n")

    print("Setting secrets:")
    for env_var, secret_name in SECRETS_MAP.items():
        value = local_env.get(env_var, os.getenv(env_var, ""))
        if not value:
            print(f"  ⏭️  {secret_name} — skipping (no value found in .env or environment)")
            continue
        encrypted = encrypt_secret(public_key, value)
        set_secret(token, key_id, encrypted, secret_name)

    print("\n✅ Done. Push to main to trigger CI: git push origin main")


if __name__ == "__main__":
    main()
