import re

def extract_mention(text: str) -> str:
    match = re.search(r'@(\d+)', text)
    if match:
        return match.group(1)
    return None
