"""Sanitize fetched web text before the agent reads it.

This is defense-in-depth, NOT the security boundary — the real boundary is that the
deterministic gates (preflight/check_limits) and the agent's narrow tool allowlist mean
injected text can bias intent but cannot bypass a cap. Here we (1) normalize away common
obfuscation (NFKC, zero-width/control strip, HTML strip) so the blocklist isn't trivially
evaded, (2) redact imperative injection phrasing, and (3) offer wrap_untrusted() to delimit
fetched text as data when building a prompt.
"""
from __future__ import annotations

import re
import unicodedata

# Imperative phrasing common in prompt-injection attempts within fetched text.
INJECTION_PATTERNS = [
    r"ignore (?:all |any |the )?(?:previous|prior|above|earlier) (?:instructions|prompts|context|directives|guidance)?",
    r"disregard (?:all |any |the )?(?:above|previous|prior|earlier|restrictions|risk)",
    r"set aside (?:the )?(?:earlier|previous|prior) (?:guidance|instructions)",
    r"system prompt",
    r"you are now",
    r"new instructions:",
    r"override (?:the )?(?:risk|gate|limit)",
    r"execute (?:trade|order|the following)",
    r"buy now",
    r"sell now",
    r"(?:place|submit|execute) (?:an? )?(?:market |limit )?order",
    r"(?:take|open) (?:a |the )?(?:maximum|max|full) (?:allowed )?position",
    r"<\s*system\s*>",
    r"\[\[.*?\]\]",
]

_COMPILED = [re.compile(p, re.IGNORECASE) for p in INJECTION_PATTERNS]
_ZERO_WIDTH = dict.fromkeys(
    [0x200B, 0x200C, 0x200D, 0x2060, 0xFEFF, 0x00AD], None
)
_TAG_RE = re.compile(r"<[^>]+>")


def _strip_controls(text: str) -> str:
    # drop C0/C1 control chars except tab/newline/carriage-return
    return "".join(
        ch for ch in text
        if ch in "\t\n\r" or unicodedata.category(ch) != "Cc"
    )


def sanitize_news(text: str) -> str:
    """Normalize obfuscation, strip HTML, and redact injection imperatives."""
    if not text:
        return text
    out = unicodedata.normalize("NFKC", text)
    out = out.translate(_ZERO_WIDTH)
    out = _strip_controls(out)
    out = _TAG_RE.sub(" ", out)
    for pat in _COMPILED:
        out = pat.sub("[REDACTED]", out)
    # collapse the whitespace our tag/zero-width removal may have introduced,
    # but only when we actually changed the text (keep clean input byte-identical)
    if out != text:
        out = re.sub(r"[ \t]{2,}", " ", out).strip()
    return out


_LABEL_RE = re.compile(r"[^a-z0-9_-]")


def wrap_untrusted(label: str, text: str) -> str:
    """Delimit fetched text as DATA (never instructions) for prompt construction.

    The label is sanitized to [a-z0-9_-] so a caller can't pass a fetched field that
    injects attributes and breaks out of the data envelope.
    """
    safe_label = _LABEL_RE.sub("", (label or "data").lower()) or "data"
    safe = sanitize_news(text or "")
    return (
        f"<UNTRUSTED_DATA source=\"{safe_label}\">\n"
        f"{safe}\n"
        f"</UNTRUSTED_DATA>"
    )
