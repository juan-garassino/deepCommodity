import re

# Imperative phrasing common in prompt-injection attempts within news content.
INJECTION_PATTERNS = [
    r"ignore (?:all |any |the )?previous (?:instructions|prompts|context)",
    r"disregard (?:all |any |the )?(?:above|previous|prior)",
    r"system prompt",
    r"you are now",
    r"new instructions:",
    r"execute (?:trade|order|the following)",
    r"buy now",
    r"sell now",
    r"(?:place|submit) (?:an? )?(?:market |limit )?order",
    r"<\s*system\s*>",
    r"\[\[.*\]\]",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]


def sanitize_news(text: str) -> str:
    """Replace prompt-injection-style imperatives with [REDACTED] before the agent reads news."""
    if not text:
        return text
    out = text
    for pat in _COMPILED:
        out = pat.sub("[REDACTED]", out)
    return out
