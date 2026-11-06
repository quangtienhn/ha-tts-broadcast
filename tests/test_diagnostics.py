"""Tests for diagnostics."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from custom_components.tts_broadcast.diagnostics import (
    async_get_config_entry_diagnostics,
)


async def test_diagnostics(hass: HomeAssistant, mock_config_entry) -> None:
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    data = await async_get_config_entry_diagnostics(hass, mock_config_entry)
    assert data["entry_id"] == "test_entry"
    assert data["speakers"] == ["media_player.speaker_one", "media_player.speaker_two"]
