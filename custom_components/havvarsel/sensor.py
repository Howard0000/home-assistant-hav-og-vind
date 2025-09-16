from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.const import UnitOfTemperature, ATTR_ATTRIBUTION, UnitOfSpeed
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

def _series_to_attr(series: list[dict], key: str, limit: int) -> list[dict]:
    out = []
    for p in series:
        if key in p and p[key] is not None:
            out.append({"time": int(p["raw_time"]), "value": p[key]})
        if len(out) >= limit:
            break
    return out

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
        temp = await api.fetch_variable(cfg.lon, cfg.lat, "temperature")
        sal  = await api.fetch_variable(cfg.lon, cfg.lat, "salinity")
        merged = api.merge_series_by_time(temp, sal)
        return merged

    coordinator = DataUpdateCoordinator(
        hass,
        logger=hass.logger,
        name=f"havvarsel_{cfg.lat}_{cfg.lon}",
        update_method=_update,
        update_interval=timedelta(seconds=cfg.scan),
    )
    await coordinator.async_config_entry_first_refresh()

    entities: list[SensorEntity] = [TempSensor(coordinator, cfg), SalSensor(coordinator, cfg)]
    sample = coordinator.data[0] if coordinator.data else {}
    if any(k in sample for k in ("wind_length","wind_direction")):
        entities += [WindSpeedSensor(coordinator, cfg), WindDirSensor(coordinator, cfg)]
    if any(k in sample for k in ("current_length","current_direction")):
        entities += [CurrentSpeedSensor(coordinator, cfg), CurrentDirSensor(coordinator, cfg)]
    async_add_entities(entities)

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
            attrs["model_time"] = int(series[0].get("raw_time"))
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
    def native_value(self):
        s = self.coordinator.data or []
        return None if not s else s[0].get("temperature")
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs = super().extra_state_attributes
        s = self.coordinator.data or []
        attrs["forecast_series_temp"] = _series_to_attr(s, "temperature", self._cfg.forecast_hours)
        return attrs

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
    def native_value(self):
        s = self.coordinator.data or []
        return None if not s else s[0].get("salinity")
    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs = super().extra_state_attributes
        s = self.coordinator.data or []
        attrs["forecast_series_sal"] = _series_to_attr(s, "salinity", self._cfg.forecast_hours)
        return attrs

class WindSpeedSensor(_Base):
    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = UnitOfSpeed.METERS_PER_SECOND
    _attr_icon = "mdi:weather-windy"
    def __init__(self, coordinator, cfg: Cfg):
        super().__init__(coordinator, cfg)
        self._attr_name = f"{cfg.name} vindhastighet"
        self._attr_unique_id = f"havvarsel_windspeed_{cfg.lat:.5f}_{cfg.lon:.5f}"
    @property
    def native_value(self):
        s = self.coordinator.data or []
        return None if not s else s[0].get("wind_length")

class WindDirSensor(_Base):
    _attr_has_entity_name = True
    _attr_icon = "mdi:compass"
    def __init__(self, coordinator, cfg: Cfg):
        super().__init__(coordinator, cfg)
        self._attr_name = f"{cfg.name} vindretning"
        self._attr_unique_id = f"havvarsel_winddir_{cfg.lat:.5f}_{cfg.lon:.5f}"
    @property
    def native_value(self):
        s = self.coordinator.data or []
        return None if not s else s[0].get("wind_direction")

class CurrentSpeedSensor(_Base):
    _attr_has_entity_name = True
    _attr_native_unit_of_measurement = UnitOfSpeed.METERS_PER_SECOND
    _attr_icon = "mdi:wave"
    def __init__(self, coordinator, cfg: Cfg):
        super().__init__(coordinator, cfg)
        self._attr_name = f"{cfg.name} strømhastighet"
        self._attr_unique_id = f"havvarsel_currentspeed_{cfg.lat:.5f}_{cfg.lon:.5f}"
    @property
    def native_value(self):
        s = self.coordinator.data or []
        return None if not s else s[0].get("current_length")

class CurrentDirSensor(_Base):
    _attr_has_entity_name = True
    _attr_icon = "mdi:compass-outline"
    def __init__(self, coordinator, cfg: Cfg):
        super().__init__(coordinator, cfg)
        self._attr_name = f"{cfg.name} strømretning"
        self._attr_unique_id = f"havvarsel_currentdir_{cfg.lat:.5f}_{cfg.lon:.5f}"
    @property
    def native_value(self):
        s = self.coordinator.data or []
        return None if not s else s[0].get("current_direction")
