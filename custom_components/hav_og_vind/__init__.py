from __future__ import annotations

import logging
import socket
from datetime import timedelta
from aiohttp import ClientSession, TCPConnector

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import (
    CONF_LATITUDE, CONF_LONGITUDE, CONF_NAME, Platform, EVENT_HOMEASSISTANT_STOP
)
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import (
    DOMAIN, DEFAULT_SCAN_MINUTES,
)
from .api import HavOgVindApi

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.SENSOR, Platform.SELECT]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    connector = TCPConnector(family=socket.AF_INET)
    session = ClientSession(connector=connector)

    async def _on_stop(_):
        if not session.closed:
            await session.close()
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _on_stop)

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

    try:
        await coordinator.async_config_entry_first_refresh()
    except Exception:
        if not session.closed:
            await session.close()
        raise

    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "session": session,
        "lat": lat,
        "lon": lon,
        "name": name,
    }

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    data = hass.data.get(DOMAIN, {}).pop(entry.entry_id, {}) if unload_ok else {}
    sess: ClientSession | None = data.get("session")
    if sess and not sess.closed:
        await sess.close()
    return unload_ok