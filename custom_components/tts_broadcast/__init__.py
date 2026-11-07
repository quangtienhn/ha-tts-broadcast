"""The TTS Broadcast integration."""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any

import probatio
from homeassistant.config_entries import ConfigEntry, ConfigEntryState
from homeassistant.core import Context, HomeAssistant, ServiceCall, SupportsResponse
from homeassistant.exceptions import ServiceValidationError
from homeassistant.helpers import config_validation as cv
from homeassistant.helpers.event import (
    async_track_entity_registry_updated_event,
    async_track_state_change_event,
)
from homeassistant.util import dt as dt_util

from .const import (
    ATTR_FAILED,
    ATTR_LANGUAGE,
    ATTR_MESSAGE,
    ATTR_OPTIONS,
    ATTR_PLAYED,
    ATTR_SKIPPED,
    ATTR_SPEAKERS,
    ATTR_TARGETED,
    ATTR_UNEXPECTED_STARTED,
    ATTR_VOLUME,
    CONF_LANGUAGE,
    CONF_NO_VOLUME_SPEAKERS,
    CONF_OPTIONS,
    CONF_SPEAKERS,
    CONF_TTS_ENTITY,
    CONF_VOLUME,
    DEFAULT_VOLUME,
    DOMAIN,
    PLATFORMS,
    SERVICE_DEBUG_SELECTION,
    SERVICE_GET_DASHBOARD_CARD,
    SERVICE_SPEAK,
    SERVICE_STOP,
    VERSION,
)

CONFIG_SCHEMA = cv.config_entry_only_config_schema(DOMAIN)


@dataclass
class TTSBroadcastRuntimeData:
    """Runtime data for a config entry."""

    entry: ConfigEntry
    lock: asyncio.Lock
    speakers: list[str] = field(default_factory=list)
    switch_entity_ids: dict[str, str] = field(default_factory=dict)
    last_result: dict[str, Any] | None = None


type TTSBroadcastConfigEntry = ConfigEntry[TTSBroadcastRuntimeData]


def _get_entries(hass: HomeAssistant) -> list[ConfigEntry]:
    return hass.config_entries.async_entries(DOMAIN)


def _get_entry(hass: HomeAssistant) -> TTSBroadcastConfigEntry | None:
    entries = _get_entries(hass)
    if not entries:
        return None
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


_LOGGER = logging.getLogger(__name__)


async def async_setup(hass: HomeAssistant, config: dict[str, Any]) -> bool:
    """Set up the integration domain."""
    hass.data.setdefault(DOMAIN, {"lock": asyncio.Lock(), "entries": {}})
    if not hass.data[DOMAIN].get("static_registered"):
        try:
            from homeassistant.components.frontend import add_extra_js_url
            from homeassistant.components.http import StaticPathConfig

            await hass.http.async_register_static_paths(
                [
                    StaticPathConfig(
                        "/tts_broadcast/tts-broadcast-card.js",
                        hass.config.path(
                            "custom_components/tts_broadcast/www/tts-broadcast-card.js"
                        ),
                        cache_headers=True,
                    )
                ]
            )
            add_extra_js_url(hass, f"/tts_broadcast/tts-broadcast-card.js?v={VERSION}")
            hass.data[DOMAIN]["static_registered"] = True
        except Exception as err:  # noqa: BLE001
            _LOGGER.warning("Could not register frontend card: %s", err)

    async def _handle_speak(call: ServiceCall) -> dict[str, Any] | None:
        return await _async_speak(hass, call)

    async def _handle_stop(call: ServiceCall) -> dict[str, Any] | None:
        return await _async_stop(hass, call)

    async def _handle_get_dashboard_card(call: ServiceCall) -> dict[str, Any] | None:
        return await _async_get_dashboard_card(hass, call)

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
                probatio.Optional("cache"): cv.boolean,
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

    hass.services.async_register(
        DOMAIN,
        SERVICE_GET_DASHBOARD_CARD,
        _handle_get_dashboard_card,
        schema=probatio.Schema(
            {
                probatio.Optional("notify"): cv.boolean,
            }
        ),
        supports_response=SupportsResponse.ONLY,
    )

    hass.services.async_register(
        DOMAIN,
        SERVICE_DEBUG_SELECTION,
        _async_debug_selection,
        schema=probatio.Schema({}),
        supports_response=SupportsResponse.ONLY,
    )

    return True


async def _async_debug_selection(
    hass: HomeAssistant, call: ServiceCall
) -> dict[str, Any]:
    """Diagnostic service: report speaker selection state with no side effects."""
    entry = _get_entry(hass)
    if entry is None:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="no_config_entry",
        )
    from homeassistant.helpers import entity_registry as er

    config = _config(entry)
    configured = _coerce_speakers(config.get(CONF_SPEAKERS))
    registry = er.async_get(hass)

    speakers_info: list[dict[str, Any]] = []
    for speaker in configured:
        state = hass.states.get(speaker)
        attrs = dict(state.attributes) if state else {}
        reg_ent = registry.async_get(speaker)
        group_members = attrs.get("group_members") or attrs.get("entity_id") or []
        switch_entity_id = entry.runtime_data.switch_entity_ids.get(speaker)
        switch_state = hass.states.get(switch_entity_id) if switch_entity_id else None
        reg_lookup = None
        for ent in registry.entities.values():
            if (
                ent.config_entry_id == entry.entry_id
                and ent.domain == "switch"
                and ent.unique_id == f"{entry.entry_id}_switch_{speaker}"
            ):
                reg_lookup = ent.entity_id
                break
        speakers_info.append(
            {
                "speaker": speaker,
                "state": state.state if state else None,
                "group_members": (
                    list(group_members)
                    if isinstance(group_members, list | tuple | set)
                    else group_members
                ),
                "sync_group": attrs.get("sync_group"),
                "supported_features": attrs.get("supported_features"),
                "platform": reg_ent.platform if reg_ent else None,
                "device_id": reg_ent.device_id if reg_ent else None,
                "switch_entity_id": switch_entity_id,
                "switch_state": switch_state.state if switch_state else None,
                "mapping_matches_registry_lookup": switch_entity_id == reg_lookup,
            }
        )

    resolved, skipped = await _resolve_speakers(hass, entry, None)

    grouping: list[dict[str, Any]] = []
    for ent in registry.entities.values():
        if ent.domain != "media_player":
            continue
        st = hass.states.get(ent.entity_id)
        attrs = dict(st.attributes) if st else {}
        members = attrs.get("group_members") or []
        if isinstance(members, list | tuple | set):
            for m in members:
                if m in configured and m != ent.entity_id:
                    grouping.append({"media_player": ent.entity_id, "lists_speaker": m})

    return {
        "speakers": speakers_info,
        "resolved": resolved,
        "skipped": skipped,
        "grouping": grouping,
        "last_result": entry.runtime_data.last_result,
    }


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Set up a config entry."""
    runtime_data = TTSBroadcastRuntimeData(entry=entry, lock=hass.data[DOMAIN]["lock"])
    entry.runtime_data = runtime_data  # type: ignore[attr-defined]
    hass.data[DOMAIN]["entries"][entry.entry_id] = runtime_data

    config = _config(entry)
    tracked = _coerce_speakers(config.get(CONF_SPEAKERS))
    runtime_data.volume = float(config.get(CONF_VOLUME, DEFAULT_VOLUME))

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

    # Registry hygiene: warn about stale or duplicate switch mappings (no auto-delete)
    configured_set = set(_coerce_speakers(config.get(CONF_SPEAKERS)))
    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    prefix = f"{entry.entry_id}_switch_"
    seen_speakers: dict[str, str] = {}
    for ent in registry.entities.values():
        if ent.config_entry_id != entry.entry_id or ent.domain != "switch":
            continue
        if not ent.unique_id or not ent.unique_id.startswith(prefix):
            continue
        speaker = ent.unique_id[len(prefix) :]
        if speaker not in configured_set:
            _LOGGER.warning(
                "tts_broadcast stale switch entity %s maps to unconfigured speaker %s",
                ent.entity_id,
                speaker,
            )
        elif speaker in seen_speakers:
            _LOGGER.warning(
                "tts_broadcast duplicate switch mapping for speaker %s: %s and %s",
                speaker,
                seen_speakers[speaker],
                ent.entity_id,
            )
        else:
            seen_speakers[speaker] = ent.entity_id

    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data[DOMAIN]["entries"].pop(entry.entry_id, None)
    return unload_ok


async def _resolve_speakers(
    hass: HomeAssistant, entry: TTSBroadcastConfigEntry, requested: list[str] | None
) -> tuple[list[str], list[str]]:
    """Resolve the list of speakers to use."""
    config = _config(entry)
    configured = _coerce_speakers(config.get(CONF_SPEAKERS))
    if requested:
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
        from homeassistant.helpers import entity_registry as er

        registry = er.async_get(hass)
        selected: list[str] = []
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


def _own_conversation_entity_id(
    hass: HomeAssistant, entry: TTSBroadcastConfigEntry
) -> str | None:
    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    for ent in registry.entities.values():
        if ent.config_entry_id == entry.entry_id and ent.domain == "conversation":
            return ent.entity_id
    return None


async def async_announce(
    hass: HomeAssistant,
    entry: TTSBroadcastConfigEntry,
    message: str,
    speakers: list[str] | None = None,
    volume: float | None = None,
    language: str | None = None,
    options: Any = None,
    cache: bool = False,
    context: Context | None = None,
) -> dict[str, Any]:
    config = _config(entry)
    message = message.strip()
    started = time.monotonic()
    if context is None:
        context = Context()
    if not message:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="empty_message",
        )

    async with entry.runtime_data.lock:
        resolved, skipped_unavailable = await _resolve_speakers(hass, entry, speakers)
        if not resolved:
            raise ServiceValidationError(
                translation_domain=DOMAIN,
                translation_key="no_speaker",
            )

        no_volume = set(_coerce_speakers(config.get(CONF_NO_VOLUME_SPEAKERS)))
        if volume is None:
            volume = (
                entry.runtime_data.volume
                if entry.runtime_data.volume is not None
                else config.get(CONF_VOLUME, DEFAULT_VOLUME)
            )
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

        failed_volume: list[str] = []
        volume_errors: dict[str, str] = {}
        volume_tasks = []
        for speaker in resolved:
            if speaker in no_volume:
                continue

            async def _volume_call(speaker: str = speaker) -> BaseException | None:
                try:
                    await hass.services.async_call(
                        "media_player",
                        "volume_set",
                        {
                            "entity_id": speaker,
                            "volume_level": volume_int / 100.0,
                        },
                        blocking=True,
                        context=context,
                    )
                    return None
                except Exception as err:  # noqa: BLE001
                    return err

            volume_tasks.append(_volume_call())
        volume_results = await asyncio.gather(*volume_tasks, return_exceptions=True)
        volume_targets = [s for s in resolved if s not in no_volume]
        for speaker, err in zip(volume_targets, volume_results, strict=False):
            if err is not None:
                failed_volume.append(speaker)
                volume_errors[speaker] = f"{type(err).__name__}: {err}"

        if language is None:
            language = config.get(CONF_LANGUAGE)
        if options is None:
            options = config.get(CONF_OPTIONS)

        service_data: dict[str, Any] = {
            "media_player_entity_id": resolved,
            "message": message,
            "cache": cache,
        }
        if language:
            service_data["language"] = language
        if options:
            service_data["options"] = options

        async def _speak_one(speaker: str = speaker) -> BaseException | None:
            try:
                await hass.services.async_call(
                    "tts",
                    "speak",
                    {
                        "entity_id": tts_entity,
                        **service_data,
                        "media_player_entity_id": [speaker],
                    },
                    blocking=True,
                    context=context,
                )
                return None
            except Exception as err:  # noqa: BLE001
                return err

        speak_tasks = [_speak_one(s) for s in resolved]
        speak_results = await asyncio.gather(*speak_tasks, return_exceptions=True)

        played: list[str] = []
        failed_tts: list[str] = []
        errors: dict[str, str] = {}
        for speaker, err in zip(resolved, speak_results, strict=False):
            if err is None:
                played.append(speaker)
            else:
                failed_tts.append(speaker)
                errors[speaker] = f"{type(err).__name__}: {err}"
        errors.update(volume_errors)

        failed = failed_tts + [s for s in failed_volume if s not in failed_tts]
        result: dict[str, Any] = {
            ATTR_PLAYED: played,
            ATTR_SKIPPED: skipped_unavailable,
            ATTR_FAILED: failed,
            ATTR_TARGETED: resolved,
            ATTR_UNEXPECTED_STARTED: [],
            "errors": errors,
        }
        entry.runtime_data.last_result = {
            "timestamp": dt_util.utcnow().isoformat(),
            "context_id": context.id,
            "resolved": resolved,
            "skipped": skipped_unavailable,
            "failed": failed,
            "errors": errors,
            "targeted": resolved,
            "unexpected_started": [],
        }
        _LOGGER.info(
            "tts_broadcast announce context=%s targeted=%s "
            "resolved=%s skipped=%s failed=%s",
            context.id,
            resolved,
            resolved,
            skipped_unavailable,
            failed,
        )
        for speaker in failed:
            _LOGGER.warning(
                "tts_broadcast announce failed for speaker %s: %s",
                speaker,
                errors.get(speaker, "unknown error"),
            )
        _LOGGER.debug(
            "tts_broadcast announce took %s seconds", time.monotonic() - started
        )

        async def _audit_unexpected() -> None:
            unexpected: list[str] = []

            def _listener(event) -> None:
                new_state = event.data.get("new_state")
                if new_state is None:
                    return
                if new_state.state not in ("playing", "buffering"):
                    return
                entity_id = new_state.entity_id or ""
                if not entity_id.startswith("media_player."):
                    return
                if entity_id not in resolved:
                    unexpected.append(entity_id)

            unsub = async_track_state_change_event(
                hass,
                hass.states.async_entity_ids("media_player"),
                _listener,
            )
            try:
                await asyncio.sleep(20)
            finally:
                unsub()
            entry.runtime_data.last_result["unexpected_started"] = unexpected
            for entity_id in unexpected:
                _LOGGER.warning(
                    "tts_broadcast unexpected player started %s context=%s",
                    entity_id,
                    context.id,
                )

        entry.async_create_background_task(
            hass, _audit_unexpected(), "tts_broadcast_audit"
        )
        return result


async def _async_speak(hass: HomeAssistant, call: ServiceCall) -> dict[str, Any]:
    entry = _get_entry(hass)
    if entry is None:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="no_config_entry",
        )
    message = (call.data.get(ATTR_MESSAGE) or "").strip()
    if not message:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="empty_message",
        )
    requested = call.data.get(ATTR_SPEAKERS)
    requested_list = _coerce_speakers(requested) if requested is not None else None
    return await async_announce(
        hass,
        entry,
        message,
        speakers=requested_list,
        volume=call.data.get(ATTR_VOLUME),
        language=call.data.get(ATTR_LANGUAGE),
        options=call.data.get(ATTR_OPTIONS),
        cache=call.data.get("cache") or False,
        context=call.context,
    )


async def _async_stop(hass: HomeAssistant, call: ServiceCall) -> dict[str, Any]:
    entry = _get_entry(hass)
    if entry is None:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="no_config_entry",
        )

    requested = call.data.get(ATTR_SPEAKERS)
    requested_list = _coerce_speakers(requested) if requested is not None else None

    async with entry.runtime_data.lock:
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


async def _async_get_dashboard_card(
    hass: HomeAssistant, call: ServiceCall
) -> dict[str, Any]:
    entry = _get_entry(hass)
    if entry is None:
        raise ServiceValidationError(
            translation_domain=DOMAIN,
            translation_key="no_config_entry",
        )
    yaml_text = _build_dashboard_card_yaml(hass, entry)
    if call.data.get("notify"):
        await hass.services.async_call(
            "persistent_notification",
            "create",
            {
                "title": "TTS Broadcast",
                "message": f"```yaml\n{yaml_text}\n```",
            },
            blocking=True,
        )
    return {"yaml": yaml_text}


_ASSIST_BUTTON_NAMES = {"en": "TALK", "vi": "NÓI"}
_ASSIST_BUTTON_ICON = "mdi:microphone"


def _assist_button_name(config: dict[str, Any]) -> str:
    """Return the localized Assist row name."""
    if config.get("assist_name"):
        return config.get("assist_name")
    lang = str(config.get("language") or "en").split("-")[0]
    return _ASSIST_BUTTON_NAMES.get(lang, _ASSIST_BUTTON_NAMES["en"])


def _assist_button_icon(config: dict[str, Any]) -> str:
    """Return the Assist row icon."""
    return config.get("assist_icon") or _ASSIST_BUTTON_ICON


def _build_dashboard_card_yaml(hass: HomeAssistant, entry: ConfigEntry) -> str:
    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    entities = [
        e for e in registry.entities.values() if e.config_entry_id == entry.entry_id
    ]
    switches = sorted(
        [
            e
            for e in entities
            if e.domain == "switch" and e.translation_key == "speaker"
        ],
        key=lambda e: (
            (
                hass.states.get(e.entity_id).attributes.get("friendly_name")
                if hass.states.get(e.entity_id)
                else None
            )
            or e.entity_id
        ),
    )
    volume = next(
        (e for e in entities if e.domain == "number" and e.translation_key == "volume"),
        None,
    )
    message = next(
        (e for e in entities if e.domain == "text" and e.translation_key == "message"),
        None,
    )
    speak = next(
        (e for e in entities if e.domain == "button" and e.translation_key == "speak"),
        None,
    )
    stop = next(
        (e for e in entities if e.domain == "button" and e.translation_key == "stop"),
        None,
    )
    select_all = next(
        (
            e
            for e in entities
            if e.domain == "button" and e.translation_key == "select_all"
        ),
        None,
    )
    select_none = next(
        (
            e
            for e in entities
            if e.domain == "button" and e.translation_key == "select_none"
        ),
        None,
    )

    lines = ["type: entities", "title: TTS Broadcast", "entities:"]
    for entity in switches:
        lines.append(f"  - {entity.entity_id}")
    if volume is not None or message is not None:
        lines.append("  - type: divider")
        if volume is not None:
            lines.append(f"  - {volume.entity_id}")
        if message is not None:
            lines.append(f"  - {message.entity_id}")
    lines.append("  - type: divider")
    if speak is not None:
        lines.append(f"  - {speak.entity_id}")
    lines.append("  - type: button")
    lines.append(f"    name: {_assist_button_name(_config(entry))}")
    lines.append(f"    icon: {_assist_button_icon(_config(entry))}")
    lines.append("    tap_action:")
    lines.append("      action: assist")
    lines.append("      pipeline_id: preferred")
    lines.append("      start_listening: true")
    if stop is not None:
        lines.append(f"  - {stop.entity_id}")
    if select_all is not None:
        lines.append(f"  - {select_all.entity_id}")
    if select_none is not None:
        lines.append(f"  - {select_none.entity_id}")
    return "\n".join(lines)
