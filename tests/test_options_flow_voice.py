"""Tests for voice options flow."""

from __future__ import annotations

import pytest
from homeassistant import data_entry_flow
from homeassistant.core import HomeAssistant


@pytest.mark.asyncio
async def test_voice_options_save(hass: HomeAssistant, mock_config_entry) -> None:
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(mock_config_entry.entry_id)
    result = await hass.config_entries.options.async_configure(
        result["flow_id"], {"next_step_id": "voice"}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        {
            "strip_phrases": ["thông báo"],
            "keep_phrases": ["xin chào"],
            "require_phrase": True,
            "accent_insensitive": True,
            "reply_text": "Đã gửi",
        },
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    await hass.async_block_till_done()
    assert mock_config_entry.options["strip_phrases"] == ["thông báo"]
    assert mock_config_entry.options["keep_phrases"] == ["xin chào"]
