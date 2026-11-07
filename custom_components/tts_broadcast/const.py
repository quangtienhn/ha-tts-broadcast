"""Constants for the TTS Broadcast integration."""

from __future__ import annotations

DOMAIN = "tts_broadcast"
PLATFORMS = ["switch", "number", "text", "button", "conversation"]

CONF_TTS_ENTITY = "tts_entity"
CONF_SPEAKERS = "speakers"
CONF_NO_VOLUME_SPEAKERS = "no_volume_speakers"
CONF_VOLUME = "volume"
CONF_LANGUAGE = "language"
CONF_OPTIONS = "options"

DEFAULT_VOLUME = 50
DEFAULT_TITLE = "TTS Broadcast"
VERSION = "1.1.3"

CONF_STRIP_PHRASES = "strip_phrases"
CONF_KEEP_PHRASES = "keep_phrases"
CONF_REQUIRE_PHRASE = "require_phrase"
CONF_FALLBACK_AGENT = "fallback_agent"
CONF_ACCENT_INSENSITIVE = "accent_insensitive"
CONF_REPLY_TEXT = "reply_text"

DEFAULT_STRIP_PHRASES = ["thông báo"]
DEFAULT_KEEP_PHRASES: list[str] = []

SERVICE_SPEAK = "speak"
SERVICE_STOP = "stop"
SERVICE_GET_DASHBOARD_CARD = "get_dashboard_card"
SERVICE_DEBUG_SELECTION = "debug_selection"

ATTR_MESSAGE = "message"
ATTR_SPEAKERS = "speakers"
ATTR_VOLUME = "volume"
ATTR_LANGUAGE = "language"
ATTR_OPTIONS = "options"
ATTR_PLAYED = "played"
ATTR_SKIPPED = "skipped"
ATTR_FAILED = "failed"
ATTR_TARGETED = "targeted"
ATTR_UNEXPECTED_STARTED = "unexpected_started"
