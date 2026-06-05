"""
Embedding generation for Arabic poetry using multilingual-e5-small.
Converts searchable_text into 384-dimensional vectors.
"""
import sys
import json
from pathlib import Path
from typing import List

sys.path.insert(0, str(Path(__file__).parent.parent))

from sentence_transformers import SentenceTransformer
from diwanic.core.logger import get_logger

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
    Load poems from JSONL, generate embeddings, and save to new JSONL.
    
    Args:
        input_path: Path to poems_cleaned.jsonl
        output_path: Path to save poems_with_embeddings.jsonl
        batch_size: Batch size for embedding generation
    
    Returns:
        Number of poems embedded
    """
    embedder = PoemEmbedder()
    dim = embedder.get_embedding_dimension()
    logger.info(f"Embedding dimension: {dim}")
    
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_path}")
        return 0
    
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger.info(f"Reading poems from: {input_path}")
    
    # First pass: collect all searchable_text
    poems = []
    texts = []
    
    with open(input_file, 'r', encoding='utf-8') as f:
        for line in f:
            if not line.strip():
                continue
            poem = json.loads(line)
            poems.append(poem)
            texts.append(poem.get('searchable_text', ''))
    
    logger.info(f"Loaded {len(poems)} poems")
    
    if len(poems) == 0:
        logger.warning("No poems to embed")
        return 0
    
    # Generate embeddings in batches
    logger.info(f"Generating embeddings with batch_size={batch_size}...")
    embeddings = embedder.embed_batch(texts, batch_size=batch_size)
    
    # Write poems with embeddings
    logger.info(f"Writing to: {output_path}")
    with open(output_file, 'w', encoding='utf-8') as f:
        for poem, embedding in zip(poems, embeddings):
            poem['embedding'] = embedding
            poem['model'] = embedder.model_name
            poem['embedding_dim'] = dim
            f.write(json.dumps(poem, ensure_ascii=False) + '\n')
    
    logger.info(f"✅ Embedded {len(poems)} poems")
    logger.info(f"💾 Saved to: {output_path}")
    
    return len(poems)


if __name__ == "__main__":
    INPUT = "data/processed/poems_cleaned.jsonl"
    OUTPUT = "data/embeddings/poems_with_embeddings.jsonl"
    
    embed_poems(INPUT, OUTPUT, batch_size=16)
