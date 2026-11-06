"""Config flow for TTS Broadcast."""

from __future__ import annotations

import probatio
from homeassistant.config_entries import ConfigFlow, OptionsFlowWithReload
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers import selector

from .const import (
    CONF_LANGUAGE,
    CONF_NO_VOLUME_SPEAKERS,
    CONF_OPTIONS,
    CONF_SPEAKERS,
    CONF_TTS_ENTITY,
    CONF_VOLUME,
    DEFAULT_VOLUME,
    DOMAIN,
)

STEP_USER_DATA_SCHEMA = probatio.Schema(
    {
        probatio.Required(CONF_TTS_ENTITY): selector.EntitySelector({"domain": "tts"}),
        probatio.Required(CONF_SPEAKERS): selector.EntitySelector(
            {"domain": "media_player", "multiple": True}
        ),
        probatio.Optional(CONF_NO_VOLUME_SPEAKERS, default=[]): selector.EntitySelector(
            {"domain": "media_player", "multiple": True}
        ),
        probatio.Optional(CONF_VOLUME, default=DEFAULT_VOLUME): selector.NumberSelector(
            {"min": 0, "max": 100, "step": 1, "mode": "slider"}
        ),
        probatio.Optional(CONF_LANGUAGE, default=""): selector.TextSelector(),
        probatio.Optional(CONF_OPTIONS, default={}): selector.ObjectSelector(),
    }
)


def _validate_input(hass: HomeAssistant, user_input: dict) -> dict[str, str]:
    errors: dict[str, str] = {}
    tts_entity = user_input.get(CONF_TTS_ENTITY)
    if not tts_entity or hass.states.get(tts_entity) is None:
        errors[CONF_TTS_ENTITY] = "tts_entity_not_found"
    speakers = user_input.get(CONF_SPEAKERS) or []
    if not speakers:
        errors[CONF_SPEAKERS] = "no_speakers"
    no_volume = user_input.get(CONF_NO_VOLUME_SPEAKERS) or []
    if any(item not in speakers for item in no_volume):
        errors[CONF_NO_VOLUME_SPEAKERS] = "invalid_subset"
    return errors


class TTSBroadcastConfigFlow(ConfigFlow, domain=DOMAIN):
    """Handle a config flow for TTS Broadcast."""

    VERSION = 1

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return TTSBroadcastOptionsFlow(config_entry)

    async def async_step_user(self, user_input=None):
        errors = {}
        if user_input is not None:
            errors = _validate_input(self.hass, user_input)
            if not errors:
                await self.async_set_unique_id(DOMAIN)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title="TTS Broadcast",
                    data={},
                    options=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=STEP_USER_DATA_SCHEMA,
            errors=errors,
        )


class TTSBroadcastOptionsFlow(OptionsFlowWithReload):
    """Handle options flow."""

    async def async_step_init(self, user_input=None):
        errors = {}
        if user_input is not None:
            errors = _validate_input(self.hass, user_input)
            if not errors:
                return self.async_create_entry(title="", data=user_input)

        schema = self.add_suggested_values_to_schema(
            STEP_USER_DATA_SCHEMA, self.config_entry.options
        )
        return self.async_show_form(
            step_id="init",
            data_schema=schema,
            errors=errors,
        )
