"""
Load embeddings into Qdrant vector database.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from diwanic.vectorstore.manager import DiwanicVectorStore
from diwanic.core.config import config

if __name__ == "__main__":
    # Check if config is set
    if not config.QDRANT_API_KEY and not config.QDRANT_URL:
        print("❌ Error: QDRANT_URL or QDRANT_API_KEY not found in .env")
        print("   Please create a cluster at https://cloud.qdrant.io and add them to your .env file.")
        sys.exit(1)
        
    EMBEDDINGS_PATH = "data/embeddings/poems_with_embeddings.jsonl"
    
    print("🚀 Connecting to Qdrant...")
    store = DiwanicVectorStore()
    
    # 1. Create collection (E5-small is 384 dimensions)
    store.create_collection(vector_size=384)
    
    # 2. Upsert poems
    store.upsert_poems(EMBEDDINGS_PATH)
    
    print("\n✅ Data loaded into Qdrant successfully!")
    print(f"   Collection: {store.collection_name}")
    print("   Next step: Run a test search!")
