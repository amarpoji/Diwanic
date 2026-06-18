from fastapi import FastAPI, Query, HTTPException
from typing import List, Dict, Any
from diwanic.app.portal import perform_semantic_search
from diwanic.storage.repository import DiwanicRepository
from diwanic.app.database import SessionLocal

app = FastAPI(title="Diwanic API")

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/search")
async def search(
    query: str = Query(..., description="The poetry search query"),
    limit: int = Query(10, ge=1, le=50)
):
    try:
        results = perform_semantic_search(query=query, limit=limit)
        return {"query": query, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/poet/{poet_slug}")
async def get_poet(poet_slug: str):
    db = SessionLocal()
    repo = DiwanicRepository(db)
    poet = repo.get_poet_by_slug(poet_slug)
    db.close()
    if not poet:
        raise HTTPException(status_code=404, detail="Poet not found")
    return {"name": poet.name_ar, "era": poet.era, "slug": poet.slug}
