"""Tests for diagnostics."""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.tts_broadcast.const import DOMAIN
from custom_components.tts_broadcast.diagnostics import (
    async_get_config_entry_diagnostics,
)


async def test_diagnostics(hass: HomeAssistant, mock_config_entry) -> None:
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    async_mock_service(hass, "media_player", "volume_set")
    async_mock_service(hass, "tts", "speak")

    data = await async_get_config_entry_diagnostics(hass, mock_config_entry)
    assert data["entry_id"] == "test_entry"
    assert data["speakers"] == ["media_player.speaker_one", "media_player.speaker_two"]
    assert data["last_result"] is None

    hass.states.async_set("media_player.speaker_one", "idle")
    hass.states.async_set("media_player.speaker_two", "idle")
    for eid in hass.states.async_entity_ids("switch"):
        if "tts_broadcast" in eid:
            await hass.services.async_call(
                "switch", "turn_on", {"entity_id": eid}, blocking=True
            )
    await hass.async_block_till_done()

    result = await hass.services.async_call(
        DOMAIN,
        "speak",
        {"message": "hi"},
        blocking=True,
        return_response=True,
    )
    await hass.async_block_till_done()
    assert result["failed"] == []

    data = await async_get_config_entry_diagnostics(hass, mock_config_entry)
    assert data["last_result"] is not None
    assert data["last_result"]["failed"] == []
    assert data["last_result"]["errors"] == {}
    assert data["last_result"]["resolved"] == [
        "media_player.speaker_one",
        "media_player.speaker_two",
    ]
