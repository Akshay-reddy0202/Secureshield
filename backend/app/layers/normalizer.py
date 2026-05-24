import unicodedata
import re

def normalize_text(text: str) -> str:
    # 1. Unicode normalization (handles hidden characters)
    text = unicodedata.normalize("NFKC", text)
    
    # 2. Lowercase
    text = text.lower()
    
    # 3. Strip special symbols used for bypass (like "h-a-c-k" -> "hack")
    # This regex removes anything that isn't a letter, number, or space
    text = re.sub(r'[^a-z0-9\s]', '', text)
    
    return text