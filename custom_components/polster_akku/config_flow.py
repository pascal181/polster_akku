from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.core import callback

from .const import CONF_NOTIFY, CONF_THRESHOLD, DEFAULT_THRESHOLD, DOMAIN


class PolsterAkkuFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None):
        if self._async_current_entries():
            return self.async_abort(reason="already_configured")
        if user_input is not None:
            return self.async_create_entry(title="Polster Akku", data=user_input)
        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_THRESHOLD, default=DEFAULT_THRESHOLD): vol.All(
                        vol.Coerce(int), vol.Range(min=5, max=50)
                    ),
                    vol.Optional(CONF_NOTIFY, default=""): str,
                }
            ),
        )

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return PolsterAkkuOptions(config_entry)


class PolsterAkkuOptions(config_entries.OptionsFlow):
    def __init__(self, entry: config_entries.ConfigEntry) -> None:
        self.entry = entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)
        data = {**self.entry.data, **self.entry.options}
        return self.async_show_form(
            step_id="init",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_THRESHOLD, default=data.get(CONF_THRESHOLD, DEFAULT_THRESHOLD)
                    ): vol.All(vol.Coerce(int), vol.Range(min=5, max=50)),
                    vol.Optional(CONF_NOTIFY, default=data.get(CONF_NOTIFY, "")): str,
                }
            ),
        )
