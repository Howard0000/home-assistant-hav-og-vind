from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult
from homeassistant.core import callback

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, DEFAULT_FORECAST_HOURS

class HavvarselConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    VERSION = 1

    async def async_step_user(self, user_input=None) -> FlowResult:
        errors = {}
        if user_input is not None:
            try:
                name = str(user_input["name"]).strip()
                lat = float(user_input["lat"])
                lon = float(user_input["lon"])
                scan = int(user_input.get("scan_interval", DEFAULT_SCAN_INTERVAL))
                fh   = int(user_input.get("forecast_hours", DEFAULT_FORECAST_HOURS))
            except Exception:
                errors["base"] = "invalid_input"
            else:
                unique = f"{lat:.5f}_{lon:.5f}"
                await self.async_set_unique_id(unique)
                self._abort_if_unique_id_configured()
                return self.async_create_entry(title=name, data={
                    "name": name, "lat": lat, "lon": lon,
                    "scan_interval": scan, "forecast_hours": fh
                })

        data_schema = vol.Schema({
            vol.Required("name", default="Bergen"): str,
            vol.Required("lat", default=60.39299): float,
            vol.Required("lon", default=5.32415): float,
            vol.Optional("scan_interval", default=DEFAULT_SCAN_INTERVAL): int,
            vol.Optional("forecast_hours", default=DEFAULT_FORECAST_HOURS): int,
        })
        return self.async_show_form(step_id="user", data_schema=data_schema, errors=errors)

    @callback
    def async_get_options_flow(self, config_entry):
        return HavvarselOptionsFlow(config_entry)

class HavvarselOptionsFlow(config_entries.OptionsFlow):
    def __init__(self, entry):
        self._entry = entry

    async def async_step_init(self, user_input=None):
        if user_input is not None:
            return self.async_create_entry(title="", data=user_input)

        data_schema = vol.Schema({
            vol.Required("scan_interval", default=self._entry.options.get("scan_interval", self._entry.data.get("scan_interval", DEFAULT_SCAN_INTERVAL))): int,
            vol.Required("forecast_hours", default=self._entry.options.get("forecast_hours", self._entry.data.get("forecast_hours", DEFAULT_FORECAST_HOURS))): int,
        })
        return self.async_show_form(step_id="init", data_schema=data_schema)
