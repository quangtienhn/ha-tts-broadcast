"""Tests for services."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from homeassistant.exceptions import HomeAssistantError
from pytest_homeassistant_custom_component.common import async_mock_service

from custom_components.tts_broadcast.const import DOMAIN


@pytest.fixture
async def setup_entry(hass: HomeAssistant, mock_config_entry):
    hass.states.async_set("media_player.speaker_one", "idle")
    hass.states.async_set("media_player.speaker_two", "idle")
    mock_config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()
    # mark switches: first on, second off
    switches = hass.states.async_entity_ids("switch")
    if switches:
        await hass.services.async_call(
            "switch", "turn_on", {"entity_id": switches[0]}, blocking=True
        )
    return mock_config_entry


async def test_speak_selected(hass: HomeAssistant, setup_entry) -> None:
    volume_calls = async_mock_service(hass, "media_player", "volume_set")
    speak_calls = async_mock_service(hass, "tts", "speak")

    result = await hass.services.async_call(
        DOMAIN, "speak", {"message": "hello"}, blocking=True, return_response=True
    )
    await hass.async_block_till_done()

    assert result["played"] == ["media_player.speaker_one"]
    assert result["skipped"] == []
    assert len(volume_calls) == 1
    assert volume_calls[0].data["entity_id"] == "media_player.speaker_one"
    assert len(speak_calls) == 1
    assert speak_calls[0].data["media_player_entity_id"] == ["media_player.speaker_one"]


async def test_speak_explicit_speakers(hass: HomeAssistant, setup_entry) -> None:
    async_mock_service(hass, "media_player", "volume_set")
    speak_calls = async_mock_service(hass, "tts", "speak")

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

    assert set(result["played"]) == {
        "media_player.speaker_one",
        "media_player.speaker_two",
    }
    assert len(speak_calls) == 2
    calls_by_speaker = {
        call.data["media_player_entity_id"][0]: call for call in speak_calls
    }
    assert calls_by_speaker["media_player.speaker_one"].data[
        "media_player_entity_id"
    ] == ["media_player.speaker_one"]
    assert calls_by_speaker["media_player.speaker_two"].data[
        "media_player_entity_id"
    ] == ["media_player.speaker_two"]


async def test_speak_response_shape(hass: HomeAssistant, setup_entry) -> None:
    async_mock_service(hass, "media_player", "volume_set")
    async_mock_service(hass, "tts", "speak")

    result = await hass.services.async_call(
        DOMAIN,
        "speak",
        {"message": "hi"},
        blocking=True,
        return_response=True,
    )
    await hass.async_block_till_done()

    assert set(result) == {
        "played",
        "skipped",
        "failed",
        "errors",
        "targeted",
        "unexpected_started",
        "context_id",
    }
    assert result["errors"] == {}
    assert result["targeted"] == ["media_player.speaker_one"]
    assert result["unexpected_started"] == []


async def test_speak_cache_flag(hass: HomeAssistant, setup_entry) -> None:
    speak_calls = async_mock_service(hass, "tts", "speak")

    await hass.services.async_call(
        DOMAIN,
        "speak",
        {"message": "hi", "cache": True},
        blocking=True,
        return_response=True,
    )
    await hass.async_block_till_done()

    assert speak_calls[0].data["cache"] is True


async def test_slider_volume_used(hass: HomeAssistant, setup_entry) -> None:
    volume_calls = async_mock_service(hass, "media_player", "volume_set")
    async_mock_service(hass, "tts", "speak")

    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": "number.tts_broadcast_volume", "value": 80},
        blocking=True,
    )
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN, "speak", {"message": "hi"}, blocking=True, return_response=True
    )
    await hass.async_block_till_done()

    assert len(volume_calls) == 1
    assert volume_calls[0].data["entity_id"] == "media_player.speaker_one"
    assert volume_calls[0].data["volume_level"] == 0.8


async def test_service_volume_override_wins(hass: HomeAssistant, setup_entry) -> None:
    volume_calls = async_mock_service(hass, "media_player", "volume_set")
    async_mock_service(hass, "tts", "speak")

    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": "number.tts_broadcast_volume", "value": 80},
        blocking=True,
    )
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN,
        "speak",
        {"message": "hi", "volume": 30},
        blocking=True,
        return_response=True,
    )
    await hass.async_block_till_done()

    assert volume_calls[0].data["volume_level"] == 0.3


async def test_no_volume_speaker_no_volume_set(
    hass: HomeAssistant, setup_entry
) -> None:
    volume_calls = async_mock_service(hass, "media_player", "volume_set")
    async_mock_service(hass, "tts", "speak")

    for eid in hass.states.async_entity_ids("switch"):
        if "tts_broadcast" in eid:
            await hass.services.async_call(
                "switch", "turn_on", {"entity_id": eid}, blocking=True
            )
    await hass.async_block_till_done()

    await hass.services.async_call(
        DOMAIN, "speak", {"message": "hi"}, blocking=True, return_response=True
    )
    await hass.async_block_till_done()

    assert len(volume_calls) == 1
    assert volume_calls[0].data["entity_id"] == "media_player.speaker_one"


async def test_slider_restored_after_reload(hass: HomeAssistant, setup_entry) -> None:
    await hass.services.async_call(
        "number",
        "set_value",
        {"entity_id": "number.tts_broadcast_volume", "value": 80},
        blocking=True,
    )
    await hass.async_block_till_done()

    await hass.config_entries.async_reload(setup_entry.entry_id)
    await hass.async_block_till_done()

    assert setup_entry.runtime_data.volume == 80


async def test_speak_volume_skip(hass: HomeAssistant, setup_entry) -> None:
    volume_calls = async_mock_service(hass, "media_player", "volume_set")
    async_mock_service(hass, "tts", "speak")

    await hass.services.async_call(
        DOMAIN,
        "speak",
        {"message": "hi", "speakers": ["media_player.speaker_two"]},
        blocking=True,
        return_response=True,
    )
    await hass.async_block_till_done()

    assert len(volume_calls) == 0


async def test_speak_one_failing(hass: HomeAssistant, setup_entry) -> None:
    def raise_for_speaker(call):
        if call.data["entity_id"] == "media_player.speaker_one":
            raise RuntimeError("boom")

    async_mock_service(
        hass, "media_player", "volume_set", raise_exception=RuntimeError("boom")
    )
    async_mock_service(hass, "tts", "speak")

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

    # Volume failure should not block TTS
    assert set(result["played"]) == {
        "media_player.speaker_one",
        "media_player.speaker_two",
    }


async def test_speak_one_speaker_failing_does_not_stop_others(
    hass: HomeAssistant, setup_entry
) -> None:
    async_mock_service(hass, "media_player", "volume_set")
    speak_calls = []

    async def _tts_speak(call) -> None:
        speak_calls.append(call)
        if call.data.get("media_player_entity_id") == ["media_player.speaker_one"]:
            raise RuntimeError("boom")

    hass.services.async_register("tts", "speak", _tts_speak)

    for eid in hass.states.async_entity_ids("switch"):
        if "tts_broadcast" in eid:
            await hass.services.async_call(
                "switch", "turn_on", {"entity_id": eid}, blocking=True
            )
    await hass.async_block_till_done()

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

    assert result["played"] == ["media_player.speaker_two"]
    assert result["failed"] == ["media_player.speaker_one"]
    assert result["errors"]["media_player.speaker_one"] == "RuntimeError: boom"


async def test_speak_none_selected(hass: HomeAssistant, setup_entry) -> None:
    async_mock_service(hass, "media_player", "volume_set")
    async_mock_service(hass, "tts", "speak")

    # turn all switches off
    for eid in hass.states.async_entity_ids("switch"):
        if "tts_broadcast" in eid:
            await hass.services.async_call(
                "switch", "turn_off", {"entity_id": eid}, blocking=True
            )
    await hass.async_block_till_done()

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN, "speak", {"message": "hi"}, blocking=True, return_response=True
        )


async def test_speak_empty_message(hass: HomeAssistant, setup_entry) -> None:
    async_mock_service(hass, "media_player", "volume_set")
    async_mock_service(hass, "tts", "speak")

    with pytest.raises(HomeAssistantError):
        await hass.services.async_call(
            DOMAIN, "speak", {"message": "   "}, blocking=True, return_response=True
        )


async def test_speak_unavailable_speaker(hass: HomeAssistant, setup_entry) -> None:
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

    assert result["played"] == ["media_player.speaker_two"]
    assert result["skipped"] == ["media_player.speaker_one"]
    assert speak_calls[0].data["media_player_entity_id"] == ["media_player.speaker_two"]


async def test_stop(hass: HomeAssistant, setup_entry) -> None:
    stop_calls = async_mock_service(hass, "media_player", "media_stop")

    result = await hass.services.async_call(
        DOMAIN,
        "stop",
        {"speakers": ["media_player.speaker_one"]},
        blocking=True,
        return_response=True,
    )
    await hass.async_block_till_done()

    assert result["failed"] == []
    assert len(stop_calls) == 1
