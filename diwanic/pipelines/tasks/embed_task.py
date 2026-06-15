"""Prefect task for generating embeddings."""
from prefect import task
from diwanic.embeddings.generator import embed_poems

@task
def embed_poems_task(input_path: str = "data/processed/poems_cleaned.jsonl", output_path: str = "data/embeddings/poems_with_embeddings.jsonl"):
    """
    Generate embeddings for cleaned poems and save to JSONL.
    """
    count = embed_poems(input_path, output_path)
    return count
