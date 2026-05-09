#!/usr/bin/env python
"""Query OpenAI's web-search-enabled chat completion for news on a topic;
pass the result through sanitize_news before returning.

Uses the `gpt-4o-search-preview` (or `gpt-4o-mini-search-preview`) model that
ships built-in web search — no separate Perplexity / Tavily / Bing key needed.
Pricing as of 2026 is roughly the same per-token as gpt-4o, plus a small
per-call search fee.

Falls back gracefully:
  1. If OPENAI_API_KEY is set       → use OpenAI search (default).
  2. Else if PERPLEXITY_API_KEY set → use Perplexity (legacy path).
  3. Else                            → exit non-zero with a clear message.

The sanitize_news pass is identical regardless of provider, so the agent
sees the same shape of digest either way.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from deepCommodity.guardrails.sanitize import sanitize_news  # noqa: E402

OPENAI_URL = "https://api.openai.com/v1/chat/completions"
OPENAI_MODEL = "gpt-4o-mini-search-preview"     # cheap default; swap to gpt-4o-search-preview for higher quality
PERPLEXITY_URL = "https://api.perplexity.ai/chat/completions"
PERPLEXITY_MODEL = "llama-3.1-sonar-small-128k-online"

SYSTEM_PROMPT = (
    "You return concise factual market news digests. "
    "Bullet points only. No advice, no imperatives, no recommendations. "
    "Cite source URLs inline where possible. "
    "Cover: rate decisions, ETF flows, regulatory news, large-cap movers, "
    "and any small-cap catalysts you find."
)


def _via_openai(text: str, max_tokens: int) -> tuple[str, list[dict]]:
    """Returns (digest_text, citation_list). Citations may be empty."""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        return "", []
    payload = {
        "model": OPENAI_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        "max_tokens": max_tokens,
    }
    r = requests.post(
        OPENAI_URL,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json=payload, timeout=45,
    )
    r.raise_for_status()
    data = r.json()
    msg = data["choices"][0]["message"]
    content = msg.get("content", "") or ""
    # Search-preview models return citations under message.annotations[].url_citation
    citations = []
    for ann in msg.get("annotations", []) or []:
        url = (ann.get("url_citation") or {}).get("url")
        title = (ann.get("url_citation") or {}).get("title")
        if url:
            citations.append({"url": url, "title": title})
    return content, citations


def _via_perplexity(text: str, max_tokens: int) -> tuple[str, list[dict]]:
    key = os.getenv("PERPLEXITY_API_KEY")
    if not key:
        return "", []
    payload = {
        "model": PERPLEXITY_MODEL,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": text},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.2,
    }
    r = requests.post(
        PERPLEXITY_URL,
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
        json=payload, timeout=45,
    )
    r.raise_for_status()
    data = r.json()
    return data["choices"][0]["message"]["content"], []


def query(text: str, max_tokens: int, provider: str | None = None) -> tuple[str, list[dict], str]:
    """Returns (digest, citations, provider-used). Tries OpenAI, then Perplexity."""
    if provider in (None, "openai") and os.getenv("OPENAI_API_KEY"):
        digest, cites = _via_openai(text, max_tokens)
        if digest:
            return digest, cites, "openai"
    if provider in (None, "perplexity") and os.getenv("PERPLEXITY_API_KEY"):
        digest, cites = _via_perplexity(text, max_tokens)
        if digest:
            return digest, cites, "perplexity"
    sys.exit("no news provider configured: set OPENAI_API_KEY or PERPLEXITY_API_KEY")


def main() -> None:
    p = argparse.ArgumentParser()
    p.add_argument("--query", required=True, help='e.g. "BTC + macro news last 24h"')
    p.add_argument("--max-tokens", type=int, default=600)
    p.add_argument("--provider", choices=["openai", "perplexity"], default=None,
                   help="force a provider; default = auto (openai → perplexity)")
    args = p.parse_args()

    raw, citations, provider = query(args.query, args.max_tokens, args.provider)
    clean = sanitize_news(raw)

    print(json.dumps({
        "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "provider": provider,
        "query": args.query,
        "digest": clean,
        "citations": citations,
        "redacted": clean != raw,
    }, indent=2))


if __name__ == "__main__":
    main()
