from qdrant_client import QdrantClient
from diwanic.core.config import settings as config

def get_qdrant_client() -> QdrantClient:
    """
    Returns a configured QdrantClient instance.
    """
    if config.qdrant.url:
        return QdrantClient(url=config.qdrant.url, api_key=config.qdrant.api_key.get_secret_value())
    return QdrantClient(host=config.qdrant.host, port=config.qdrant.port)
