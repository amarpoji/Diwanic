"""
Reciprocal Rank Fusion (RRF) for Diwanic search engine.
"""
from typing import List, Dict, Any


def reciprocal_rank_fusion(
    results_list: List[List[Dict[str, Any]]], 
    k: int = 60
) -> List[Dict[str, Any]]:
    """
    RRF algorithm to merge multiple ranked lists.
    Formula: score = sum(1 / (k + rank))
    """
    fused_scores = {}

    for results in results_list:
        for rank, item in enumerate(results):
            # item must have a unique 'poem_id' or 'id'
            item_id = item.get("poem_id") or item.get("id")
            if not item_id:
                continue

            if item_id not in fused_scores:
                fused_scores[item_id] = {"score": 0.0, "item": item}

            fused_scores[item_id]["score"] += 1.0 / (k + rank + 1)

    # Sort by fused score descending
    fused_results = sorted(
        fused_scores.values(),
        key=lambda x: x["score"],
        reverse=True
    )

    # Return sorted items with their new scores
    final_results = []
    for entry in fused_results:
        item = entry["item"]
        item["rrf_score"] = entry["score"]
        final_results.append(item)

    return final_results
