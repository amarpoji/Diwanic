"""
Diwanic Search Schemas
======================

Pydantic models that represent the RESPONSE side of the retrieval pipeline.

Responsibility
--------------
These schemas define what the UI / API client receives:

- ``SearchResult`` : A single poem or verse with all metadata.
- ``SearchResponse`` : The complete response wrapper (query, intent, results).

These models are the **public contract**.  Changes here must be version-controlled
to avoid breaking the UI or any downstream consumers.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class SearchResult(BaseModel):
    """A single search result returned to the user."""
    poem_id: str = Field(description="Unique poem identifier")
    title: str = Field(description="Poem title")
    poet: str = Field(description="Poet name")
    era: Optional[str] = Field(default=None, description="Literary era")
    original_text: str = Field(description="Original Arabic poem text or verse")
    searchable_text: Optional[str] = Field(default=None, description="Normalized searchable text")
    score: float = Field(description="Final relevance score")
    source: Optional[str] = Field(default=None, description="Which retrieval source produced the result, e.g. vector, keyword, fused")
    verse_index: Optional[int] = Field(default=None, description="Index of the matching verse within the poem")
    match_type: Optional[str] = Field(default="poem", description="Whether the result is a full 'poem' match or a 'verse' match")


class SearchResponse(BaseModel):
    """Top-level response returned by the API."""
    query: str = Field(description="Original user query")
    intent: Optional[str] = Field(default=None, description="Detected query intent")
    confidence: Optional[float] = Field(default=None, description="Router confidence")
    results: List[SearchResult] = Field(default_factory=list, description="List of ranked results")
    total_results: int = Field(default=0, description="Number of returned results")
    message: Optional[str] = Field(default=None, description="Optional friendly message")