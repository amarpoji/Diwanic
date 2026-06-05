"""
Discover poet information from Aldiwan.net URL.
Robust version covering multiple page layouts.
"""
import sys
import re
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

from diwanic.scraper.fetcher import PoemFetcher

def discover_poet(poet_url: str):
    """
    Extract poet metadata from their Aldiwan page.
    Returns: slug, name, era
    """
    fetcher = PoemFetcher()
    soup = fetcher.get_soup(poet_url)
    
    if not soup:
        print("❌ Failed to fetch poet page")
        return None
    
    # 1. Extract slug from URL
    slug = poet_url.split('cat-poet-')[-1].strip('/')
    
    # 2. Extract Poet Name
    # Priority 1: h2 heading inside content
    name = "Unknown"
    h2_name = soup.find('h2', style=False, class_=False) 
    # Usually the poet name is in an <h2> without classes near the top
    # Or in h2 class="breadcrumbs"
    
    title_tag = soup.find('title')
    if title_tag:
        # Title usually looks like: "ديوان قيس بن الملوح - الديوان"
        title_text = title_tag.get_text()
        name_match = re.search(r'ديوان (.*?) -', title_text)
        if name_match:
            name = name_match.group(1).strip()

    # Priority 2: From breadcrumbs if title fails
    breadcrumb = soup.find('h2', class_='breadcrumbs')
    era = "Unknown"
    
    if breadcrumb:
        links = breadcrumb.find_all('a')
        # Format: الديوان » العصر العباسي » المتنبي
        if len(links) >= 2:
            # The last link is usually the poet, second to last is the era
            found_era = links[-1].get_text(strip=True) if len(links) == 2 else links[-2].get_text(strip=True)
            if "العصر" in found_era or "عصر" in found_era:
                era = found_era
            
            if name == "Unknown":
                name = links[-1].get_text(strip=True)

    # 3. Alternative Era Lookup (Paragraphs)
    if era == "Unknown":
        for p in soup.find_all('p'):
            p_text = p.get_text(strip=True)
            if "العصر" in p_text or "عصر" in p_text:
                # Basic check to avoid long paragraphs
                if len(p_text) < 50:
                    era = p_text
                    break

    # Clean up name (remove "ديوان " prefix if still there)
    name = name.replace("ديوان ", "").strip()
    
    # Count available poems
    poem_links = []
    for a in soup.find_all('a', href=True):
        href = a['href']
        if href.startswith('poem') and href.endswith('.html'):
            poem_links.append(href)
    
    poem_count = len(set(poem_links))
    
    print("=" * 60)
    print("📖 POET DISCOVERED")
    print("=" * 60)
    print(f"Slug:        {slug}")
    print(f"Name:        {name}")
    print(f"Era:         {era}")
    print(f"Poems:       ~{poem_count} available")
    print("=" * 60)
    print("\n✅ To add this poet, run:")
    print(f'./venv/bin/python scripts/add_poet.py "{slug}" "{name}" "{era}"')
    print()
    
    return {
        'slug': slug,
        'name': name,
        'era': era,
        'poem_count': poem_count
    }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    
    discover_poet(sys.argv[1])
