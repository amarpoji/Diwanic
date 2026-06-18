import pytest
from diwanic.core.config import settings

def test_config_loading():
    """Verify that settings are loaded correctly from env or defaults."""
    assert settings.qdrant.collection_poems == "poems"
    assert settings.embedding.dim == 384
