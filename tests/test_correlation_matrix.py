"""Correlation matrix + regime-break detector — pure-math units."""
from __future__ import annotations

import importlib.util
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOOL = ROOT / "tools" / "correlation_matrix.py"


def _load():
    spec = importlib.util.spec_from_file_location("correlation_matrix", TOOL)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_pearson_perfect_correlation():
    mod = _load()
    a = [1, 2, 3, 4, 5]
    b = [2, 4, 6, 8, 10]
    assert abs(mod.pearson(a, b) - 1.0) < 1e-9


def test_pearson_perfect_anti_correlation():
    mod = _load()
    a = [1, 2, 3, 4, 5]
    b = [10, 8, 6, 4, 2]
    assert abs(mod.pearson(a, b) + 1.0) < 1e-9


def test_pearson_zero_correlation():
    mod = _load()
    a = [1, 2, 1, 2, 1]
    b = [1, 1, 1, 1, 1]
    # constant series → undefined corr → returns None
    assert mod.pearson(a, b) is None


def test_pearson_too_short():
    mod = _load()
    assert mod.pearson([1, 2], [3, 4]) is None


def test_matrix_includes_only_unique_pairs():
    mod = _load()
    rets = {
        "A": [0.01, -0.02, 0.03, -0.01, 0.02],
        "B": [-0.01, 0.02, -0.03, 0.01, -0.02],   # anti-correlated to A
        "C": [0.01, -0.02, 0.03, -0.01, 0.02],   # identical to A
    }
    m = mod.matrix(rets)
    # 3 symbols → 3 unique pairs (AB, AC, BC)
    assert len(m) == 3
    assert ("A", "B") in m
    assert ("A", "C") in m
    assert ("B", "C") in m
    # AB ≈ -1
    assert m[("A", "B")] < -0.99
    # AC ≈ +1
    assert m[("A", "C")] > 0.99
