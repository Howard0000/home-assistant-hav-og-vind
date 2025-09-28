# custom_components/hav_og_vind/__init__.py
from __future__ import annotations

from datetime import timedelta
import logging
import socket
from aiohttp import ClientSession, TCPConnector

from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.const import CONF_LATITUDE, CONF_LONGITUDE, Platform, EVENT_HOMEASSISTANT_STOP
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .const import DOMAIN, DEFAULT_SCAN_MINUTES
from .api import HavvarselApi

_LOGGER = logging.getLogger(__name__)
PLATFORMS: list[Platform] = [Platform.SENSOR]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Sett opp integrasjonen basert på en konfigurasjonsentry."""
    # Bruk TCPConnector for å tvinge IPv4, dette kan løse nettverksproblemer
    connector = TCPConnector(family=socket.AF_INET)
    session = ClientSession(connector=connector)

    # Sørg for at sesjonen lukkes når Home Assistant stopper
    async def _on_stop(_):
        if not session.closed:
            await session.close()
    hass.bus.async_listen_once(EVENT_HOMEASSISTANT_STOP, _on_stop)

    api = HavvarselApi(session)
    # Hent breddegrad og lengdegrad fra konfigurasjon, eller bruk systemets standard
    lat = float(entry.data.get(CONF_LATITUDE, hass.config.latitude))
    lon = float(entry.data.get(CONF_LONGITUDE, hass.config.longitude))

    # Definer oppdateringsmetoden for koordinator
    async def _async_update():
        try:
            # Kall API-et for å hente data
            return await api.fetch(lat, lon)
        except Exception as e:
            # Kast UpdateFailed hvis det skjer en feil under henting
            raise UpdateFailed(str(e)) from e

    # Hent oppdateringsintervall fra opsjoner, ellers bruk standard
    scan_minutes = entry.options.get("scan_interval_minutes", DEFAULT_SCAN_MINUTES)
    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name=f"havvarsel_coordinator_{entry.entry_id}", # Unikt navn for koordinator
        update_method=_async_update,
        update_interval=timedelta(minutes=scan_minutes),
    )

    # Kjør første oppdatering med en gang integrasjonen legges til
    try:
        await coordinator.async_config_entry_first_refresh()
        _LOGGER.debug("Rådata fra koordinator: %s", coordinator.data)
    except Exception:
        # Hvis første oppdatering feiler, lukk sesjonen og kast feilen
        if not session.closed:
            await session.close()
        raise

    # Lagre data som koordinator, lokasjon og sesjon i hass.data
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = {
        "coordinator": coordinator,
        "lat": lat,
        "lon": lon,
        "session": session,
    }

    # Forward entry setup til sensor plattformen
    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)
    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Avlast integrasjonen og fjern dens data."""
    # Avlast sensor-plattformen
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    
    # Fjern data for denne entry_id fra hass.data
    data = hass.data.get(DOMAIN, {}).pop(entry.entry_id, {}) if unload_ok else {}
    
    # Lukk klient-sesjonen hvis den er åpen
    sess: ClientSession | None = data.get("session")
    if sess and not sess.closed:
        await sess.close()
        
    return unload_ok
