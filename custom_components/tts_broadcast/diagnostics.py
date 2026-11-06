"""Diagnostics for TTS Broadcast."""

from __future__ import annotations

from typing import Any

from homeassistant.core import HomeAssistant

from . import TTSBroadcastConfigEntry


async def async_get_config_entry_diagnostics(
    hass: HomeAssistant, entry: TTSBroadcastConfigEntry
) -> dict[str, Any]:
    """Return diagnostics."""
    config = {**entry.data, **entry.options}
    runtime_data = entry.runtime_data
    return {
        "entry_id": entry.entry_id,
        "state": entry.state.value,
        "tts_entity": config.get("tts_entity"),
        "speakers": config.get("speakers", []),
        "no_volume_speakers": config.get("no_volume_speakers", []),
        "volume": config.get("volume"),
        "language": config.get("language"),
        "last_result": runtime_data.last_result if runtime_data else None,
    }
