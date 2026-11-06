"""The TTS Broadcast integration."""

from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass, field
from typing import Any

import probatio
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import async_track_entity_registry_updated_event

from .const import (
    ATTR_FAILED,
    ATTR_LANGUAGE,
    ATTR_MESSAGE,
    ATTR_OPTIONS,
    ATTR_PLAYED,
    ATTR_SKIPPED,
    ATTR_SPEAKERS,
    ATTR_VOLUME,
    CONF_NO_VOLUME_SPEAKERS,
    CONF_SPEAKERS,
    CONF_TTS_ENTITY,
    CONF_VOLUME,
    DEFAULT_VOLUME,
    DOMAIN,
    PLATFORMS,
    SERVICE_SPEAK,
    SERVICE_STOP,
)
from .const import (
    CONF_LANGUAGE as CONF_LANGUAGE_KEY,
)
from .const import (
    CONF_OPTIONS as CONF_OPTIONS_KEY,
)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


@dataclass
class TTSBroadcastRuntimeData:
    """Runtime data for a config entry."""

    entry: ConfigEntry
    lock: asyncio.Lock
    speakers: list[str] = field(default_factory=list)
    switch_entity_ids: dict[str, str] = field(default_factory=dict)


type TTSBroadcastConfigEntry = ConfigEntry[TTSBroadcastRuntimeData]


def _get_entries(hass: HomeAssistant) -> list[ConfigEntry]:
    return hass.config_entries.async_entries(DOMAIN)


def _get_entry(hass: HomeAssistant) -> ConfigEntry | None:
    entries = _get_entries(hass)
    if not entries:
        return None
    # Prefer a loaded entry.
    for entry in entries:
        if entry.state == ConfigEntryState.LOADED:
            return entry
    return entries[0]


def _config(entry: ConfigEntry) -> dict[str, Any]:
    return {**entry.data, **entry.options}


def _coerce_speakers(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    return [str(item) for item in value]


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the integration domain."""
    hass.data.setdefault(DOMAIN, {"lock": asyncio.Lock(), "entries": {}})

    async def _handle_speak(call: ServiceCall) -> dict[str, Any] | None:
        return await _async_speak(hass, call)

    async def _handle_stop(call: ServiceCall) -> dict[str, Any] | None:
        return await _async_stop(hass, call)

    hass.services.async_register(
        DOMAIN,
        SERVICE_SPEAK,
        _handle_speak,
        schema=probatio.Schema(
            {
                probatio.Required(ATTR_MESSAGE): cv.string,
                probatio.Optional(ATTR_SPEAKERS): [cv.entity_id],
                probatio.Optional(ATTR_VOLUME): probatio.All(
                    probatio.Coerce(float), probatio.Range(min=0, max=100)
                ),
                probatio.Optional(ATTR_LANGUAGE): cv.string,
                probatio.Optional(ATTR_OPTIONS): dict,
            }
        ),
        supports_response=SupportsResponse.OPTIONAL,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_STOP,
        _handle_stop,
        schema=probatio.Schema(
            {
                probatio.Optional(ATTR_SPEAKERS): [cv.entity_id],
            }
        ),
        supports_response=SupportsResponse.OPTIONAL,
    )

    return True


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    runtime_data = TTSBroadcastRuntimeData(entry=entry, lock=hass.data[DOMAIN]["lock"])
    entry.runtime_data = runtime_data  # type: ignore[attr-defined]
    hass.data[DOMAIN]["entries"][entry.entry_id] = runtime_data

    config = _config(entry)
    tracked = _coerce_speakers(config.get(CONF_SPEAKERS))

    async def _async_speaker_registry_updated(event) -> None:
        data = event.data
        action = data.get("action")
        old_entity_id = data.get("old_entity_id")
        entity_id = data["entity_id"]
        if action == "update" and old_entity_id and old_entity_id != entity_id:
            current_config = _config(entry)
            speakers = [
                entity_id if s == old_entity_id else s
                for s in _coerce_speakers(current_config.get(CONF_SPEAKERS))
            ]
            no_volume = [
                entity_id if s == old_entity_id else s
                for s in _coerce_speakers(current_config.get(CONF_NO_VOLUME_SPEAKERS))
            ]
            hass.config_entries.async_update_entry(
                entry,
                options={
                    **entry.options,
                    CONF_SPEAKERS: speakers,
                    CONF_NO_VOLUME_SPEAKERS: no_volume,
                },
            )
            await hass.config_entries.async_reload(entry.entry_id)
        elif action == "remove" and entity_id in tracked:
            current_config = _config(entry)
            speakers = [
                s
                for s in _coerce_speakers(current_config.get(CONF_SPEAKERS))
                if s != entity_id
            ]
            no_volume = [
                s
                for s in _coerce_speakers(current_config.get(CONF_NO_VOLUME_SPEAKERS))
                if s != entity_id
            ]
            hass.config_entries.async_update_entry(
                entry,
                options={
                    **entry.options,
                    CONF_SPEAKERS: speakers,
                    CONF_NO_VOLUME_SPEAKERS: no_volume,
                },
            )
            await hass.config_entries.async_reload(entry.entry_id)

    entry.async_on_unload(
        async_track_entity_registry_updated_event(
            hass, tracked, _async_speaker_registry_updated
        )
    )

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN]["entries"].pop(entry.entry_id, None)
    return unload_ok


async def _resolve_speakers(
    hass: HomeAssistant, entry: ConfigEntry, requested: list[str] | None
) -> tuple[list[str], list[str]]:
    """Resolve the list of speakers to use.

    Returns (resolved_speakers, skipped_unavailable).
    """
    config = _config(entry)
    configured = _coerce_speakers(config.get(CONF_SPEAKERS))
    if requested:
        # Validate subset.
        configured_set = set(configured)
        for speaker in requested:
            if speaker not in configured_set:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="speaker_not_configured",
                    translation_placeholders={"speaker": speaker},
                )
        candidates = list(requested)
    else:
        runtime_data: TTSBroadcastRuntimeData = entry.runtime_data  # type: ignore[attr-defined]
        # Use currently selected switches.
        selected: list[str] = []
        from homeassistant.helpers import entity_registry as er

        registry = er.async_get(hass)
        for speaker in configured:
            switch_entity_id = runtime_data.switch_entity_ids.get(speaker)
            if switch_entity_id is None:
                for ent in registry.entities.values():
                    if (
                        ent.config_entry_id == entry.entry_id
                        and ent.domain == "switch"
                        and ent.unique_id == f"{entry.entry_id}_switch_{speaker}"
                    ):
                        switch_entity_id = ent.entity_id
                        runtime_data.switch_entity_ids[speaker] = switch_entity_id
                        break
            is_on = False
            if switch_entity_id is not None:
                state = hass.states.get(switch_entity_id)
                is_on = bool(state is not None and state.state == "on")
            else:
                # Fall back to scanning switch entities for this entry.
                for entity_id in hass.states.async_entity_ids("switch"):
                    if entity_id.endswith(speaker.replace(".", "_")):
                        state = hass.states.get(entity_id)
                        is_on = bool(state is not None and state.state == "on")
            if is_on:
                selected.append(speaker)
        candidates = selected

    resolved: list[str] = []
    skipped: list[str] = []
    for speaker in candidates:
        state = hass.states.get(speaker)
        if state is None or state.state in ("unavailable", "unknown"):
            skipped.append(speaker)
            _LOGGER.warning("Skipping unavailable speaker %s", speaker)
            continue
        resolved.append(speaker)
    return resolved, skipped


_LOGGER = logging.getLogger(__name__)


async def _async_speak(hass: HomeAssistant, call: ServiceCall) -> dict[str, Any]:
    entry = _get_entry(hass)
    if entry is None:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="no_config_entry",
        )

    config = _config(entry)
    message = (call.data.get(ATTR_MESSAGE) or "").strip()
    if not message:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="empty_message",
        )

    requested = call.data.get(ATTR_SPEAKERS)
    requested_list = _coerce_speakers(requested) if requested is not None else None

    async with entry.runtime_data.lock:  # type: ignore[attr-defined]
        resolved, skipped_unavailable = await _resolve_speakers(
            hass, entry, requested_list
        )
        if not resolved:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="no_speaker",
            )

        no_volume = set(_coerce_speakers(config.get(CONF_NO_VOLUME_SPEAKERS)))
        volume_override = call.data.get(ATTR_VOLUME)
        if volume_override is None:
            volume = config.get(CONF_VOLUME, DEFAULT_VOLUME)
        else:
            volume = volume_override
        try:
            volume_float = float(volume)
        except (TypeError, ValueError):
            volume_float = 50.0
        volume_int = int(round(volume_float))

        tts_entity = config.get(CONF_TTS_ENTITY)
        if not tts_entity:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="no_tts_entity",
            )

        # Set volume on speakers that support it.
        failed_volume: list[str] = []
        for speaker in resolved:
            if speaker in no_volume:
                continue
            try:
                await hass.services.async_call(
                    "media_player",
                    "volume_set",
                    {"entity_id": speaker, "volume_level": volume_int / 100.0},
                    blocking=True,
                )
            except Exception as err:  # noqa: BLE001
                failed_volume.append(speaker)
                _LOGGER.warning("Failed to set volume on %s: %s", speaker, err)

        language = call.data.get(ATTR_LANGUAGE)
        if language is None:
            language = config.get(CONF_LANGUAGE_KEY)
        options = call.data.get(ATTR_OPTIONS)
        if options is None:
            options = config.get(CONF_OPTIONS_KEY)

        service_data: dict[str, Any] = {
            "media_player_entity_id": resolved,
            "message": message,
            "cache": False,
        }
        if language:
            service_data["language"] = language
        if options:
            service_data["options"] = options

        played: list[str] = []
        failed_tts: list[str] = []
        try:
            await hass.services.async_call(
                "tts",
                "speak",
                {"entity_id": tts_entity, **service_data},
                blocking=True,
            )
            played = list(resolved)
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("TTS speak failed: %s", err)
            failed_tts = list(resolved)
            played = []

        failed = failed_tts + [s for s in failed_volume if s not in failed_tts]
        return {
            ATTR_PLAYED: played,
            ATTR_SKIPPED: skipped_unavailable,
            ATTR_FAILED: failed,
        }


async def _async_stop(hass: HomeAssistant, call: ServiceCall) -> dict[str, Any]:
    entry = _get_entry(hass)
    if entry is None:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="no_config_entry",
        )

    requested = call.data.get(ATTR_SPEAKERS)
    requested_list = _coerce_speakers(requested) if requested is not None else None

    async with entry.runtime_data.lock:  # type: ignore[attr-defined]
        resolved, skipped_unavailable = await _resolve_speakers(
            hass, entry, requested_list
        )

        failed: list[str] = []
        for speaker in resolved:
            try:
                await hass.services.async_call(
                    "media_player",
                    "media_stop",
                    {"entity_id": speaker},
                    blocking=True,
                )
            except Exception as err:  # noqa: BLE001
                failed.append(speaker)
                _LOGGER.warning("Failed to stop %s: %s", speaker, err)

        return {
            ATTR_PLAYED: [],
            ATTR_SKIPPED: skipped_unavailable,
            ATTR_FAILED: failed,
        }
