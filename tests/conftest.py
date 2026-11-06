"""Shared test fixtures."""

from __future__ import annotations

import pytest
from homeassistant.core import HomeAssistant
from pytest_homeassistant_custom_component.common import MockConfigEntry

from custom_components.tts_broadcast.const import DOMAIN


@pytest.fixture(autouse=True)
def auto_enable_custom_integrations(enable_custom_integrations):
    """Enable custom integrations for all tests."""
    return


@pytest.fixture
def mock_config_entry(hass: HomeAssistant):
    return MockConfigEntry(
        domain=DOMAIN,
        data={},
        options={
            "tts_entity": "tts.wyoming_vietnamese",
            "speakers": [
                "media_player.speaker_one",
                "media_player.speaker_two",
            ],
            "no_volume_speakers": ["media_player.speaker_two"],
            "volume": 50,
            "language": "",
            "options": {},
        },
        entry_id="test_entry",
        title="TTS Broadcast",
    )
