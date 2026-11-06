"""Tests for config flow."""

from __future__ import annotations

from homeassistant import config_entries, data_entry_flow
from homeassistant.core import HomeAssistant

from custom_components.tts_broadcast.const import DOMAIN


async def test_user_flow_valid(hass: HomeAssistant) -> None:
    hass.states.async_set("tts.wyoming_vietnamese", "idle")
    hass.states.async_set("media_player.speaker_one", "idle")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "tts_entity": "tts.wyoming_vietnamese",
            "speakers": ["media_player.speaker_one"],
            "no_volume_speakers": [],
            "volume": 40,
            "language": "",
            "options": {},
        },
    )
    assert result["type"] == data_entry_flow.FlowResultType.CREATE_ENTRY
    assert result["data"] == {}
    assert result["options"]["speakers"] == ["media_player.speaker_one"]


async def test_user_flow_no_speakers(hass: HomeAssistant) -> None:
    hass.states.async_set("tts.wyoming_vietnamese", "idle")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "tts_entity": "tts.wyoming_vietnamese",
            "speakers": [],
            "no_volume_speakers": [],
            "volume": 50,
            "language": "",
            "options": {},
        },
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"]["speakers"] == "no_speakers"


async def test_user_flow_missing_tts(hass: HomeAssistant) -> None:
    hass.states.async_set("media_player.speaker_one", "idle")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "tts_entity": "tts.missing",
            "speakers": ["media_player.speaker_one"],
            "no_volume_speakers": [],
            "volume": 50,
            "language": "",
            "options": {},
        },
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"]["tts_entity"] == "tts_entity_not_found"


async def test_user_flow_bad_subset(hass: HomeAssistant) -> None:
    hass.states.async_set("tts.wyoming_vietnamese", "idle")
    hass.states.async_set("media_player.speaker_one", "idle")

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "tts_entity": "tts.wyoming_vietnamese",
            "speakers": ["media_player.speaker_one"],
            "no_volume_speakers": ["media_player.other"],
            "volume": 50,
            "language": "",
            "options": {},
        },
    )
    assert result["type"] == data_entry_flow.FlowResultType.FORM
    assert result["errors"]["no_volume_speakers"] == "invalid_subset"


async def test_single_config_entry(hass: HomeAssistant) -> None:
    hass.states.async_set("tts.wyoming_vietnamese", "idle")
    hass.states.async_set("media_player.speaker_one", "idle")

    await _create_entry(hass)
    # second attempt aborts
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == data_entry_flow.FlowResultType.ABORT
    assert result["reason"] in ("already_configured", "single_instance_allowed")


async def _create_entry(hass: HomeAssistant):
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            "tts_entity": "tts.wyoming_vietnamese",
            "speakers": ["media_player.speaker_one"],
            "no_volume_speakers": [],
            "volume": 50,
            "language": "",
            "options": {},
        },
    )
    return result["result"]
