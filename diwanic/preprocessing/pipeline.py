"""
Preprocessing pipeline logic for cleaning poems.
"""
import json
from pathlib import Path
from diwanic.preprocessing.cleaner import ArabicCleaner
from diwanic.utils.logger_util import get_logger

logger = get_logger(__name__)

def process_poems(input_path: str, output_path: str):
    """
    Read raw poems, clean the text, and save to processed JSONL.
    """
    cleaner = ArabicCleaner()
    
    input_file = Path(input_path)
    output_file = Path(output_path)
    
    if not input_file.exists():
        logger.error(f"Input file not found: {input_path}")
        return
        
    output_file.parent.mkdir(parents=True, exist_ok=True)
    
    processed_count = 0
    with open(input_file, 'r', encoding='utf-8') as f_in, \
         open(output_file, 'w', encoding='utf-8') as f_out:
         
        for line in f_in:
            if not line.strip():
                continue
                
            poem = json.loads(line)
            
            # 1. Store original text (with diacritics) for display
            poem['original_text'] = '\n'.join(poem.get('verses', []))
            
            # 2. Store cleaned text (without diacritics) for search
            cleaned_verses = cleaner.clean_verses(poem.get('verses', []))
            # Fallback if cleaning removed everything
            if not cleaned_verses:
                cleaned_verses = poem.get('verses', [])
            poem['searchable_text'] = '\n'.join(cleaned_verses)
            
            # 3. Add clean versions of metadata for exact matching
            poem['title_searchable'] = cleaner.clean_for_search(poem.get('title', ''))
            poem['poet_searchable'] = cleaner.clean_for_search(poem.get('poet', ''))
            
            f_out.write(json.dumps(poem, ensure_ascii=False) + '\n')
            processed_count += 1
            
    logger.info(f"✅ Processed {processed_count} poems.")
    logger.info(f"💾 Saved to: {output_path}")
    return processed_count