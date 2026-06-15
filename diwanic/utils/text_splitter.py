def split_text(text: str, max_length: int = 500) -> list[str]:
    """
    Simple text splitter that splits by sentences (naive) and then chunks.
    For Arabic, we might want to split by punctuation like .،؛؟ and spaces.
    This is a placeholder; replace with a more sophisticated splitter if needed.
    """
    if not text:
        return []
    
    # Naive split by common sentence endings in Arabic and English
    import re
    # Split by .،؛؟ and then by newline
    sentences = re.split(r'[.،؛؟\n]', text)
    # Remove empty strings and strip
    sentences = [s.strip() for s in sentences if s.strip()]
    
    chunks = []
    current_chunk = ""
    for sentence in sentences:
        if len(current_chunk) + len(sentence) + 1 <= max_length:
            if current_chunk:
                current_chunk += " " + sentence
            else:
                current_chunk = sentence
        else:
            if current_chunk:
                chunks.append(current_chunk)
            current_chunk = sentence
    if current_chunk:
        chunks.append(current_chunk)
    
    return chunks
