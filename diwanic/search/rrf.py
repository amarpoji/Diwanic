"""
Reciprocal Rank Fusion (RRF) for Diwanic search engine.
"""
from typing import List, Dict, Any


def reciprocal_rank_fusion(
    results_list: List[List[Dict[str, Any]]],
    k: int = 60,
) -> List[Dict[str, Any]]:
    """
    RRF algorithm to merge multiple ranked lists.

    Uses the caller-provided ``id`` as the primary dedupe key.
    This lets verse-level results remain unique (e.g. ``v_<poem>_<verse>``)
    while poem-level results can still collapse naturally via ``k_<poem>``.
    """
    fused_scores: Dict[str, Dict[str, Any]] = {}

    for results in results_list:
        for rank, item in enumerate(results):
            item_id = item.get("id") or item.get("poem_id")
            if not item_id:
                continue

            if item_id not in fused_scores:
                fused_scores[item_id] = {"score": 0.0, "item": item}

            fused_scores[item_id]["score"] += 1.0 / (k + rank + 1)

    fused_results = sorted(
        fused_scores.values(),
        key=lambda x: x["score"],
        reverse=True,
    )

    final_results = []
    for entry in fused_results:
        item = entry["item"]
        item["rrf_score"] = entry["score"]
        final_results.append(item)

    return final_results
