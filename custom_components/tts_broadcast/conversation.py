"""Conversation platform for TTS Broadcast."""

from __future__ import annotations

import logging

from homeassistant.components.conversation import (
    ConversationEntity,
    ConversationInput,
    ConversationResult,
    async_converse,
)
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import (
    TTSBroadcastConfigEntry,
    _own_conversation_entity_id,
    _resolve_speakers,
    async_announce,
)
from .const import DOMAIN
from .phrase_matching import match_phrase

_LOGGER = logging.getLogger(__name__)

_REPLIES = {
    "en": {
        "sent": "Sent",
        "missing_content": "Please provide the content to announce.",
        "no_speaker": "No speaker is selected.",
        "not_an_announcement": "Not an announcement.",
        "fallback_error": "Fallback agent failed.",
        "no_fallback": "No matching phrase.",
    },
    "vi": {
        "sent": "Đã gửi",
        "missing_content": "Vui lòng cung cấp nội dung cần thông báo.",
        "no_speaker": "Chưa chọn loa nào.",
        "not_an_announcement": "Không phải thông báo.",
        "fallback_error": "Agent dự phòng lỗi.",
        "no_fallback": "Không khớp cụm từ nào.",
    },
}


def _reply(lang: str, key: str, reply_text: str = "") -> str:
    table = _REPLIES.get(lang.split("-")[0], _REPLIES["en"])
    if key == "sent" and reply_text:
        return reply_text
    return table.get(key, table["sent"])


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TTSBroadcastConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([TTSBroadcastConversationEntity(hass, entry)])


class TTSBroadcastConversationEntity(ConversationEntity):
    _attr_has_entity_name = True
    _attr_name = "TTS Broadcast"
    _attr_translation_key = "tts_broadcast"

    def __init__(self, hass: HomeAssistant, entry: TTSBroadcastConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_conversation"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="TTS Broadcast",
        )

    @property
    def supported_languages(self) -> str:
        return "*"

    async def async_process(self, user_input: ConversationInput) -> ConversationResult:
        config = {**self._entry.data, **self._entry.options}
        strip_phrases = config.get("strip_phrases", [])
        keep_phrases = config.get("keep_phrases", [])
        require_phrase = config.get("require_phrase", True)
        accent = config.get("accent_insensitive", True)
        reply_text = config.get("reply_text", "")
        fallback = config.get("fallback_agent")
        lang = user_input.language or "en"

        match = match_phrase(
            user_input.text,
            strip_phrases,
            keep_phrases,
            accent,
            require_phrase,
        )

        if match.action == "reply":
            response = intent.IntentResponse(user_input.language)
            response.async_set_speech(
                _reply(lang, match.reply or "missing_content", "")
            )
            return ConversationResult(
                response=response, conversation_id=user_input.conversation_id
            )

        if match.action == "delegate":
            own = _own_conversation_entity_id(self.hass, self._entry)
            if fallback and (own is None or fallback != own):
                try:
                    result = await async_converse(
                        self.hass,
                        user_input.text,
                        user_input.conversation_id,
                        user_input.context,
                        language=user_input.language,
                        agent_id=fallback,
                        device_id=user_input.device_id,
                        satellite_id=user_input.satellite_id,
                    )
                    return result
                except Exception as err:  # noqa: BLE001
                    _LOGGER.warning("Fallback agent failed: %s", err)
                    response = intent.IntentResponse(user_input.language)
                    response.async_set_speech(_reply(lang, "fallback_error", ""))
                    return ConversationResult(
                        response=response, conversation_id=user_input.conversation_id
                    )
            response = intent.IntentResponse(user_input.language)
            response.async_set_speech(_reply(lang, "no_fallback", ""))
            return ConversationResult(
                response=response, conversation_id=user_input.conversation_id
            )

        resolved, _ = await _resolve_speakers(self.hass, self._entry, None)
        if not resolved:
            response = intent.IntentResponse(user_input.language)
            response.async_set_speech(_reply(lang, "no_speaker", ""))
            return ConversationResult(
                response=response, conversation_id=user_input.conversation_id
            )

        async def _run() -> None:
            try:
                await async_announce(self.hass, self._entry, match.message)
            except Exception as err:  # noqa: BLE001
                _LOGGER.warning("Announcement failed: %s", err)

        self._entry.async_create_background_task(
            self.hass, _run(), "tts_broadcast_announce"
        )

        response = intent.IntentResponse(user_input.language)
        response.async_set_speech(_reply(lang, "sent", reply_text))
        return ConversationResult(
            response=response, conversation_id=user_input.conversation_id
        )
