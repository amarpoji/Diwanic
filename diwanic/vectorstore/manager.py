"""
Qdrant vector store manager for Diwanic.
Handles collection creation, data upserting, and search.
"""
import json
from typing import List, Dict, Optional

from qdrant_client import QdrantClient
from qdrant_client.http import models
from diwanic.core.config import settings as config
from diwanic.utils.logger_util import get_logger

logger = get_logger(__name__)


class DiwanicVectorStore:
    def __init__(self):
        """Initialize Qdrant client based on configuration."""
        if config.qdrant.url:
            logger.info(f"Connecting to Qdrant Cloud: {config.qdrant.url}")
            return QdrantClient(
                url=config.qdrant.url,
                api_key=config.qdrant.api_key.get_secret_value()
            )
        else:
            logger.info(f"Connecting to Qdrant Local: {config.qdrant.host}:{config.qdrant.port}")
            return QdrantClient(
                host=config.qdrant.host,
                port=config.qdrant.port
            )
        
        self.collection_name = "poems"

    def create_collection(self, vector_size: int = 384):
        """Create a new collection for poems."""
        logger.info(f"Creating collection '{self.collection_name}' with size {vector_size}...")
        
        # Check if exists
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        
        if exists:
            logger.info(f"Collection '{self.collection_name}' already exists. Overwriting...")
            self.client.delete_collection(self.collection_name)
            
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=vector_size,
                distance=models.Distance.COSINE
            )
        )
        logger.info(f"✅ Collection created.")

    def upsert_poems(self, poems_path: str):
        """Load poems with embeddings from JSONL and upsert to Qdrant."""
        logger.info(f"Loading poems from {poems_path}...")
        
        points = []
        with open(poems_path, 'r', encoding='utf-8') as f:
            for i, line in enumerate(f):
                poem = json.loads(line)
                
                # Payload: metadata stored in Qdrant for filtering
                payload = {
                    "poem_id": poem.get("poem_id"),
                    "title": poem.get("title"),
                    "poet": poem.get("poet"),
                    "era": poem.get("era"),
                    "meter": poem.get("meter"),
                    "category": poem.get("category"),
                    "rhyme": poem.get("rhyme"),
                    "original_text": poem.get("original_text"),
                    "searchable_text": poem.get("searchable_text"),
                    "source_url": poem.get("source_url")
                }
                
                # Point for Qdrant
                points.append(models.PointStruct(
                    id=i,  # Simple integer ID
                    vector=poem.get("embedding"),
                    payload=payload
                ))
        
        logger.info(f"Upserting {len(points)} points to '{self.collection_name}'...")
        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        logger.info("✅ Upsert complete.")

    def search(self, query_vector: List[float], limit: int = 5, filters: Optional[Dict] = None):
        """Perform vector search."""
        query_filter = None
        if filters:
            must = []
            for key, value in filters.items():
                must.append(models.FieldCondition(
                    key=key,
                    match=models.MatchValue(value=value)
                ))
            query_filter = models.Filter(must=must)
        
        # query_points returns a QueryResponse object, access .points for the list
        result = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector,
            query_filter=query_filter,
            limit=limit
        )
        
        # Return the list of points from the result
        return result.points
