"""Tests for translation key parity."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRANS = ROOT / "custom_components" / "tts_broadcast" / "translations"


def _keys(obj, prefix=""):
    out = set()
    if isinstance(obj, dict):
        for k, v in obj.items():
            out |= _keys(v, f"{prefix}.{k}" if prefix else k)
    return out


def test_translation_key_parity() -> None:
    en = json.loads((TRANS / "en.json").read_text(encoding="utf-8"))
    vi = json.loads((TRANS / "vi.json").read_text(encoding="utf-8"))
    assert _keys(en) == _keys(vi), _keys(en).symmetric_difference(_keys(vi))
