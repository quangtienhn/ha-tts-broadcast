"""Constants for the TTS Broadcast integration."""

from __future__ import annotations

DOMAIN = "tts_broadcast"
PLATFORMS = ["switch", "number", "text", "button"]

CONF_TTS_ENTITY = "tts_entity"
CONF_SPEAKERS = "speakers"
CONF_NO_VOLUME_SPEAKERS = "no_volume_speakers"
CONF_VOLUME = "volume"
CONF_LANGUAGE = "language"
CONF_OPTIONS = "options"

DEFAULT_VOLUME = 50
DEFAULT_TITLE = "TTS Broadcast"
VERSION = "1.0.0"

SERVICE_SPEAK = "speak"
SERVICE_STOP = "stop"
SERVICE_GET_DASHBOARD_CARD = "get_dashboard_card"

ATTR_MESSAGE = "message"
ATTR_SPEAKERS = "speakers"
ATTR_VOLUME = "volume"
ATTR_LANGUAGE = "language"
ATTR_OPTIONS = "options"
ATTR_PLAYED = "played"
ATTR_SKIPPED = "skipped"
ATTR_FAILED = "failed"
