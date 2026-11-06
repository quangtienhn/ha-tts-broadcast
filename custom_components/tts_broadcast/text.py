"""Text platform for TTS Broadcast."""

from __future__ import annotations

from homeassistant.components.text import RestoreText as TextEntity
from homeassistant.components.text import TextMode
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TTSBroadcastConfigEntry
from .const import DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TTSBroadcastConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up text entities."""
    async_add_entities([TTSBroadcastMessageText(hass, entry)])


class TTSBroadcastMessageText(TextEntity):
    """Message input."""

    _attr_has_entity_name = True
    _attr_translation_key = "message"
    _attr_native_min = 0
    _attr_native_max = 255
    _attr_mode = TextMode.TEXT

    def __init__(self, hass: HomeAssistant, entry: TTSBroadcastConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_message"
        self._attr_native_value = ""
        # Restore from config is not needed; entity restore handles it.
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="TTS Broadcast",
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_data = await self.async_get_last_text_data()
        if last_data is not None and last_data.native_value is not None:
            self._attr_native_value = last_data.native_value

    async def async_set_value(self, value: str) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()

    @property
    def native_value(self) -> str | None:
        return self._attr_native_value
