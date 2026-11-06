"""Tests for phrase matching."""

from __future__ import annotations

from custom_components.tts_broadcast.phrase_matching import match_phrase


def test_strip() -> None:
    r = match_phrase("Thông báo cơm chín rồi", ["thông báo"], [], True, True)
    assert r.action == "speak"
    assert r.message == "cơm chín rồi"


def test_strip_punctuation_connectors() -> None:
    r = match_phrase("thông báo, rằng cơm chín", ["thông báo"], [], True, True)
    assert r.message == "cơm chín"


def test_keep() -> None:
    r = match_phrase("xin chào mọi người", [], ["xin chào"], True, True)
    assert r.message == "xin chào mọi người"


def test_longest() -> None:
    r = match_phrase(
        "thông báo rằng x", ["thông báo", "thông báo rằng"], [], True, True
    )
    assert r.message == "x"


def test_accent_insensitive() -> None:
    r = match_phrase("THONG BAO hi", ["thông báo"], [], True, True)
    assert r.message == "hi"


def test_phrase_only() -> None:
    r = match_phrase("thông báo", ["thông báo"], [], True, True)
    assert r.action == "reply"
    assert r.reply == "missing_content"


def test_no_match_require() -> None:
    r = match_phrase("hello", ["thông báo"], [], True, True)
    assert r.action == "delegate"


def test_no_match_not_require() -> None:
    r = match_phrase("hello", ["thông báo"], [], True, False)
    assert r.action == "speak"
    assert r.message == "hello"


def test_phrase_in_both_rejected_in_flow() -> None:
    # validated in config flow; matching just uses first list order
    r = match_phrase("thông báo hi", ["thông báo"], ["thông báo"], True, True)
    assert r.message == "hi"
