"""Tests for entities."""

from __future__ import annotations

from homeassistant.core import HomeAssistant


async def test_switch_restore(hass: HomeAssistant, mock_config_entry) -> None:
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    switches = hass.states.async_entity_ids("switch")
    assert len(switches) == 2

    # Turn one on via service
    await hass.services.async_call(
        "switch", "turn_on", {"entity_id": switches[0]}, blocking=True
    )
    await hass.async_block_till_done()
    assert hass.states.get(switches[0]).state == "on"


async def test_number_restore(hass: HomeAssistant, mock_config_entry) -> None:
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    numbers = hass.states.async_entity_ids("number")
    assert len(numbers) == 1
    await hass.services.async_call(
        "number", "set_value", {"entity_id": numbers[0], "value": 70}, blocking=True
    )
    await hass.async_block_till_done()
    assert float(hass.states.get(numbers[0]).state) == 70.0


async def test_text_restore(hass: HomeAssistant, mock_config_entry) -> None:
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    texts = hass.states.async_entity_ids("text")
    assert len(texts) == 1
    await hass.services.async_call(
        "text", "set_value", {"entity_id": texts[0], "value": "hello"}, blocking=True
    )
    await hass.async_block_till_done()
    assert hass.states.get(texts[0]).state == "hello"
