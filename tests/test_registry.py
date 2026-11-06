"""Tests for entity registry handling."""

from __future__ import annotations

from homeassistant.core import HomeAssistant

from custom_components.tts_broadcast.const import DOMAIN


async def test_unavailable_speaker_skipped(
    hass: HomeAssistant, mock_config_entry
) -> None:
    hass.states.async_set("media_player.speaker_one", "idle")
    hass.states.async_set("media_player.speaker_two", "idle")
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    from pytest_homeassistant_custom_component.common import async_mock_service

    async_mock_service(hass, "media_player", "volume_set")
    speak_calls = async_mock_service(hass, "tts", "speak")

    hass.states.async_set("media_player.speaker_one", "unavailable")

    result = await hass.services.async_call(
        DOMAIN,
        "speak",
        {
            "message": "hi",
            "speakers": ["media_player.speaker_one", "media_player.speaker_two"],
        },
        blocking=True,
        return_response=True,
    )
    await hass.async_block_till_done()

    assert result["skipped"] == ["media_player.speaker_one"]
    assert speak_calls[0].data["media_player_entity_id"] == ["media_player.speaker_two"]
