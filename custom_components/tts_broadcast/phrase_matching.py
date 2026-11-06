"""Phrase matching for voice announcements."""

from __future__ import annotations

import unicodedata
from dataclasses import dataclass
from typing import Literal

CONNECTORS = {"rằng", "là"}


def _strip_diacritics(text: str) -> str:
    normalized = unicodedata.normalize("NFD", text)
    result = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return result.replace("đ", "d").replace("Đ", "D")


def normalize_token(token: str, accent_insensitive: bool) -> str:
    token = unicodedata.normalize("NFC", token).lower().strip()
    # strip surrounding punctuation
    token = token.strip(".,!?;:\"'()[]{}")
    if accent_insensitive:
        token = _strip_diacritics(token)
    return token


def tokenize(text: str, accent_insensitive: bool) -> list[str]:
    return [normalize_token(t, accent_insensitive) for t in text.split() if t.strip()]


def _tokenize_original(text: str) -> list[str]:
    return text.split()


@dataclass
class MatchResult:
    action: Literal["speak", "reply", "delegate"]
    message: str = ""
    reply: str = ""


def match_phrase(
    text: str,
    strip_phrases: list[str],
    keep_phrases: list[str],
    accent_insensitive: bool,
    require_phrase: bool,
) -> MatchResult:
    original_tokens = _tokenize_original(text)
    norm_tokens = tokenize(text, accent_insensitive)

    # Build phrase token lists (normalized) preserving order.
    candidates: list[tuple[list[str], str, bool]] = []
    for phrase in strip_phrases:
        pt = tokenize(phrase, accent_insensitive)
        if pt:
            candidates.append((pt, phrase, True))
    for phrase in keep_phrases:
        pt = tokenize(phrase, accent_insensitive)
        if pt:
            candidates.append((pt, phrase, False))

    # Longest first.
    candidates.sort(key=lambda item: len(item[0]), reverse=True)

    for phrase_tokens, _phrase, is_strip in candidates:
        if (
            len(phrase_tokens) <= len(norm_tokens)
            and norm_tokens[: len(phrase_tokens)] == phrase_tokens
        ):
            if is_strip:
                # strip leading connectors (compare normalized original tokens)
                # Work with original tokens sliced by count.
                remaining_original = original_tokens[len(phrase_tokens) :]
                # remove leading connectors based on normalized comparison
                connectors = {
                    normalize_token(c, accent_insensitive) for c in CONNECTORS
                }
                idx = 0
                while idx < len(remaining_original):
                    if (
                        normalize_token(remaining_original[idx], accent_insensitive)
                        in connectors
                    ):
                        idx += 1
                        continue
                    # also skip empty/punctuation-only
                    if (
                        normalize_token(remaining_original[idx], accent_insensitive)
                        == ""
                    ):
                        idx += 1
                        continue
                    break
                spoken_tokens = remaining_original[idx:]
                spoken = " ".join(spoken_tokens).strip()
                if not spoken:
                    return MatchResult(action="reply", reply="missing_content")
                return MatchResult(action="speak", message=spoken)
            # keep
            return MatchResult(action="speak", message=text.strip())

    if require_phrase:
        return MatchResult(action="delegate", message=text.strip())
    return MatchResult(action="speak", message=text.strip())
