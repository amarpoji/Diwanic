"""Prefect task for preprocessing poems."""
from prefect import task
from diwanic.preprocessing.pipeline import process_poems

@task
def preprocess_poems_task(input_path: str = "data/raw/poems_all.jsonl", output_path: str = "data/processed/poems_cleaned.jsonl"):
    """
    Clean and preprocess poems from raw JSONL and save to processed JSONL.
    """
    count = process_poems(input_path, output_path)
    return count
