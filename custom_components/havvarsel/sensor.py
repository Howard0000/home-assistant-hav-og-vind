from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfTemperature, ATTR_ATTRIBUTION
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, CoordinatorEntity
from homeassistant.helpers.aiohttp_client import async_get_clientsession

from .const import DOMAIN, DEFAULT_SCAN_INTERVAL, DEFAULT_FORECAST_HOURS, USER_AGENT
from .api import HavvarselApi

ATTRIBUTION = "Data fra Havvarsel (IMR)"

@dataclass
class Cfg:
    name: str
    lat: float
    lon: float
    scan: int
    forecast_hours: int

def _pick(d: dict[str, Any], *keys, default=None):
    for k in keys:
        if k in d:
            return d[k]
    lower = {k.lower(): v for k, v in d.items()}
    for k in keys:
        v = lower.get(k.lower())
        if v is not None:
            return v
    return default

def _extract_series(payload: Any) -> list[dict]:
    if not payload:
        return []
    if isinstance(payload, dict):
        for k in ("data", "series", "projection", "results"):
            if isinstance(payload.get(k), list):
                payload = payload[k]
                break
    if not isinstance(payload, list):
        return []
    out: list[dict] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        t = _pick(item, "time", "timestamp", "t")
        temp = _pick(item, "temperature", "temp", "T")
        sal = _pick(item, "salinity", "psu", "S")
        out.append({"time": t, "temperature": temp, "salinity": sal})
    return out

class _Base(CoordinatorEntity, SensorEntity):
    _attr_icon = "mdi:waves"

    def __init__(self, coordinator, cfg: Cfg):
        super().__init__(coordinator)
        self._cfg = cfg

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs = {"lat": self._cfg.lat, "lon": self._cfg.lon, ATTR_ATTRIBUTION: ATTRIBUTION}
        series: list[dict] = self.coordinator.data or []
        if series:
            attrs["forecast_series_temp"] = [
                {"time": p.get("time"), "value": p.get("temperature")}
                for p in series if p.get("temperature") is not None
            ][: self._cfg.forecast_hours]
            attrs["forecast_series_sal"] = [
                {"time": p.get("time"), "value": p.get("salinity")}
                for p in series if p.get("salinity") is not None
            ][: self._cfg.forecast_hours]
            attrs["model_time"] = series[0].get("time")
        return attrs

class TempSensor(_Base):
    _attr_has_entity_name = True
    _attr_device_class = "temperature"
    _attr_native_unit_of_measurement = UnitOfTemperature.CELSIUS

    def __init__(self, coordinator, cfg: Cfg):
        super().__init__(coordinator, cfg)
        self._attr_name = f"{cfg.name} sjøtemperatur"
        self._attr_unique_id = f"havvarsel_temp_{cfg.lat:.5f}_{cfg.lon:.5f}"

    @property
    def native_value(self) -> float | None:
        series: list[dict] = self.coordinator.data or []
        if not series:
            return None
        v = series[0].get("temperature")
        try:
            return None if v is None else float(v)
        except Exception:
            return None

class SalSensor(_Base):
    _attr_has_entity_name = True
    _attr_icon = "mdi:beaker"

    def __init__(self, coordinator, cfg: Cfg):
        super().__init__(coordinator, cfg)
        self._attr_name = f"{cfg.name} saltholdighet"
        self._attr_unique_id = f"havvarsel_sal_{cfg.lat:.5f}_{cfg.lon:.5f}"

    @property
    def native_unit_of_measurement(self) -> str | None:
        return "PSU"

    @property
    def native_value(self) -> float | None:
        series: list[dict] = self.coordinator.data or []
        if not series:
            return None
        v = series[0].get("salinity")
        try:
            return None if v is None else float(v)
        except Exception:
            return None

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    cfg = Cfg(
        name=entry.data["name"],
        lat=float(entry.data["lat"]),
        lon=float(entry.data["lon"]),
        scan=int(entry.options.get("scan_interval", entry.data.get("scan_interval", DEFAULT_SCAN_INTERVAL))),
        forecast_hours=int(entry.options.get("forecast_hours", entry.data.get("forecast_hours", DEFAULT_FORECAST_HOURS))),
    )

    session = async_get_clientsession(hass)
    api = HavvarselApi(session, USER_AGENT)

    async def _update() -> list[dict] | None:
        data = await api.fetch_projection(cfg.lon, cfg.lat)
        return _extract_series(data)

    coordinator = DataUpdateCoordinator(
        hass,
        logger=hass.logger,
        name=f"havvarsel_{cfg.lat}_{cfg.lon}",
        update_method=_update,
        update_interval=timedelta(seconds=cfg.scan),
    )
    await coordinator.async_config_entry_first_refresh()

    async_add_entities([TempSensor(coordinator, cfg), SalSensor(coordinator, cfg)])
