"""Number platform for TTS Broadcast."""

from __future__ import annotations

from homeassistant.components.number import NumberMode
from homeassistant.components.number import RestoreNumber as NumberEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TTSBroadcastConfigEntry
from .const import CONF_VOLUME, DEFAULT_VOLUME, DOMAIN


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TTSBroadcastConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up number entities."""
    async_add_entities([TTSBroadcastVolumeNumber(hass, entry)])


class TTSBroadcastVolumeNumber(NumberEntity):
    """Shared volume slider (single source of truth for announcement volume)."""

    _attr_has_entity_name = True
    _attr_translation_key = "volume"
    _attr_native_min_value = 0
    _attr_native_max_value = 100
    _attr_native_step = 1
    _attr_mode = NumberMode.SLIDER

    def __init__(self, hass: HomeAssistant, entry: TTSBroadcastConfigEntry) -> None:
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_volume"
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="TTS Broadcast",
        )

    async def async_added_to_hass(self) -> None:
        await super().async_added_to_hass()
        last_data = await self.async_get_last_number_data()
        if last_data is not None and last_data.native_value is not None:
            self._attr_native_value = last_data.native_value
        else:
            self._attr_native_value = float(
                self._entry.options.get(CONF_VOLUME, DEFAULT_VOLUME)
            )
        # Single source of truth lives in runtime data.
        self._entry.runtime_data.volume = float(self._attr_native_value)

    async def async_set_native_value(self, value: float) -> None:
        self._attr_native_value = value
        self.async_write_ha_state()
        # Keep runtime data in sync so announcements use the slider value.
        self._entry.runtime_data.volume = float(value)

    @property
    def native_value(self) -> float | None:
        return self._attr_native_value
