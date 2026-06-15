import re

def normalize_arabic(text: str) -> str:
    """
    Authoritative Arabic text normalization utility.
    Used for both ingestion (searchable_text generation) and query preprocessing.
    
    Rules:
    - Remove diacritics (harakat).
    - Normalize alef variants (أ, إ, آ -> ا).
    - Normalize hamza variants (ؤ, ئ -> ء).
    - Normalize taa marbuta (ة -> ه).
    - Normalize yaa (ى -> ي).
    - Remove punctuation and multiple spaces.
    """
    if not text:
        return ""
    
    # Strip diacritics
    text = re.sub(r"[\u064B-\u0652]", "", text)
    
    # Normalize Alef
    text = re.sub(r"[أإآ]", "ا", text)
    
    # Normalize Yaa/Alef Maqsura
    text = text.replace("ى", "ي")
    
    # Normalize Taa Marbuta
    text = text.replace("ة", "ه")
    
    # Normalize Hamza
    text = text.replace("ؤ", "ء").replace("ئ", "ء")
    
    # Remove punctuation
    text = re.sub(r"[^\w\s]", " ", text)
    
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text).strip()
    
    return text
