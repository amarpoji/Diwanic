from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from diwanic.search.engine import HybridSearchEngineV2
from diwanic.search.router import IntentRouter
from diwanic.schemas.search import SearchResponse
from diwanic.utils.logger_util import get_logger
import traceback

logger = get_logger(__name__)

router = APIRouter(prefix="/api/v2", tags=["search"])

class SearchRequest(BaseModel):
    query: str = Field(..., description="User search query, e.g. 'أفضل قصيدة في الحب لأبي نواس'")
    limit: int = Field(default=5, ge=1, le=20, description="Max number of results")

@router.post("/search")
def search(request: SearchRequest):
    intent_router = IntentRouter()
    engine = HybridSearchEngineV2()
    try:
        plan = intent_router.analyze_query(request.query)
        results = engine.search(plan, limit=request.limit)
        return SearchResponse(
            query=request.query,
            intent=plan.intent if hasattr(plan, "intent") else None,
            confidence=plan.confidence if hasattr(plan, "confidence") else None,
            results=results,
            total_results=len(results),
        )
    except Exception as e:
        logger.error(f"Search failed: {e}\n{traceback.format_exc()}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        engine.close()
