"""Tests for phrase matching."""

from __future__ import annotations

import unicodedata

from custom_components.tts_broadcast.phrase_matching import match_phrase


def test_strip() -> None:
    r = match_phrase("Thông báo cơm chín rồi", ["thông báo"], [], True, True)
    assert r.action == "speak"
    assert r.message == "cơm chín rồi"


def test_strip_punctuation_connectors() -> None:
    r = match_phrase("thông báo, rằng cơm chín", ["thông báo"], [], True, True)
    assert r.message == "cơm chín"


def test_strip_accent_insensitive_no_accent() -> None:
    r = match_phrase("thong bao com chin roi", ["thông báo"], [], True, True)
    assert r.action == "speak"
    assert r.message == "com chin roi"


def test_keep() -> None:
    r = match_phrase("xin chào mọi người", [], ["xin chào"], True, True)
    assert r.message == "xin chào mọi người"


def test_keep_full_sentence() -> None:
    r = match_phrase("xin chào mọi người xuống ăn cơm", [], ["xin chào"], True, True)
    assert r.action == "speak"
    assert r.message == "xin chào mọi người xuống ăn cơm"


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


def test_unmatched_sentence_delegates() -> None:
    r = match_phrase("mọi người ơi xuống ăn cơm", ["thông báo"], [], True, True)
    assert r.action == "delegate"


def test_nfd_strip() -> None:
    nfd = unicodedata.normalize("NFD", "thông báo")
    r = match_phrase(nfd, ["thông báo"], [], True, True)
    assert r.action == "reply"
    assert not r.message


def test_no_accent_no_match() -> None:
    r = match_phrase("thong bao x", ["thông báo"], [], False, True)
    assert r.action == "delegate"
