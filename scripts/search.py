"""
CLI Search Tool for Diwanic.
Usage: ./venv/bin/python scripts/search.py "query string"
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from diwanic.search.engine import HybridSearchEngine
from diwanic.core.logger import get_logger

# Turn off verbose logging for clean CLI output
import logging
logging.getLogger("diwanic").setLevel(logging.WARNING)

def run_search(query: str):
    engine = HybridSearchEngine()
    results = engine.hybrid_search(query, limit=5)
    
    print("\n" + "═"*70)
    print(f"🔍 SEARCH RESULTS FOR: '{query}'")
    print("═"*70)
    
    if not results:
        print("\n   ❌ No poems found for this query.")
        return

    for i, r in enumerate(results, 1):
        print(f"\n✨ {i}. {r['title']}")
        print(f"   👤 {r['poet']}  |  ⏳ {r['era']}")
        print(f"   🏆 Score: {r['hybrid_score']:.6f}")
        print("-" * 40)
        
        # Format the text preview nicely
        preview = r['original_text'].strip()
        if len(preview) > 200:
            preview = preview[:200] + "..."
        
        # Indent and print text
        for line in preview.split('\n'):
            print(f"   {line}")
        print()

    print("═"*70 + "\n")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: ./venv/bin/python scripts/search.py 'your search query'")
        sys.exit(1)
        
    query = " ".join(sys.argv[1:])
    run_search(query)
