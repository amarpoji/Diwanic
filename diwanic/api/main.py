"""
FastAPI Server for Diwanic Poetry Search.
Exposes hybrid search and metadata endpoints.
"""
from fastapi import FastAPI, Query, HTTPException
from typing import List, Optional
from pydantic import BaseModel

from diwanic.search.engine import HybridSearchEngine
from diwanic.core.logger import get_logger

logger = get_logger(__name__)

app = FastAPI(
    title="Diwanic API",
    description="Arabic Poetry Retrieval System (Hybrid Search)",
    version="1.0.0"
)

# Initialize the search engine once
engine = HybridSearchEngine()

class SearchResult(BaseModel):
    poem_id: str
    title: str
    poet: str
    era: str
    original_text: str
    hybrid_score: float

class Status(BaseModel):
    status: str
    version: str

@app.get("/", response_model=Status)
async def root():
    """Health check and status."""
    return {"status": "online", "version": "1.0.0"}

@app.get("/search", response_model=List[SearchResult])
async def search(
    q: str = Query(..., description="The search query (Arabic)"),
    limit: int = Query(10, ge=1, le=50),
    vector_weight: float = 0.7,
    keyword_weight: float = 0.3
):
    """
    Perform hybrid search (Vector + Keyword) on the poetry collection.
    """
    logger.info(f"API Search request: {q}")
    try:
        results = engine.hybrid_search(
            query=q, 
            limit=limit, 
            vector_weight=vector_weight, 
            keyword_weight=keyword_weight
        )
        return results
    except Exception as e:
        logger.error(f"Search failed: {e}")
        raise HTTPException(status_code=500, detail="Search engine failure")

@app.get("/poets")
async def get_poets():
    """Get list of poets (placeholder - normally from DB)."""
    # This would ideally come from a DB call to DiwanicDB
    return {"message": "Poet list endpoint under construction"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
