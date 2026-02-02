from __future__ import annotations

from datetime import timedelta
from typing import Any

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.helpers.storage import Store
from homeassistant.components.select import SelectEntity

from .const import DOMAIN


_STORAGE_VERSION = 1
_STORAGE_KEY = f"{DOMAIN}.prefs"
_ACTIVE_KEY = "active_station"


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    """Set up the Hav og vind select entities.

    Integrasjonen kan ha mange config entries (én per lokasjon), men vi ønsker kun
    én global dropdown for "aktiv stasjon". Derfor oppretter vi entityen kun én gang.
    """
    domain_data: dict[str, Any] = hass.data.setdefault(DOMAIN, {})
    global_data: dict[str, Any] = domain_data.setdefault("_global", {})

    if global_data.get("active_station_select_added"):
        return

    async_add_entities([HavOgVindActiveStationSelect(hass)])
    global_data["active_station_select_added"] = True


class HavOgVindActiveStationSelect(SelectEntity):
    """Dropdown for å velge aktiv stasjon (globalt i integrasjonen)."""

    _attr_has_entity_name = True
    _attr_name = "Aktiv stasjon"
    _attr_unique_id = "hav_og_vind_active_station"
    _attr_icon = "mdi:map-marker"
    _attr_entity_category = EntityCategory.CONFIG

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._store: Store[dict[str, Any]] = Store(hass, _STORAGE_VERSION, _STORAGE_KEY)
        self._active: str | None = None
        self._unsub = None

    @property
    def options(self) -> list[str]:
        return self._stations()

    @property
    def current_option(self) -> str | None:
        # Sørg for at aktiv stasjon alltid er gyldig hvis mulig
        stations = self._stations()
        if self._active in stations:
            return self._active
        if stations:
            return stations[0]
        return None

    async def async_select_option(self, option: str) -> None:
        stations = self._stations()
        if option not in stations:
            return
        self._active = option
        await self._store.async_save({_ACTIVE_KEY: option})
        self.async_write_ha_state()


    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, "global")},
            "name": "Hav og vind",
            "manufacturer": "MET Norway / Kartverket / Havvarsel",
            "configuration_url": "https://api.met.no/",
        }

    def _stations(self) -> list[str]:
        entries = self._hass.config_entries.async_entries(DOMAIN)
        names = [e.title for e in entries if e.title]
        uniq = list(dict.fromkeys(names))
        uniq.sort()
        return uniq

    async def async_added_to_hass(self) -> None:
        # Last inn lagret valgt stasjon
        data = await self._store.async_load() or {}
        saved = data.get(_ACTIVE_KEY)
        if isinstance(saved, str) and saved:
            self._active = saved

        # Hvis lagret verdi ikke finnes lenger, fall tilbake til første
        if self._active not in self._stations():
            self._active = None

        # Oppdater jevnlig for å fange opp nye/slettede stasjoner uten restart
        self._unsub = async_track_time_interval(
            self._hass, lambda _now: self.schedule_update_ha_state(), timedelta(seconds=30)
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None
