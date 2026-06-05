"""
Arabic text cleaning and normalization for Diwanic.
Follows the principle: strip diacritics, keep letter variants (أ إ آ ة).
"""
import re

class ArabicCleaner:
    def __init__(self):
        # A more aggressive range for all Arabic diacritics and marks
        # This covers tashkeel, shadda, maddah, and other marks
        # Range: 064B to 065F
        self.tashkeel_pattern = re.compile(r'[\u064B-\u065F]')
        # Tatweel (Kashida)
        self.tatweel_pattern = re.compile(r'\u0640')
        # Punctuation (including Arabic and some Quranic ones)
        self.punctuation_pattern = re.compile(r'[،؛؟«»]')

    def remove_tashkeel(self, text: str) -> str:
        """Remove all Arabic diacritics."""
        if not text: return ""
        return self.tashkeel_pattern.sub('', text)

    def remove_tatweel(self, text: str) -> str:
        """Remove kashida (stretched letters)."""
        if not text: return ""
        return self.tatweel_pattern.sub('', text)

    def remove_punctuation(self, text: str) -> str:
        """Remove common Arabic punctuations."""
        if not text: return ""
        return self.punctuation_pattern.sub('', text)

    def clean_for_search(self, text: str) -> str:
        """
        Creates a version for the search engine:
        - Removes diacritics
        - Removes kashida
        - Removes common Arabic punctuation
        - Normalizes multiple spaces
        - Preserves Alef variants and Ta Marbuta
        """
        if not text: return ""
        
        text = self.remove_tashkeel(text)
        text = self.remove_tatweel(text)
        text = self.remove_punctuation(text)
        
        # Remove any other non-word symbols except space and Arabic characters
        # This helps strip hidden markers
        text = re.sub(r'[^\u0621-\u064A\s]', '', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        
        return text

    def clean_verses(self, verses: list) -> list:
        """Clean a list of verses."""
        return [self.clean_for_search(v) for v in verses]
