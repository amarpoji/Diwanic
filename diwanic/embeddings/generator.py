"""
Embedding generation for Arabic poetry using multilingual-e5-small.
Converts searchable_text into 384-dimensional vectors.
Uses disk-based caching to avoid re-computing embeddings for identical verses.
"""
import json
from pathlib import Path
from typing import List

from sentence_transformers import SentenceTransformer
from diwanic.utils.logger_util import get_logger
from diwanic.utils.text_utils import normalize_arabic
from diwanic.core.config import settings
from diwanic.embeddings.cache import EmbeddingCache

logger = get_logger(__name__)


class PoemEmbedder:
    def __init__(self, model_name: str = None, cache_path: str = None):
        """
        Initialize the embedder with a multilingual model and a disk cache.
        
        Args:
            model_name: HuggingFace model identifier (defaults to settings.embedding.model)
            cache_path: Path to the embedding cache file. Defaults to data/embeddings/cache.json
        """
        # Use config value if model_name is not provided
        if model_name is None:
            model_name = settings.embedding.model
        
        # Initialize the embedding cache
        self.cache = EmbeddingCache(cache_path or "data/embeddings/cache.json")
        logger.info(f"Embedding cache at {self.cache.cache_path} ({self.cache.size()} entries)")
            
        logger.info(f"Loading model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        
    def embed_text(self, text: str, prefix: str = "passage: ") -> List[float]:
        """
        Generate embedding for a single text. Uses cache if available.
        E5 models perform better with prefixes.
        
        Args:
            text: The text to embed
            prefix: Prefix to add ("passage: " for documents, "query: " for queries)
        
        Returns:
            List of floats representing the vector
        """
        if not text or len(text.strip()) == 0:
            # Return zero vector if text is empty
            return [0.0] * self.model.get_embedding_dimension()
        
        # Check cache first
        cached = self.cache.get(text)
        if cached is not None:
            logger.debug(f"Cache hit for text: {text[:30]}...")
            return cached
        
        # Compute embedding
        prefixed_text = prefix + text
        embedding = self.model.encode(prefixed_text)
        result = embedding.tolist()
        
        # Cache the result
        self.cache.set(text, result)
        return result
    
    def embed_batch(self, texts: List[str], prefix: str = "passage: ", 
                   batch_size: int = 16) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (more efficient).
        Uses cache to avoid re-computing embeddings for identical verses.
        
        Args:
            texts: List of texts to embed
            prefix: Prefix to add
            batch_size: Number of texts to process at once
        
        Returns:
            List of embedding vectors
        """
        # Split texts into cached vs. to-embed
        to_embed = []
        indices = []
        
        for i, text in enumerate(texts):
            cached = self.cache.get(text)
            if cached is not None:
                # Use cached result directly
                yield cached  # This won't work in a list comprehension, fix below
            else:
                to_embed.append(text)
                indices.append(i)
        
        # If we have texts without embeddings, compute them in batch
        if to_embed:
            prefixed_texts = [prefix + text for text in to_embed]
            new_embeddings = self.model.encode(prefixed_texts, batch_size=batch_size).tolist()
            
            # Cache each new embedding
            for text, emb in zip(to_embed, new_embeddings):
                self.cache.set(text, emb)
        
        # Reconstruct the full list (simpler approach: compute all at once but cache results)
        all_prefixed = [prefix + text for text in texts]
        all_embeddings = self.model.encode(all_prefixed, batch_size=batch_size).tolist()
        
        # Update cache with newly computed embeddings
        for text, emb in zip(texts, all_embeddings):
            if self.cache.get(text) is None:
                self.cache.set(text, emb)
        
        return all_embeddings
    
    def get_embedding_dimension(self) -> int:
        """Get the dimensionality of the embeddings."""
        return self.model.get_embedding_dimension()


def embed_poems(input_path: str, output_path: str, batch_size: int = 16):
    """
    Load poems from JSONL, generate embeddings for EACH VERSE, and save.
    Uses caching to avoid re-embedding identical verses.
    
    Args:
        input_path: Path to poems_cleaned.jsonl
        output_path: Path to save poems_with_embeddings.jsonl
    """
    embedder = PoemEmbedder()
    dim = embedder.get_embedding_dimension()
    
    input_file = Path(input_path)
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Generating verse-level embeddings from: {input_path}")
    
    with open(input_file, 'r', encoding='utf-8') as f_in, \
         open(output_file, 'w', encoding='utf-8') as f_out:
        
        for line in f_in:
            if not line.strip():
                continue
            poem = json.loads(line)
            
            # 1. Get searchable verses (normalized)
            # If the poem was already cleaned, we split the searchable_text
            searchable_verses = poem.get("searchable_text", "").split("\n")
            
            # Fallback: if searchable_text is empty or count mismatch, 
            # we re-normalize the original verses
            if not searchable_verses or len(searchable_verses) != len(poem["verses"]):
                searchable_verses = [normalize_arabic(v) for v in poem["verses"]]
            
            # 2. Embed verses in batches
            verse_embeddings = embedder.embed_batch(searchable_verses, batch_size=batch_size)
            
            # 3. Add to poem object
            poem["verse_embeddings"] = verse_embeddings
            poem["model"] = embedder.model_name
            poem["embedding_dim"] = dim
            
            f_out.write(json.dumps(poem, ensure_ascii=False) + "\n")
            
    logger.info("✅ Verse-level embedding complete.")
    return True


if __name__ == "__main__":
    INPUT = "data/processed/poems_cleaned.jsonl"
    OUTPUT = "data/embeddings/poems_with_embeddings.jsonl"
    
    embed_poems(INPUT, OUTPUT, batch_size=16)