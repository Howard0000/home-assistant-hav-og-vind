from __future__ import annotations

import logging
from datetime import timedelta

from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME, Platform
from homeassistant.core import HomeAssistant
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import HavOgVindApi
from .const import DEFAULT_SCAN_MINUTES, DOMAIN

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SELECT]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    # Use Home Assistant-managed aiohttp session
    session = async_get_clientsession(hass)
    api = HavOgVindApi(session)

    lat = float(entry.data.get(CONF_LATITUDE, hass.config.latitude))
    lon = float(entry.data.get(CONF_LONGITUDE, hass.config.longitude))
    name = entry.data.get(CONF_NAME) or "Hav og vind"
    scan_minutes = entry.options.get("scan_interval_minutes", DEFAULT_SCAN_MINUTES)

    async def _async_update():
        try:
            return await api.fetch(lat, lon, name=name)
        except Exception as e:
            raise UpdateFailed(str(e)) from e

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"hav_og_vind_{entry.entry_id}",
        update_method=_async_update,
        update_interval=timedelta(minutes=scan_minutes),
    )

    # NEW: Apply updated options without restart/reload
    async def _async_update_options(hass: HomeAssistant, updated_entry: ConfigEntry) -> None:
        scan_minutes_new = updated_entry.options.get(
            "scan_interval_minutes", DEFAULT_SCAN_MINUTES
        )
        coordinator.update_interval = timedelta(minutes=scan_minutes_new)
        await coordinator.async_request_refresh()

    entry.async_on_unload(entry.add_update_listener(_async_update_options))

    await coordinator.async_config_entry_first_refresh()

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "lat": lat,
        "lon": lon,
        "name": name,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        hass.data.get(DOMAIN, {}).pop(entry.entry_id, None)
    return unload_ok
