"""
Embedding generation for Arabic poetry using multilingual-e5-small.
Converts searchable_text into 384-dimensional vectors.
"""
import json
from pathlib import Path
from typing import List

from sentence_transformers import SentenceTransformer
from diwanic.utils.logger_util import get_logger
from diwanic.utils.text_utils import normalize_arabic

logger = get_logger(__name__)

class PoemEmbedder:
    def __init__(self, model_name: str = "intfloat/multilingual-e5-small"):
        """
        Initialize the embedder with a multilingual model.
        
        Args:
            model_name: HuggingFace model identifier
        """
        logger.info(f"Loading model: {model_name}")
        self.model = SentenceTransformer(model_name)
        self.model_name = model_name
        
    def embed_text(self, text: str, prefix: str = "passage: ") -> List[float]:
        """
        Generate embedding for a single text.
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
        
        prefixed_text = prefix + text
        embedding = self.model.encode(prefixed_text)
        return embedding.tolist()
    
    def embed_batch(self, texts: List[str], prefix: str = "passage: ", 
                   batch_size: int = 16) -> List[List[float]]:
        """
        Generate embeddings for multiple texts (more efficient).
        
        Args:
            texts: List of texts to embed
            prefix: Prefix to add
            batch_size: Number of texts to process at once
        
        Returns:
            List of embedding vectors
        """
        prefixed_texts = [prefix + text for text in texts]
        embeddings = self.model.encode(prefixed_texts, batch_size=batch_size)
        return embeddings.tolist()
    
    def get_embedding_dimension(self) -> int:
        """Get the dimensionality of the embeddings."""
        return self.model.get_embedding_dimension()


def embed_poems(input_path: str, output_path: str, batch_size: int = 16):
    """
    Load poems from JSONL, generate embeddings for EACH VERSE, and save.
    
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
