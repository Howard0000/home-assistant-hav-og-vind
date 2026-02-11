from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.helpers import config_validation as cv

from .const import DEFAULT_SCAN_MINUTES, DOMAIN

_LOGGER = logging.getLogger(__name__)


class HavOgVindOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        opts = self.config_entry.options
        schema = vol.Schema(
            {
                vol.Required(
                    "scan_interval_minutes",
                    default=opts.get("scan_interval_minutes", DEFAULT_SCAN_MINUTES),
                ): vol.All(vol.Coerce(int), vol.Range(min=5, max=360)),
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)


class HavOgVindConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors: dict[str, str] = {}

        if user_input is not None:
            name = user_input.get(CONF_NAME) or "Hav og vind"
            lat = user_input.get(CONF_LATITUDE)
            lon = user_input.get(CONF_LONGITUDE)

            if lat is None or lon is None:
                errors["base"] = "missing_coordinates"
            elif not isinstance(lat, (int, float)) or not isinstance(lon, (int, float)):
                # Skulle normalt ikke skje siden vi bruker cv.latitude/cv.longitude i schema,
                # men dette gjør den robust.
                errors["base"] = "invalid_coordinates"
            else:
                unique_id = f"{round(float(lat), 4)}_{round(float(lon), 4)}"
                await self.async_set_unique_id(unique_id)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=str(name), data=user_input)

        schema = vol.Schema(
            {
                vol.Required(CONF_NAME, default="Hav og vind"): str,
                vol.Required(CONF_LATITUDE, default=self.hass.config.latitude): cv.latitude,
                vol.Required(CONF_LONGITUDE, default=self.hass.config.longitude): cv.longitude,
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema, errors=errors)

    @staticmethod
    def async_get_options_flow(config_entry: config_entries.ConfigEntry):
        return HavOgVindOptionsFlow(config_entry)
