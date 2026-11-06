"""Switch platform for TTS Broadcast."""

from __future__ import annotations

from typing import Any

from homeassistant.components.switch import SwitchEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.restore_state import RestoreEntity

from . import TTSBroadcastConfigEntry
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TTSBroadcastConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up switch entities."""
    config = {**entry.data, **entry.options}
    speakers = config.get("speakers", [])

    entities = [TTSBroadcastSpeakerSwitch(hass, entry, speaker) for speaker in speakers]
    async_add_entities(entities)


class TTSBroadcastSpeakerSwitch(SwitchEntity, RestoreEntity):
    """Switch selecting a speaker."""

    _attr_has_entity_name = True

    def __init__(
        self, hass: HomeAssistant, entry: TTSBroadcastConfigEntry, speaker: str
    ) -> None:
        self.hass = hass
        self._entry = entry
        self.speaker = speaker
        self._attr_unique_id = f"{entry.entry_id}_switch_{speaker}"
        self._attr_is_on = False
        self._attr_name = _friendly_name(hass, speaker)
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="TTS Broadcast",
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_state = await self.async_get_last_state()
        if last_state is not None and last_state.state not in (
            "unavailable",
            "unknown",
        ):
            self._attr_is_on = last_state.state == "on"
        # Update runtime mapping with real entity id.
        self._entry.runtime_data.switch_entity_ids[self.speaker] = self.entity_id

    async def async_turn_on(self, **kwargs: Any) -> None:
        self._attr_is_on = True
        self.async_write_ha_state()

    async def async_turn_off(self, **kwargs: Any) -> None:
        self._attr_is_on = False
        self.async_write_ha_state()

    @property
    def is_on(self) -> bool | None:
        return self._attr_is_on


def _friendly_name(hass: HomeAssistant, entity_id: str) -> str:
    state = hass.states.get(entity_id)
    if state is not None and state.attributes.get("friendly_name"):
        return str(state.attributes["friendly_name"])
    return entity_id
