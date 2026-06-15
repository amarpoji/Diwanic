import json
import os
import logfire
from diwanic.core.observability import setup_observability
from diwanic.search.engine import HybridSearchEngineV2
from diwanic.search.router import IntentRouter

# Initialize observability after imports
setup_observability()

class SearchEvaluator:
    def __init__(self):
        self.router = IntentRouter()
        self.engine = HybridSearchEngineV2()

    def run_eval(self, golden_set_path: str, top_k: int = 3):
        print(f"\n🚀 --- Starting Evaluation using: {golden_set_path} --- 🚀")
        mrr_scores = []
        top_k_hits = 0
        total_queries = 0
        
        with logfire.span("evaluation_run"):
            try:
                with open(golden_set_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if not line:
                            continue
                            
                        item = json.loads(line)
                        query = item['query']
                        expected_id = item['expected_poem_id']
                        total_queries += 1
                        
                        try:
                            # 1. Analyze Intent
                            plan = self.router.analyze_query(query)
                            
                            # 2. Execute Search
                            results = self.engine.search(plan, limit=10)
                            
                            # 3. Determine Rank
                            found_rank = None
                            for i, res in enumerate(results):
                                if res.poem_id == expected_id:
                                    found_rank = i + 1
                                    break
                            
                            # 4. Compute Metrics for this query
                            score = 1 / found_rank if found_rank else 0
                            mrr_scores.append(score)
                            
                            is_top_k = found_rank is not None and found_rank <= top_k
                            if is_top_k:
                                top_k_hits += 1
                                
                            # Display status
                            status = f"✅ Rank {found_rank}" if found_rank else "❌ Not Found"
                            print(f"Query: {query[:35]:<35} | {status:<12} | MRR: {score:.3f} | Top-{top_k}: {is_top_k}")
                            
                        except Exception as e:
                            print(f"Query: {query[:35]:<35} | ⚠️ ERROR: {str(e)}")
                            logfire.error("Evaluation error on query", query=query, error=str(e))
                            mrr_scores.append(0)
            
            except FileNotFoundError:
                print(f"❌ Error: Golden set file not found at {golden_set_path}")
                return
            
            # 5. Final Calculations
            avg_mrr = sum(mrr_scores) / len(mrr_scores) if mrr_scores else 0
            recall_top_k = (top_k_hits / total_queries) * 100 if total_queries else 0
            
            print(f"\n📊 --- Final Metrics ({total_queries} queries) --- 📊")
            print(f"🎯 Mean Reciprocal Rank (MRR): {avg_mrr:.3f} (Aim for > 0.6)")
            print(f"🎯 Top-{top_k} Recall: {recall_top_k:.1f}% (Aim for > 80%)")
            
            logfire.info("Evaluation Complete", mrr=avg_mrr, top_k_recall=recall_top_k, total_queries=total_queries)

if __name__ == "__main__":
    golden_path = "tests/golden_set.jsonl"
    if not os.path.exists(golden_path):
        print(f"Please create a golden set at {golden_path} to run the evaluation.")
    else:
        evaluator = SearchEvaluator()
        evaluator.run_eval(golden_path, top_k=3)
