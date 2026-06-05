"""
Scraping pipeline logic for Aldiwan.net.
"""
import yaml
from pathlib import Path
from typing import List
from diwanic.scraper.fetcher import PoemFetcher
from diwanic.scraper.parser import PoemParser
from diwanic.scraper.models import Poem
from diwanic.core.logger import get_logger

logger = get_logger(__name__)

def scrape_poet_poems(slug: str, max_poems: int = 50) -> List[dict]:
    """Scrape poems for a specific poet slug."""
    fetcher = PoemFetcher()
    parser = PoemParser()
    
    poet_url = f"https://www.aldiwan.net/cat-poet-{slug}"
    logger.info(f"Scraping poet: {slug} ({poet_url})")
    
    soup = fetcher.get_soup(poet_url)
    if not soup:
        return []
        
    # Extract all poem links
    poem_links = soup.find_all('a', href=True)
    poem_urls = []
    for link in poem_links:
        href = link['href']
        if '/poem' in href and '.html' in href:
            if not href.startswith('http'):
                href = f"https://www.aldiwan.net{href}"
            poem_urls.append(href)
    
    # Unique URLs
    poem_urls = list(dict.fromkeys(poem_urls))
    logger.info(f"Found {len(poem_urls)} poems for {slug}")
    
    scraped_poems = []
    for i, url in enumerate(poem_urls[:max_poems]):
        try:
            poem_data = parser.parse_poem(url)
            if poem_data and poem_data.get('verses'):
                # Validate with Poem model
                poem_obj = Poem.from_dict(poem_data)
                scraped_poems.append(poem_obj.to_dict())
                logger.info(f"  [{i+1}/{max_poems}] Scraped: {poem_data['title']}")
            else:
                logger.warning(f"  [{i+1}/{max_poems}] Skipped: {url} (no verses)")
        except Exception as e:
            logger.error(f"  [{i+1}/{max_poems}] Error scraping {url}: {e}")
            
    return scraped_poems

def scrape_all_poets(config_path: str = "configs/poets.yaml", max_poems_per_poet: int = 30) -> List[dict]:
    """Scrape all poets defined in the config file."""
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
        
    poets = config.get('poets', [])
    all_poems = []
    
    for poet in poets:
        slug = poet['slug']
        poems = scrape_poet_poems(slug, max_poems=max_poems_per_poet)
        all_poems.extend(poems)
        
    return all_poems

def save_poems(poems: List[dict], output_path: str):
    """Save poems to JSONL file."""
    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    import json
    with open(output_file, 'w', encoding='utf-8') as f:
        for poem in poems:
            f.write(json.dumps(poem, ensure_ascii=False) + '\n')
    
    logger.info(f"Saved {len(poems)} poems to {output_path}")
