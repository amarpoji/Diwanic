import json
from openai import OpenAI

from diwanic.core.config import settings as config
from diwanic.schemas.query import SearchPlan
from diwanic.utils.logger_util import get_logger
import logfire

logger = get_logger(__name__)

# Standard OpenAI client pointing to 9Router
client = OpenAI(
    base_url=config.router.base_url,
    api_key=config.router.api_key.get_secret_value() or "dummy-key",
)

class IntentRouter:
    """
    Agent that translates raw Arabic user queries into a structured ``SearchPlan``.

    Responsibility
    --------------
    Given a natural-language query, this class calls the configured LLM
    (via 9Router) to extract:
    - ``semantic_query`` : the theme in Classical Arabic.
    - ``filters``        : poet_name, era, category, meter, rhyme.
    - ``intent``         : ``search_poems`` or ``ask_about_poet``.

    Threading / Async
    ------------------
    This class is stateless after construction.  ``analyze_query`` blocks
    on an HTTP call; wrap it in ``asyncio.to_thread()`` from async code.

    Configuration
    -------------
    ``config.router.base_url``, ``config.router.api_key``, and
    ``config.router.model`` are read once at import time.
    """

    def __init__(self, model: str = config.router.model):
        self.model = model

    def analyze_query(self, query: str) -> SearchPlan:
        """Return a structured SearchPlan for retrieval."""
        
        system_prompt = """
You are an expert Arabic poetry search router.
Your job is to convert the user query into a structured JSON object.

IMPORTANT RULES:
1. Return ONLY valid JSON matching the exact schema. Do not include markdown formatting like ```json.
2. filters must always be a real nested JSON object.
3. semantic_query must contain the core theme/meaning translated into Classical Arabic.
4. Remove poet names from semantic_query if they are used as filters.
5. Use poet_name only when the user clearly mentions a poet (e.g., أبو نواس, أحمد شوقي, المتنبي, الأصمعي, الإمام الشافعي).
6. Use era only for historical eras like العصر العباسي, العصر الأموي.
7. Use category only for real literary categories like مدح, هجاء, غزل, رثاء, حكمة.
8. Use meter for rhythmic structures like البحر الطويل, البحر البسيط.
9. Emotional words (sad, brave, love) should go into semantic_query, not category, unless it perfectly fits غزل (love poetry) or رثاء (elegies).
10. If the query asks "Who is X?", set intent to 'ask_about_poet'.

Expected JSON Structure:
{
  "original_query": "...",
  "semantic_query": "...",
  "filters": {
    "poet_name": null,
    "era": null,
    "category": null,
    "meter": null,
    "rhyme": null
  },
  "intent": "search_poems",
  "language": "en",
  "confidence": 0.95 
}
"""
        with logfire.span("router_analyze_query", query=query):
            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": query},
                ],
                temperature=0.1,  # Low temperature for consistent JSON
            )

            raw_content = response.choices[0].message.content

            # FIX: Handle both string and dict responses from the LLM
            if isinstance(raw_content, dict):
                parsed_data = raw_content
            elif isinstance(raw_content, str):
                raw_content = raw_content.strip()
                if raw_content.startswith("```json"):
                    raw_content = raw_content[7:-3].strip()
                elif raw_content.startswith("```"):
                    raw_content = raw_content[3:-3].strip()
                try:
                    parsed_data = json.loads(raw_content)
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse router response as JSON: {raw_content}")
                    raise e
            else:
                raise ValueError(f"Unexpected response type from LLM: {type(raw_content)} = {raw_content}")

            # Log the parsed plan
            logfire.info("Router plan", intent=parsed_data.get("intent"), 
                         confidence=parsed_data.get("confidence"),
                         filters=parsed_data.get("filters"))
            
            # Validate and return the SearchPlan
            return SearchPlan(**parsed_data)
