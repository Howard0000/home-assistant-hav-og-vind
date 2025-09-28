# custom_components/hav_og_vind/sensor.py
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import UnitOfTemperature, UnitOfSpeed, UnitOfLength
import logging

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)

@dataclass
class SensorDesc:
    """Beskriver en sensor."""
    key: str
    name: str
    unit: str | None = None
    device_class: SensorDeviceClass | None = None
    icon: str | None = None
    value_fn: Callable[[dict], Any] | None = None


def _deg_to_cardinal_16(deg: float | None) -> str | None:
    """Konverterer grader til et 16-punkts kompassretning."""
    if deg is None:
        return None
    labels = [
        "N", "NNØ", "NØ", "ØNØ", "Ø", "ØSØ", "SØ", "SSØ",
        "S", "SSV", "SV", "VSV", "V", "VNV", "NV", "NNV"
    ]
    try:
        deg_float = float(deg)
        i = int((deg_float % 360) / 22.5 + 0.5) % 16
        return labels[i]
    except (ValueError, TypeError, ZeroDivisionError):
        _LOGGER.error("Kunne ikke konvertere gradverdi '%s' til kardinal retning", deg)
        return None


SENSORS: list[SensorDesc] = [
    # Hav / strøm / bølger
    SensorDesc("sea_water_temperature", "Sjøtemperatur", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, "mdi:coolant-temperature"),
    SensorDesc("sea_water_speed", "Strømhastighet", UnitOfSpeed.METERS_PER_SECOND, None, "mdi:arrow-projectile"),
    SensorDesc(
        "sea_water_to_direction",
        "Strømmens retning (mot)",
        None,
        None,
        "mdi:compass-rose",
        value_fn=lambda data: _deg_to_cardinal_16(data.get("sea_water_to_direction")) if data and data.get("sea_water_to_direction") is not None else None
    ),
    SensorDesc("sea_surface_wave_height", "Signifikant bølgehøyde", UnitOfLength.METERS, None, "mdi:waves"),
    SensorDesc(
        "sea_surface_wave_from_direction",
        "Bølgenes retning (fra)",
        None,
        None,
        "mdi:compass-rose",
        value_fn=lambda data: _deg_to_cardinal_16(data.get("sea_surface_wave_from_direction")) if data and data.get("sea_surface_wave_from_direction") is not None else None
    ),
    # Saltholdighet (fra Havvarsel)
    SensorDesc(
        "sea_water_salinity",
        "Saltholdighet (psu)",
        "psu",
        None,
        "mdi:beaker",
        value_fn=lambda data: round(float(data.get("sea_water_salinity")), 2) if data and data.get("sea_water_salinity") is not None else None
    ),

    # Vind
    SensorDesc("wind_speed", "Vindhastighet", UnitOfSpeed.METERS_PER_SECOND, None, "mdi:weather-windy"),
    SensorDesc(
        "wind_from_direction",
        "Vindretning",
        None,
        None,
        "mdi:compass-rose",
        value_fn=lambda data: _deg_to_cardinal_16(data.get("wind_from_direction")) if data and data.get("wind_from_direction") is not None else None
    ),
]


async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback) -> None:
    """Setter opp sensor-entitetene for en konfigurasjonsentry."""
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]
    entities = [HavOgVindSensor(coordinator, entry, desc) for desc in SENSORS]
    async_add_entities(entities)


class HavOgVindSensor(CoordinatorEntity, SensorEntity):
    """En sensor-entitet for Hav og vind data."""
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry: ConfigEntry, desc: SensorDesc) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._desc = desc

        # Beholder eksisterende navnestil: "<Stedsnavn> <sensornavn>"
        self._attr_name = f"{self._entry.title} {desc.name}"
        self._attr_unique_id = f"{entry.entry_id}_{desc.key}"
        self._attr_icon = desc.icon
        self._attr_device_class = desc.device_class

        # Ingen enhet for kardinalretning, ellers bruk oppgitt enhet
        if desc.key in ("sea_water_to_direction", "sea_surface_wave_from_direction", "wind_from_direction") and desc.value_fn:
            self._attr_native_unit_of_measurement = None
        else:
            self._attr_native_unit_of_measurement = desc.unit

    @property
    def native_value(self) -> Any:
        data: dict = self.coordinator.data or {}
        if self._desc.value_fn:
            try:
                return self._desc.value_fn(data)
            except Exception as e:
                _LOGGER.error("Feil ved prosessering av verdi for %s: %s", self._desc.key, e)
                return None
        return data.get(self._desc.key)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        """Legger ved tidsstempel + relevante prognoselister dersom de finnes."""
        attrs: dict[str, Any] = {"attribution": "Data: MET Norway (api.met.no)"}
        data: dict = self.coordinator.data or {}

        if self._desc.key.startswith("sea_") and "ocean_time" in data:
            attrs["ocean_time"] = data["ocean_time"]
        if self._desc.key.startswith("wind_") and "wind_time" in data:
            attrs["wind_time"] = data["wind_time"]

        # Prognoser på relevante sensorer
        if self._desc.key == "wind_speed" and "wind_speed_forecast" in data:
            attrs["wind_speed_forecast"] = data["wind_speed_forecast"]

        if self._desc.key == "sea_surface_wave_height" and "sea_surface_wave_height_forecast" in data:
            attrs["sea_surface_wave_height_forecast"] = data["sea_surface_wave_height_forecast"]

        if self._desc.key == "sea_water_speed" and "sea_water_speed_forecast" in data:
            attrs["sea_water_speed_forecast"] = data["sea_water_speed_forecast"]

        if self._desc.key == "sea_water_salinity":
            if "salinity_time" in data:
                attrs["salinity_time"] = data["salinity_time"]
            if "sea_water_salinity_forecast" in data:
                attrs["sea_water_salinity_forecast"] = data["sea_water_salinity_forecast"]

        return attrs

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": "Hav og vind",
            "manufacturer": "MET Norway",
            "configuration_url": "https://api.met.no/",
        }
