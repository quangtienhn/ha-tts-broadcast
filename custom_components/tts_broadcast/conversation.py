"""Conversation platform for TTS Broadcast."""

from __future__ import annotations

from typing import Any

from homeassistant.components.conversation import ConversationEntity
from homeassistant.components.conversation.agent_manager import async_converse
from homeassistant.core import HomeAssistant
from homeassistant.helpers import intent
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TTSBroadcastConfigEntry
from .const import DOMAIN
from .phrase_matching import match_phrase


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TTSBroadcastConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    async_add_entities([TTSBroadcastConversationEntity(hass, entry)])


class TTSBroadcastConversationEntity(ConversationEntity):
    _attr_has_entity_name = True
    _attr_name = "TTS Broadcast"

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

    async def async_process(self, user_input) -> Any:
        from homeassistant.components.conversation.models import ConversationResult

        config = {**self._entry.data, **self._entry.options}
        strip_phrases = config.get("strip_phrases", [])
        keep_phrases = config.get("keep_phrases", [])
        require_phrase = config.get("require_phrase", True)
        accent = config.get("accent_insensitive", True)
        reply_text = config.get("reply_text", "")
        fallback = config.get("fallback_agent")

        match = match_phrase(
            user_input.text,
            strip_phrases,
            keep_phrases,
            accent,
            require_phrase,
        )

        if match.action == "reply":
            response = intent.IntentResponse(user_input.language)
            response.async_set_speech(match.reply or reply_text or "Sent")
            return ConversationResult(
                response=response, conversation_id=user_input.conversation_id
            )

        if match.action == "delegate":
            if fallback:
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
                except Exception:  # noqa: BLE001
                    pass
            response = intent.IntentResponse(user_input.language)
            response.async_set_speech(reply_text or "No phrase matched")
            return ConversationResult(
                response=response, conversation_id=user_input.conversation_id
            )

        # speak
        # check selected speakers
        from . import _resolve_speakers

        resolved, _ = await _resolve_speakers(self.hass, self._entry, None)
        if not resolved:
            response = intent.IntentResponse(user_input.language)
            response.async_set_speech(reply_text or "No speaker selected")
            return ConversationResult(
                response=response, conversation_id=user_input.conversation_id
            )

        from . import async_announce

        # background task for fast pipeline response
        async def _run() -> None:
            await async_announce(self.hass, self._entry, match.message)

        self._entry.async_create_background_task(
            self.hass, _run(), "tts_broadcast_announce"
        )

        response = intent.IntentResponse(user_input.language)
        response.async_set_speech(reply_text or "Sent")
        return ConversationResult(
            response=response, conversation_id=user_input.conversation_id
        )
