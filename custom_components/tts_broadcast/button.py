"""Button platform for TTS Broadcast."""

from __future__ import annotations

from homeassistant.components.button import ButtonEntity
from homeassistant.core import HomeAssistant
from homeassistant.helpers.device_registry import DeviceInfo
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from . import TTSBroadcastConfigEntry
from .const import DOMAIN, SERVICE_SPEAK, SERVICE_STOP


async def async_setup_entry(
    hass: HomeAssistant,
    entry: TTSBroadcastConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up button entities."""
    async_add_entities(
        [
            TTSBroadcastSpeakButton(hass, entry),
            TTSBroadcastStopButton(hass, entry),
            TTSBroadcastSelectAllButton(hass, entry),
            TTSBroadcastSelectNoneButton(hass, entry),
        ]
    )


class _BaseButton(ButtonEntity):
    _attr_has_entity_name = True

    def __init__(
        self, hass: HomeAssistant, entry: TTSBroadcastConfigEntry, key: str
    ) -> None:
        self.hass = hass
        self._entry = entry
        self._attr_unique_id = f"{entry.entry_id}_{key}"
        self._attr_translation_key = key
        self._attr_device_info = DeviceInfo(
            identifiers={(DOMAIN, entry.entry_id)},
            name="TTS Broadcast",
        )


class TTSBroadcastSpeakButton(_BaseButton):
    def __init__(self, hass, entry) -> None:
        super().__init__(hass, entry, "speak")

    async def async_press(self) -> None:
        text_entity = _find_text_entity(self.hass, self._entry)
        message = ""
        if text_entity is not None:
            state = self.hass.states.get(text_entity)
            if state is not None:
                message = state.state or ""
        if not message.strip():
            return
        await self.hass.services.async_call(
            DOMAIN,
            SERVICE_SPEAK,
            {"message": message},
            blocking=True,
        )


class TTSBroadcastStopButton(_BaseButton):
    def __init__(self, hass, entry) -> None:
        super().__init__(hass, entry, "stop")

    async def async_press(self) -> None:
        await self.hass.services.async_call(
            DOMAIN,
            SERVICE_STOP,
            {},
            blocking=True,
        )


class TTSBroadcastSelectAllButton(_BaseButton):
    def __init__(self, hass, entry) -> None:
        super().__init__(hass, entry, "select_all")

    async def async_press(self) -> None:
        for entity_id in _switch_entity_ids(self.hass, self._entry):
            await self.hass.services.async_call(
                "switch",
                "turn_on",
                {"entity_id": entity_id},
                blocking=True,
            )


class TTSBroadcastSelectNoneButton(_BaseButton):
    def __init__(self, hass, entry) -> None:
        super().__init__(hass, entry, "select_none")

    async def async_press(self) -> None:
        for entity_id in _switch_entity_ids(self.hass, self._entry):
            await self.hass.services.async_call(
                "switch",
                "turn_off",
                {"entity_id": entity_id},
                blocking=True,
            )


def _switch_entity_ids(
    hass: HomeAssistant, entry: TTSBroadcastConfigEntry
) -> list[str]:
    runtime = entry.runtime_data
    return list(runtime.switch_entity_ids.values())


def _find_text_entity(
    hass: HomeAssistant, entry: TTSBroadcastConfigEntry
) -> str | None:
    # Find the text entity belonging to this entry via entity registry.
    from homeassistant.helpers import entity_registry as er

    registry = er.async_get(hass)
    for entity in registry.entities.values():
        if entity.config_entry_id == entry.entry_id and entity.domain == "text":
            return entity.entity_id
    return None
