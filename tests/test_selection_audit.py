"""Characterization tests for speaker selection targeting.

These tests assert exactly which entity ids reach tts.speak and
media_player.volume_set in each scenario on the CURRENT code.
They do not fix anything; they only capture current behavior.
"""

from __future__ import annotations

from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import (
    MockConfigEntry,
    async_mock_service,
)

from custom_components.tts_broadcast.const import (
    DOMAIN,
)


async def _setup_and_turn_on(hass: HomeAssistant, entry: MockConfigEntry) -> None:
    entry.add_to_hass(hass)
    await hass.config_entries.async_setup(entry.entry_id)
    await hass.async_block_till_done()
    hass.states.async_set("media_player.speaker_one", "idle")
    hass.states.async_set("media_player.speaker_two", "idle")
    switches = hass.states.async_entity_ids("switch")
    if switches:
        await hass.services.async_call(
            "switch",
            "turn_on",
            {"entity_id": switches[0]},
            blocking=True,
        )
    await hass.async_block_till_done()


async def _speak(hass: HomeAssistant, speakers=None) -> dict:
    data: dict = {"message": "hello"}
    if speakers is not None:
        data["speakers"] = speakers
    result = await hass.services.async_call(
        DOMAIN, "speak", data, blocking=True, return_response=True
    )
    await hass.async_block_till_done()
    return result


async def test_one_switch_on_only_one_speaker_spoken(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Exactly one switch ON -> exactly one tts.speak call with one speaker."""
    volume_calls = async_mock_service(hass, "media_player", "volume_set")
    speak_calls = async_mock_service(hass, "tts", "speak")

    await _setup_and_turn_on(hass, mock_config_entry)

    result = await _speak(hass)

    assert len(speak_calls) == 1, speak_calls
    assert speak_calls[0].data["media_player_entity_id"] == ["media_player.speaker_one"]
    assert len(volume_calls) == 1
    assert volume_calls[0].data["entity_id"] == "media_player.speaker_one"
    assert result["played"] == ["media_player.speaker_one"]
    assert result["skipped"] == []
    assert result["failed"] == []
    assert result["errors"] == {}


async def test_switch_states_snapshot_in_result(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """The response should reflect which switches were ON vs resolved."""
    async_mock_service(hass, "tts", "speak")
    async_mock_service(hass, "media_player", "volume_set")

    await _setup_and_turn_on(hass, mock_config_entry)

    result = await _speak(hass)

    assert result["played"] == ["media_player.speaker_one"]
    assert result["skipped"] == []


async def test_explicit_speakers_arg_uses_only_requested(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """speakers=[speaker_two] -> only speaker_two is spoken, regardless of switch."""
    speak_calls = async_mock_service(hass, "tts", "speak")
    async_mock_service(hass, "media_player", "volume_set")

    await _setup_and_turn_on(hass, mock_config_entry)

    result = await _speak(hass, speakers=["media_player.speaker_two"])

    assert len(speak_calls) == 1
    assert speak_calls[0].data["media_player_entity_id"] == ["media_player.speaker_two"]
    assert result["played"] == ["media_player.speaker_two"]


async def test_unavailable_speaker_skipped(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Switch ON but media_player unavailable -> speaker skipped, not played."""
    speak_calls = async_mock_service(hass, "tts", "speak")
    async_mock_service(hass, "media_player", "volume_set")

    await _setup_and_turn_on(hass, mock_config_entry)
    # turn on BOTH switches first
    switches = hass.states.async_entity_ids("switch")
    for sw in switches:
        await hass.services.async_call(
            "switch", "turn_on", {"entity_id": sw}, blocking=True
        )
    await hass.async_block_till_done()

    # verify both switches are on
    for sw in switches:
        st = hass.states.get(sw)
        assert st is not None and st.state == "on", (sw, st.state if st else None)

    hass.states.async_set("media_player.speaker_one", "unavailable")
    await hass.async_block_till_done()

    result = await _speak(hass)

    assert result["played"] == ["media_player.speaker_two"]
    assert result["skipped"] == ["media_player.speaker_one"]
    assert len(speak_calls) == 1
    assert speak_calls[0].data["media_player_entity_id"] == ["media_player.speaker_two"]


async def test_restart_simulation_restore_state(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Restart simulation: after reload, only one switch ON
    -> only that speaker spoken."""
    speak_calls = async_mock_service(hass, "tts", "speak")
    async_mock_service(hass, "media_player", "volume_set")

    # First setup: turn on speaker_one switch
    await _setup_and_turn_on(hass, mock_config_entry)

    # Simulate unload (restart)
    await hass.config_entries.async_unload(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    # Re-setup (restart): switch entities re-created
    await hass.config_entries.async_setup(mock_config_entry.entry_id)
    await hass.async_block_till_done()

    hass.states.async_set("media_player.speaker_one", "idle")
    hass.states.async_set("media_player.speaker_two", "idle")

    # Exactly one switch ON (as if restored or re-selected)
    switches = hass.states.async_entity_ids("switch")
    for sw in switches:
        if "speaker_one" in sw:
            await hass.services.async_call(
                "switch", "turn_on", {"entity_id": sw}, blocking=True
            )
        elif "speaker_two" in sw:
            await hass.services.async_call(
                "switch", "turn_off", {"entity_id": sw}, blocking=True
            )
    await hass.async_block_till_done()

    result = await _speak(hass)

    assert len(speak_calls) == 1
    assert speak_calls[0].data["media_player_entity_id"] == ["media_player.speaker_one"]
    assert result["played"] == ["media_player.speaker_one"]


async def test_select_all_select_none_then_one_switch(
    hass: HomeAssistant, mock_config_entry: MockConfigEntry
) -> None:
    """Select all -> Select none -> turn on one -> speak: only that one spoken."""
    speak_calls = async_mock_service(hass, "tts", "speak")
    async_mock_service(hass, "media_player", "volume_set")

    await _setup_and_turn_on(hass, mock_config_entry)

    def _switch_ids() -> list[str]:
        return [
            e
            for e in hass.states.async_entity_ids("switch")
            if e.startswith("switch.tts_broadcast_media_player_")
        ]

    # turn both on (select all)
    for sw in _switch_ids():
        await hass.services.async_call(
            "switch", "turn_on", {"entity_id": sw}, blocking=True
        )
    await hass.async_block_till_done()

    # turn both off (select none)
    for sw in _switch_ids():
        await hass.services.async_call(
            "switch", "turn_off", {"entity_id": sw}, blocking=True
        )
    await hass.async_block_till_done()

    # turn on exactly one
    for sw in _switch_ids():
        if "speaker_one" in sw:
            await hass.services.async_call(
                "switch", "turn_on", {"entity_id": sw}, blocking=True
            )
    await hass.async_block_till_done()

    result = await _speak(hass)

    assert len(speak_calls) == 1
    assert speak_calls[0].data["media_player_entity_id"] == ["media_player.speaker_one"]
    assert result["played"] == ["media_player.speaker_one"]
