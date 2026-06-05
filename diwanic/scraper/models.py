"""
Data models and schema validation for scraped poems.
"""
from dataclasses import dataclass, asdict
from typing import List, Optional
from datetime import datetime


@dataclass
class Poem:
    """
    Schema for a single poem.
    All fields are validated before saving.
    """
    # Required fields
    poem_id: str              # Unique ID (e.g., "aldiwan_71682")
    title: str
    poet: str
    verses: List[str]
    source_url: str
    website: str              # e.g., "aldiwan"
    scraped_at: str           # ISO timestamp
    
    # Optional metadata
    era: Optional[str] = None
    meter: Optional[str] = None
    rhyme: Optional[str] = None
    category: Optional[str] = None
    
    # Text variants
    original_text: Optional[str] = None      # Full text with diacritics
    searchable_text: Optional[str] = None    # Full text without diacritics
    
    def to_dict(self):
        """Convert to dictionary for JSON serialization."""
        return asdict(self)
    
    @classmethod
    def from_raw_data(cls, raw_data: dict, poem_id: str, website: str = "aldiwan"):
        """
        Create a Poem from raw scraper output.
        Adds required fields like poem_id, website, timestamp.
        """
        return cls(
            poem_id=poem_id,
            title=raw_data.get("title", ""),
            poet=raw_data.get("poet", ""),
            verses=raw_data.get("verses", []),
            source_url=raw_data.get("source_url", ""),
            website=website,
            scraped_at=datetime.utcnow().isoformat(),
            era=raw_data.get("era"),
            meter=raw_data.get("meter"),
            rhyme=raw_data.get("rhyme"),
            category=raw_data.get("category"),
            original_text=None,  # Will be populated in preprocessing
            searchable_text=None,
        )
    
    def validate(self) -> bool:
        """
        Validate required fields.
        Returns True if valid, False otherwise.
        """
        if not self.poem_id:
            return False
        if not self.title or len(self.title.strip()) == 0:
            return False
        if not self.poet or len(self.poet.strip()) == 0:
            return False
        if not self.verses or len(self.verses) == 0:
            return False
        if not self.source_url:
            return False
        return True
