"""Tests for options flow."""

from __future__ import annotations

import pytest
from homeassistant import data_entry_flow
from homeassistant.core import HomeAssistant


@pytest.mark.asyncio
async def test_options_flow_opens(hass: HomeAssistant, mock_config_entry) -> None:
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    assert result["type"] == data_entry_flow.FlowResultType.MENU

    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "voice"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
