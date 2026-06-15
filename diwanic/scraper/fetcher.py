import requests
import time
from typing import Optional
from bs4 import BeautifulSoup

from diwanic.utils.logger_util import get_logger

logger = get_logger(__name__)

class PoemFetcher:
    def __init__(self, base_url: str = "https://www.aldiwan.net", delay: float = 1.5):
        self.base_url = base_url
        self.delay = delay
        self.session = requests.Session()
        
        # Modern browser User-Agent to avoid blocking
        self.session.headers.update({
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "ar,en-US;q=0.9,en;q=0.8",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8"
        })

    def fetch_page(self, url: str) -> Optional[str]:
        """Fetches the HTML content of a URL."""
        try:
            logger.info(f"Fetching URL: {url}")
            response = self.session.get(url, timeout=15)
            response.raise_for_status()
            
            # Let requests detect encoding automatically or force utf-8
            response.encoding = 'utf-8' 
            
            time.sleep(self.delay)  # Be polite, avoid rate limits
            return response.text
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch {url}: {e}")
            return None

    def get_soup(self, url: str) -> Optional[BeautifulSoup]:
        """Fetches the page and returns a BeautifulSoup object."""
        html = self.fetch_page(url)
        if html:
            return BeautifulSoup(html, 'html.parser')
        return None

    def fetch_poet_page(self, poet_name: str) -> Optional[BeautifulSoup]:
        """Fetches a poet's page (e.g., Al-Mutanabbi)."""
        # Format: cat-poet-Mutanabi
        poet_slug = poet_name.lower().replace(" ", "-")
        url = f"{self.base_url}/cat-poet-{poet_slug}"
        return self.get_soup(url)

    def fetch_poem_page(self, poem_id: str) -> Optional[BeautifulSoup]:
        """Fetches a specific poem page by ID (e.g., poem71682.html)."""
        url = f"{self.base_url}/{poem_id}"
        return self.get_soup(url)

    def fetch_random_poem(self) -> Optional[BeautifulSoup]:
        """Fetches a random poem page."""
        url = f"{self.base_url}/random"
        return self.get_soup(url)

if __name__ == "__main__":
    # Test the fetcher with a real poem URL
    fetcher = PoemFetcher()
    
    # Test 1: Fetch a specific poem
    logger.info("Test 1: Fetching poem71682.html...")
    soup = fetcher.fetch_poem_page("poem71682.html")
    
    if soup:
        logger.info(f"Successfully fetched poem page!")
        title = soup.title.string if soup.title else 'No Title'
        logger.info(f"Page Title: {title}")
        
        # Check if we got the poem content
        headings = soup.find_all('h3')
        if headings:
            logger.info(f"Found {len(headings)} verse headings")
            for i, h in enumerate(headings[:3]):
                logger.info(f"Verse {i+1}: {h.text[:50]}...")
    else:
        logger.error("Failed to fetch the poem page.")
    
    # Test 2: Fetch a poet page
    logger.info("\nTest 2: Fetching Al-Mutanabbi's page...")
    poet_soup = fetcher.fetch_poet_page("Mutanabi")
    
    if poet_soup:
        logger.info(f"Successfully fetched poet page!")
        poet_title = poet_soup.title.string if poet_soup.title else 'No Title'
        logger.info(f"Poet Page Title: {poet_title}")
    else:
        logger.error("Failed to fetch poet page.")
