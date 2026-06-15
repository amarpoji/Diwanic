"""
Verse-level Qdrant manager for Diwanic.
"""
import uuid
from typing import List, Dict, Any
from qdrant_client import QdrantClient
from qdrant_client.http import models
from diwanic.core.config import settings as config
from diwanic.utils.logger_util import get_logger

logger = get_logger(__name__)

class DiwanicVerseStore:
    def __init__(self):
        """Initialize Qdrant client based on configuration."""
        if config.qdrant.url:
            logger.info(f"Connecting to Qdrant Cloud: {config.qdrant.url}")
            self.client = QdrantClient(
                url=config.qdrant.url,
                api_key=config.qdrant.api_key.get_secret_value(),
                timeout=60.0
            )
        else:
            logger.info(f"Connecting to Qdrant Local: {config.qdrant.host}:{config.qdrant.port}")
            self.client = QdrantClient(
                host=config.qdrant.host,
                port=config.qdrant.port,
                timeout=60.0
            )
        self.collection_name = "verses"

    def create_collection(self, vector_size: int = 384):
        logger.info(f"Creating collection '{self.collection_name}' with size {vector_size}...")
        
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        
        if exists:
            logger.info(f"Collection '{self.collection_name}' exists. Overwriting...")
            self.client.delete_collection(self.collection_name)
            
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE
            )
        )
        
        # Create payload indexes for filtering
        self.client.create_payload_index(self.collection_name, "poet", models.PayloadSchemaType.KEYWORD)
        self.client.create_payload_index(self.collection_name, "era", models.PayloadSchemaType.KEYWORD)
        self.client.create_payload_index(self.collection_name, "poem_id", models.PayloadSchemaType.KEYWORD)
        logger.info(f"✅ Collection created with indexes.")

    def upsert_verses(self, verses_data: List[Dict[str, Any]]):
        """
        Upsert verses to Qdrant with deterministic IDs (poem_id:verse_index)
        for idempotency. Payload is kept minimal as metadata truth resides in Postgres.
        
        Expects a list of dicts: 
        {
            "vector": list,
            "payload": {
                "poem_id": str (uuid),
                "verse_index": int,
                "poet": str,  # Kept for filtering
                "era": str,   # Kept for filtering
                "text": str   # Kept for immediate debug view (optional)
            }
        }
        """
        # Namespace for generating deterministic UUIDs
        DIWANIC_NAMESPACE = uuid.UUID('6ba7b810-9dad-11d1-80b4-00c04fd430c8') # Using DNS namespace as base

        points = []
        for v in verses_data:
            poem_id = v["payload"]["poem_id"]
            verse_idx = v["payload"]["verse_index"]
            
            # Generate deterministic UUID: poem_id + verse_index
            stable_id = str(uuid.uuid5(DIWANIC_NAMESPACE, f"{poem_id}:{verse_idx}"))
            
            points.append(
                models.PointStruct(
                    id=stable_id,
                    vector=v["vector"],
                    payload={
                        "poem_id": poem_id,
                        "verse_index": verse_idx,
                        "poet": v["payload"].get("poet"),
                        "era": v["payload"].get("era"),
                        "text": v["payload"].get("text")
                    }
                )
            )
        
        logger.info(f"Upserting {len(points)} verses to '{self.collection_name}' with stable IDs...")
        self.client.upsert(
            collection_name=self.collection_name,
            points=points,
            wait=True
        )
        logger.info("✅ Idempotent verse upsert complete.")
