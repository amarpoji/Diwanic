from typing import Dict, Any
from bs4 import BeautifulSoup
from diwanic.utils.logger_util import get_logger

logger = get_logger(__name__)

class PoemParser:
    def __init__(self):
        pass

    def parse_poem(self, soup: BeautifulSoup, url: str) -> Dict[str, Any]:
        """Parses a poem page and returns structured data."""
        
        # 1. Extract Title from the <title> tag or breadcrumb
        # Page title format: "خذ في البكا إن الخليط مقوض - المتنبي - الديوان"
        page_title = ""
        if soup.title:
            page_title = soup.title.string.strip()
        
        # The breadcrumb h2 contains the full path
        title = ""
        poet = ""
        era = ""
        
        breadcrumb_h2 = soup.find('h2')
        if breadcrumb_h2:
            # Get all links in the breadcrumb
            links = breadcrumb_h2.find_all('a')
            if len(links) >= 2:
                era = links[1].text.strip()
            if len(links) >= 3:
                poet = links[2].text.strip()
            
            # Get the title from the breadcrumb text after the last link
            breadcrumb_text = breadcrumb_h2.get_text()
            parts = breadcrumb_text.split('»')
            if len(parts) >= 4:
                title = parts[-1].strip()
            elif len(parts) >= 3:
                title = parts[-1].strip()
        
        # Fallback: extract title from <title> tag
        if not title and ' - ' in page_title:
            title = page_title.split(' - ')[0].strip()
        
        # 3. Extract Verses
        # Verses are h3 elements, but we already got the first one as title
        verses = []
        all_headings = soup.find_all('h3')
        
        for h in all_headings:
            verse_text = h.text.strip()
            if verse_text and verse_text != title:
                # Skip AI suggestions, user contributions, and other non-verse content
                if any(skip_word in verse_text for skip_word in ["مساهمة", "اقتراحات", "المزيد", "أضف معلومة", "تم اضافة"]):
                    continue
                verses.append(verse_text)

        # 4. Extract Metadata from "نبذة عن القصيدة" section
        # Find the section that contains poem info
        meter = ""
        category = ""
        rhyme = ""
        
        # Look for links in the poem info section
        # The structure is: نبذة عن القصيدة -> links for topic, type, meter, rhyme
        for a in soup.find_all('a', href=True):
            href = a['href']
            text = a.text.strip()
            
            if 'sea-' in href and 'بحر' in text:
                meter = text.replace("بحر ", "").strip()
            elif 'Poems-Topics-' in href:
                # Category/topic
                category = text.strip()
            elif href.startswith('q-') and 'قافية' in text:
                rhyme = text.replace("قافية ", "").strip()
        
        # 5. Clean up verses - pair hemistichs (Sadr and Ajuz)
        # Aldiwan often splits each verse into two h3 elements
        paired_verses = []
        for i in range(0, len(verses), 2):
            if i + 1 < len(verses):
                # Combine both hemistichs
                combined = f"{verses[i]} ... {verses[i+1]}"
                paired_verses.append(combined)
            else:
                # Single line verse
                paired_verses.append(verses[i])

        return {
            "title": title,
            "poet": poet,
            "era": era,
            "meter": meter,
            "rhyme": rhyme,
            "category": category,
            "verses": paired_verses,
            "source_url": url
        }

if __name__ == "__main__":
    # Test with a real fetch
    from diwanic.scraper.fetcher import PoemFetcher
    
    fetcher = PoemFetcher()
    parser = PoemParser()
    
    url = "https://www.aldiwan.net/poem71682.html"
    soup = fetcher.get_soup(url)
    
    if soup:
        data = parser.parse_poem(soup, url)
        logger.info("Parsed Poem Data:")
        logger.info(f"Title: {data['title']}")
        logger.info(f"Poet: {data['poet']}")
        logger.info(f"Era: {data['era']}")
        logger.info(f"Meter: {data['meter']}")
        logger.info(f"Rhyme: {data['rhyme']}")
        logger.info(f"Category: {data['category']}")
        logger.info(f"Verses count: {len(data['verses'])}")
        logger.info(f"First verse: {data['verses'][0][:80]}...")
    else:
        logger.error("Failed to fetch/parse the test poem.")
