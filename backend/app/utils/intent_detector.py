import re

ACK_PATTERNS = [
    r"^thanks?$",
    r"^thank you$",
    r"^thx$",
    r"^ok$",
    r"^okay$",
    r"^fine$",
    r"^got it$",
    r"^cool$",
    r"^great$",
    r"^very good$",
    r"^nice$",
]

def is_acknowledgement(text: str) -> bool:
    text = text.strip().lower()
    return any(re.match(p, text) for p in ACK_PATTERNS)
