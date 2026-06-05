"""
Add a new poet to the scraping list.
Usage: python scripts/add_poet.py <slug> <name> <era>
Example: python scripts/add_poet.py IbnSufyan_Fayyumi ابن سفيان الفيومي العصر العباسي
"""
import sys
import yaml
from pathlib import Path

CONFIG_PATH = "configs/poets.yaml"

def load_poets():
    with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)

def save_poets(poets_data):
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        yaml.dump(poets_data, f, allow_unicode=True, sort_keys=False)

def add_poet(slug: str, name: str, era: str):
    poets = load_poets()
    
    # Check if already exists
    for p in poets['poets']:
        if p['slug'] == slug:
            print(f"⚠️  Poet '{slug}' already exists: {p['name']}")
            return
    
    # Add new poet
    poets['poets'].append({
        'slug': slug,
        'name': name,
        'era': era
    })
    
    save_poets(poets)
    print(f"✅ Added: {name} ({slug}) - {era}")
    print(f"   Run: ./venv/bin/python -m scripts.scrape_all")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print(__doc__)
        sys.exit(1)
    
    add_poet(sys.argv[1], sys.argv[2], sys.argv[3])