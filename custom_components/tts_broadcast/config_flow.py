"""Config flow for TTS Broadcast."""

from __future__ import annotations

from typing import Any

import probatio
from homeassistant.config_entries import ConfigFlow, OptionsFlowWithReload
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector

from . import _own_conversation_entity_id
from .const import (
    CONF_ACCENT_INSENSITIVE,
    CONF_FALLBACK_AGENT,
    CONF_KEEP_PHRASES,
    CONF_LANGUAGE,
    CONF_NO_VOLUME_SPEAKERS,
    CONF_OPTIONS,
    CONF_REPLY_TEXT,
    CONF_REQUIRE_PHRASE,
    CONF_SPEAKERS,
    CONF_STRIP_PHRASES,
    CONF_TTS_ENTITY,
    CONF_VOLUME,
    DEFAULT_KEEP_PHRASES,
    DEFAULT_STRIP_PHRASES,
    DEFAULT_VOLUME,
    DOMAIN,
)
from .phrase_matching import normalize_token

SPEAKERS_SCHEMA = probatio.Schema(
    {
        probatio.Required(CONF_TTS_ENTITY): selector.EntitySelector({"domain": "tts"}),
        probatio.Required(CONF_SPEAKERS): selector.EntitySelector(
            {"domain": "media_player", "multiple": True}
        ),
        probatio.Optional(CONF_NO_VOLUME_SPEAKERS, default=[]): selector.EntitySelector(
            {"domain": "media_player", "multiple": True}
        ),
        probatio.Optional(CONF_VOLUME, default=DEFAULT_VOLUME): selector.NumberSelector(
            {"min": 0, "max": 100, "step": 1, "mode": "slider"}
        ),
        probatio.Optional(CONF_LANGUAGE, default=""): selector.TextSelector(),
        probatio.Optional(CONF_OPTIONS, default={}): selector.ObjectSelector(),
    }
)

VOICE_SCHEMA = probatio.Schema(
    {
        probatio.Optional(
            CONF_STRIP_PHRASES, default=DEFAULT_STRIP_PHRASES
        ): selector.TextSelector({"multiple": True}),
        probatio.Optional(
            CONF_KEEP_PHRASES, default=DEFAULT_KEEP_PHRASES
        ): selector.TextSelector({"multiple": True}),
        probatio.Optional(
            CONF_REQUIRE_PHRASE, default=True
        ): selector.BooleanSelector(),
        probatio.Optional(CONF_FALLBACK_AGENT): selector.ConversationAgentSelector(),
        probatio.Optional(
            CONF_ACCENT_INSENSITIVE, default=True
        ): selector.BooleanSelector(),
        probatio.Optional(CONF_REPLY_TEXT, default=""): selector.TextSelector(),
    }
)


def _normalize_phrases(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        value = [value]
    result: list[str] = []
    seen: set[str] = set()
    for item in value:
        text = str(item).strip()
        if not text:
            continue
        if text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _norm_phrase_set(
    phrases: list[str], accent_insensitive: bool
) -> set[tuple[str, ...]]:
    """Return normalized token tuples for a list of phrases."""
    result: set[tuple[str, ...]] = set()
    for phrase in phrases:
        tokens = [
            token
            for token in (
                normalize_token(tok, accent_insensitive) for tok in str(phrase).split()
            )
            if token
        ]
        if tokens:
            result.add(tuple(tokens))
    return result


def _validate_speakers_section(
    user_input: dict, stored: dict | None = None
) -> dict[str, str]:
    """Validate only the speakers & TTS fields of a flow step."""
    errors: dict[str, str] = {}
    current = stored or {}
    speakers = user_input.get(CONF_SPEAKERS) or current.get(CONF_SPEAKERS) or []
    if not speakers:
        errors[CONF_SPEAKERS] = "no_speakers"
    no_volume = (
        user_input.get(CONF_NO_VOLUME_SPEAKERS)
        or current.get(CONF_NO_VOLUME_SPEAKERS)
        or []
    )
    if any(item not in speakers for item in no_volume):
        errors[CONF_NO_VOLUME_SPEAKERS] = "invalid_subset"
    return errors


def _validate_voice_section(
    user_input: dict, stored: dict | None = None
) -> dict[str, str]:
    """Validate only the voice phrase fields of a flow step."""
    errors: dict[str, str] = {}
    current = stored or {}
    strip = _normalize_phrases(
        user_input.get(CONF_STRIP_PHRASES) or current.get(CONF_STRIP_PHRASES) or []
    )
    keep = _normalize_phrases(
        user_input.get(CONF_KEEP_PHRASES) or current.get(CONF_KEEP_PHRASES) or []
    )
    accent = user_input.get(CONF_ACCENT_INSENSITIVE)
    if accent is None:
        accent = True
    if _norm_phrase_set(strip, accent) & _norm_phrase_set(keep, accent):
        errors[CONF_STRIP_PHRASES] = "phrase_in_both"
    require = user_input.get(CONF_REQUIRE_PHRASE)
    if require is None:
        require = current.get(CONF_REQUIRE_PHRASE, True)
    if require and not strip and not keep:
        errors[CONF_STRIP_PHRASES] = "no_phrases"
    return errors


def _validate_fallback_self(hass: HomeAssistant, entry, fallback: Any) -> str | None:
    """Return the fallback error key if the fallback is our own agent."""
    if not fallback:
        return None
    own = _own_conversation_entity_id(hass, entry)
    if own and fallback == own:
        return "fallback_self"
    return None


class TTSBroadcastConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TTS Broadcast."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return TTSBroadcastOptionsFlow()

    async def async_step_user(self, user_input=None):
        errors: dict[str, str] = {}
        if user_input is not None:
            errors.update(_validate_speakers_section(user_input))
            errors.update(_validate_voice_section(user_input))
            tts_entity = user_input.get(CONF_TTS_ENTITY)
            if not tts_entity or self.hass.states.get(tts_entity) is None:
                errors[CONF_TTS_ENTITY] = "tts_entity_not_found"
            if not errors:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                user_input[CONF_STRIP_PHRASES] = _normalize_phrases(
                    user_input.get(CONF_STRIP_PHRASES, DEFAULT_STRIP_PHRASES)
                )
                user_input[CONF_KEEP_PHRASES] = _normalize_phrases(
                    user_input.get(CONF_KEEP_PHRASES, DEFAULT_KEEP_PHRASES)
                )
                user_input[CONF_NO_VOLUME_SPEAKERS] = user_input.get(
                    CONF_NO_VOLUME_SPEAKERS, []
                )
                return self.async_create_entry(
                    title="TTS Broadcast",
                    data={},
                    options=user_input,
                )

        combined = probatio.Schema({**SPEAKERS_SCHEMA.schema, **VOICE_SCHEMA.schema})
        if user_input is not None:
            combined = self.add_suggested_values_to_schema(combined, user_input)
        return self.async_show_form(
            step_id="user",
            data_schema=combined,
            errors=errors,
        )


class TTSBroadcastOptionsFlow(OptionsFlowWithReload):
    """Handle options flow."""

    async def async_step_init(self, user_input=None):
        return self.async_show_menu(
            step_id="init",
            menu_options=["speakers", "voice"],
        )

    async def async_step_speakers(self, user_input=None):
        errors: dict[str, str] = {}
        if user_input is not None:
            errors.update(
                _validate_speakers_section(user_input, self.config_entry.options)
            )
            tts_entity = user_input.get(
                CONF_TTS_ENTITY
            ) or self.config_entry.options.get(CONF_TTS_ENTITY)
            if not tts_entity or self.hass.states.get(tts_entity) is None:
                errors[CONF_TTS_ENTITY] = "tts_entity_not_found"
            if not errors:
                current = dict(self.config_entry.options)
                merged = {**current, **user_input}
                merged[CONF_STRIP_PHRASES] = current.get(
                    CONF_STRIP_PHRASES, DEFAULT_STRIP_PHRASES
                )
                merged[CONF_KEEP_PHRASES] = current.get(
                    CONF_KEEP_PHRASES, DEFAULT_KEEP_PHRASES
                )
                merged[CONF_NO_VOLUME_SPEAKERS] = user_input.get(
                    CONF_NO_VOLUME_SPEAKERS, current.get(CONF_NO_VOLUME_SPEAKERS, [])
                )
                merged[CONF_STRIP_PHRASES] = _normalize_phrases(
                    merged.get(CONF_STRIP_PHRASES)
                )
                merged[CONF_KEEP_PHRASES] = _normalize_phrases(
                    merged.get(CONF_KEEP_PHRASES)
                )
                return self.async_create_entry(title="", data=merged)

        schema = self.add_suggested_values_to_schema(
            SPEAKERS_SCHEMA, self.config_entry.options
        )
        return self.async_show_form(
            step_id="speakers",
            data_schema=schema,
            errors=errors,
        )

    async def async_step_voice(self, user_input=None):
        errors: dict[str, str] = {}
        if user_input is not None:
            errors.update(
                _validate_voice_section(user_input, self.config_entry.options)
            )
            fallback_error = _validate_fallback_self(
                self.hass, self.config_entry, user_input.get(CONF_FALLBACK_AGENT)
            )
            if fallback_error:
                errors[CONF_FALLBACK_AGENT] = fallback_error
            if not errors:
                current = dict(self.config_entry.options)
                merged = dict(current)
                optional_keys = (
                    CONF_STRIP_PHRASES,
                    CONF_KEEP_PHRASES,
                    CONF_REQUIRE_PHRASE,
                    CONF_FALLBACK_AGENT,
                    CONF_ACCENT_INSENSITIVE,
                    CONF_REPLY_TEXT,
                )
                for key in optional_keys:
                    if key in user_input:
                        merged[key] = user_input[key]
                    else:
                        merged.pop(key, None)
                merged[CONF_STRIP_PHRASES] = _normalize_phrases(
                    merged.get(CONF_STRIP_PHRASES) or []
                )
                merged[CONF_KEEP_PHRASES] = _normalize_phrases(
                    merged.get(CONF_KEEP_PHRASES) or []
                )
                return self.async_create_entry(title="", data=merged)

        schema = self.add_suggested_values_to_schema(
            VOICE_SCHEMA, self.config_entry.options
        )
        return self.async_show_form(
            step_id="voice",
            data_schema=schema,
            errors=errors,
        )
