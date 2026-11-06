"""Tests for dashboard card service."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant

from custom_components.tts_broadcast.const import DOMAIN


@pytest.mark.asyncio
async def test_get_dashboard_card(hass: HomeAssistant, mock_config_entry) -> None:
    hass.states.async_set("media_player.speaker_one", "idle")
    hass.states.async_set("media_player.speaker_two", "idle")
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.services.async_call(
        DOMAIN, "get_dashboard_card", {}, blocking=True, return_response=True
    )
    await hass.async_block_till_done()

    assert "yaml" in result
    assert "switch.tts_broadcast" in result["yaml"]
    assert "type: button" in result["yaml"]