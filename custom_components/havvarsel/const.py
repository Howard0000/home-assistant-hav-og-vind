# custom_components/hav_og_vind/config_flow.py
from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME
from homeassistant.core import HomeAssistant

from .const import DOMAIN, DEFAULT_SCAN_MINUTES


class HavvarselOptionsFlow(config_entries.OptionsFlow):
    """Håndterer opsjonsflyt for integrasjonen."""
    def __init__(self, config_entry: config_entries.ConfigEntry) -> None:
        self.config_entry = config_entry

    async def async_step_init(self, user_input=None):
        """Initialiserer opsjonsflyten."""
        if user_input is not None:
            # Brukeren har lagret nye innstillinger
            return self.async_create_entry(title="", data=user_input)

        # Hent gjeldende verdi for oppdateringsintervall, eller bruk standard
        current = self.config_entry.options.get(
            "scan_interval_minutes", DEFAULT_SCAN_MINUTES
        )
        
        # Definer skjema for opsjonsinnstillinger
        schema = vol.Schema(
            {
                vol.Required(
                    "scan_interval_minutes", default=current
                ): vol.All(int, vol.Range(min=5, max=360)) # Valider at det er et tall mellom 5 og 360
            }
        )
        return self.async_show_form(step_id="init", data_schema=schema)


class HavvarselConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Håndterer konfigurasjonsflyt for integrasjonen."""
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Håndterer brukerinput i konfigurasjonsflyten."""
        if user_input is not None:
            # Brukeren har gitt navn og lokasjon
            name = user_input.get(CONF_NAME, "Hav og vind")
            return self.async_create_entry(title=name, data=user_input)

        hass: HomeAssistant = self.hass
        # Definer skjema for lokasjonsinnstillinger
        schema = vol.Schema(
            {
                vol.Optional(CONF_NAME, default="Hav og vind"): str,  # <-- nytt felt
                vol.Required(
                    CONF_LATITUDE, default=hass.config.latitude
                ): vol.Coerce(float), # Sørg for at verdien blir et flyttall
                vol.Required(
                    CONF_LONGITUDE, default=hass.config.longitude
                ): vol.Coerce(float), # Sørg for at verdien blir et flyttall
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_get_options_flow(self, config_entry):
        """Returnerer opsjonsflyten for denne konfigurasjonsentryen."""
        return HavvarselOptionsFlow(config_entry)
