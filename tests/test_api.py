import requests
import pytest

BASE_URL = "http://localhost:8000"

def test_api_health():
    """Verify the API health endpoint is reachable."""
    try:
        response = requests.get(f"{BASE_URL}/health", timeout=5)
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
    except requests.exceptions.ConnectionError:
        pytest.skip("API server not running at http://localhost:8000")

def test_api_search_params():
    """Verify search endpoint requires a query parameter."""
    try:
        response = requests.get(f"{BASE_URL}/search", timeout=5)
        assert response.status_code == 422 # Unprocessable Entity (missing param)
    except requests.exceptions.ConnectionError:
        pytest.skip("API server not running")
