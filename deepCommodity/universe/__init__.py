"""Universe loader — the curated map of what's tradable, organized by bucket.

Read by:
  - the agent (via `cat deepCommodity/universe/themes.yaml` in the routine prompt)
  - tools/scan_hidden_gems.py (excludes anchors / large_cap / mid_cap from gem candidates)
  - tests/test_universe.py (schema invariants)

Edit themes.yaml only via the weekly-review proposed-edits block; never auto-edited.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path

import yaml

DEFAULT_PATH = Path(__file__).resolve().parent / "themes.yaml"
_THEME_NAME_RE = re.compile(r"^[a-z][a-z0-9_]*$")


@dataclass
class Universe:
    crypto_anchors: list[str]
    crypto_large_cap: list[str]
    crypto_mid_cap: list[str]
    equity_anchors: list[str]
    equity_themes: dict[str, list[str]] = field(default_factory=dict)

    @classmethod
    def load(cls, path: str | Path | None = None) -> "Universe":
        p = Path(path) if path else DEFAULT_PATH
        data = yaml.safe_load(p.read_text())
        c = data.get("crypto", {}) or {}
        e = data.get("equity", {}) or {}
        u = cls(
            crypto_anchors=list(c.get("anchors") or []),
            crypto_large_cap=list(c.get("large_cap") or []),
            crypto_mid_cap=list(c.get("mid_cap") or []),
            equity_anchors=list(e.get("anchors") or []),
            equity_themes={k: list(v) for k, v in (e.get("themes") or {}).items()},
        )
        u._validate()
        return u

    def _validate(self) -> None:
        # 1. theme name format
        for name in self.equity_themes:
            if not _THEME_NAME_RE.match(name):
                raise ValueError(f"theme name {name!r} must match [a-z][a-z0-9_]+")
        # 2. no duplicates within crypto tiers
        for tier_name, tier in [("anchors", self.crypto_anchors),
                                ("large_cap", self.crypto_large_cap),
                                ("mid_cap", self.crypto_mid_cap)]:
            if len(set(tier)) != len(tier):
                raise ValueError(f"duplicate symbols in crypto.{tier_name}")
        # 3. crypto symbols only appear in one tier
        seen: dict[str, str] = {}
        for tier_name, tier in [("anchors", self.crypto_anchors),
                                ("large_cap", self.crypto_large_cap),
                                ("mid_cap", self.crypto_mid_cap)]:
            for s in tier:
                if s in seen:
                    raise ValueError(
                        f"crypto symbol {s} appears in both {seen[s]} and {tier_name}"
                    )
                seen[s] = tier_name
        # 4. each theme has at least 3 symbols
        for name, syms in self.equity_themes.items():
            if len(syms) < 3:
                raise ValueError(f"theme {name!r} must list >= 3 symbols, got {len(syms)}")
        # 5. anchors non-empty
        if not self.crypto_anchors:
            raise ValueError("crypto.anchors must be non-empty")
        if not self.equity_anchors:
            raise ValueError("equity.anchors must be non-empty")

    # ---- accessors ---------------------------------------------------------

    def all_crypto_symbols(self) -> set[str]:
        return set(self.crypto_anchors) | set(self.crypto_large_cap) | set(self.crypto_mid_cap)

    def all_equity_symbols(self) -> set[str]:
        out = set(self.equity_anchors)
        for syms in self.equity_themes.values():
            out.update(syms)
        return out

    def symbols_for_theme(self, name: str) -> list[str]:
        if name not in self.equity_themes:
            raise KeyError(f"unknown theme: {name!r}. Known: {sorted(self.equity_themes)}")
        return list(self.equity_themes[name])

    def theme_names(self) -> list[str]:
        return sorted(self.equity_themes.keys())
