"""
Diwanic Query Schemas
=====================

Pydantic models that represent the contract between the Intent Router
and the downstream retrieval components.

Responsibility
--------------
These schemas define the "shape" of data that flows through the system:

- ``ExtractedFilters`` : Hard constraints (poet, era, category) extracted by the LLM.
- ``IntentResult``     : Deprecated / reference for future two-stage routing.
- ``SearchPlan``       : The ACTIVE contract — what the router returns and the engine consumes.

These models are the **single source of truth** for type validation.  Any change
to the JSON contract must be reflected here first.
"""

from typing import Optional, Literal
from pydantic import BaseModel, Field


class ExtractedFilters(BaseModel):
    """Hard filters extracted from the user's query."""

    poet_name: Optional[str] = Field(
        default=None,
        description="Arabic poet name to filter by, e.g. 'أبو نواس'",
    )
    era: Optional[str] = Field(
        default=None,
        description="Literary era, e.g. 'العصر العباسي'",
    )
    category: Optional[str] = Field(
        default=None,
        description="Poem category, e.g. 'مدح', 'هجاء', 'غزل', 'رثاء', 'حكمة'",
    )
    meter: Optional[str] = Field(
        default=None,
        description="Poetic meter, e.g. 'البحر الطويل'",
    )
    rhyme: Optional[str] = Field(
        default=None,
        description="Rhyme letter or rhyme pattern",
    )


# NOTE:
# IntentResult is kept as a reference for a future two-step router flow
# (intent detection first, search planning second).
# At the moment, the active router returns SearchPlan directly.
class IntentResult(BaseModel):
    """Only the intent/language side of the query (future/optional layer)."""

    intent: Literal[
        "search_poems",
        "search_poets",
        "search_verses",
        "ask_about_poet",
        "ask_about_poem",
        "unknown",
    ] = Field(description="The type of user request")
    original_query: str = Field(description="The exact user query")
    language: Optional[str] = Field(default=None, description="Detected language such as 'ar', 'ms', 'en'")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="How confident the router is")
    needs_clarification: bool = Field(default=False, description="Whether the system should ask a follow-up question")
    clarification_question: Optional[str] = Field(default=None, description="Question to ask if clarification is needed")
    notes: Optional[str] = Field(default=None, description="Optional internal notes")


# NOTE:
# SearchPlan is the ACTIVE schema used by the current router.
# The router returns this object, and the retrieval engine consumes it directly.
class SearchPlan(BaseModel):
    """What the retrieval engine should search for."""

    original_query: str = Field(description="The exact user query")
    semantic_query: str = Field(description="Clean Arabic semantic query for vector search")
    filters: ExtractedFilters = Field(default_factory=ExtractedFilters, description="Hard filters extracted from the query")
    intent: Literal[
        "search_poems",
        "search_poets",
        "search_verses",
        "ask_about_poet",
        "ask_about_poem",
        "unknown",
    ] = Field(description="The type of user request")
    language: Optional[str] = Field(default=None, description="Detected language such as 'ar', 'ms', 'en'")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="How confident the router is")
