"""Tests for setup and unload."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from custom_components.tts_broadcast.const import DOMAIN


async def test_setup_and_unload(hass: HomeAssistant, mock_config_entry) -> None:
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    assert (
        mock_config_entry.state.value == "loaded"
        or str(mock_config_entry.state) == "loaded"
    )
    assert hass.services.has_service(DOMAIN, "speak")
    assert hass.services.has_service(DOMAIN, "stop")

    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert hass.services.has_service(DOMAIN, "speak")
    assert hass.services.has_service(DOMAIN, "stop")


async def test_reload(hass: HomeAssistant, mock_config_entry) -> None:
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    await hass.config_entries.async_reload(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    assert (
        mock_config_entry.state.value == "loaded"
        or str(mock_config_entry.state) == "loaded"
    )
