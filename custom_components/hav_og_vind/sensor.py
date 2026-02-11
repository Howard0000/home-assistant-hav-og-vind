from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import math
from typing import Any, Callable
import logging

from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.event import async_track_time_interval
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from homeassistant.helpers.entity_platform import AddEntitiesCallback
from homeassistant.helpers.update_coordinator import CoordinatorEntity
from homeassistant.const import (
    UnitOfTemperature,
    UnitOfSpeed,
    UnitOfLength,
    UnitOfPressure,
    PERCENTAGE,
)
from homeassistant.util import slugify

from .proxy_sensor import build_proxy_entities

from .const import DOMAIN

_LOGGER = logging.getLogger(__name__)


@dataclass
class SensorDesc:
    data_key: str                 # nøkkel i coordinator.data (API-resultat)
    name: str                     # visningsnavn
    object_id: str                # entity_id-suffix (norsk slug du bruker i proxy)
    unit: str | None = None
    device_class: SensorDeviceClass | None = None
    icon: str | None = None
    value_fn: Callable[[dict], Any] | None = None


def _deg_to_cardinal_16(deg: float | None) -> str | None:
    if deg is None:
        return None
    labels = [
        "N", "NNØ", "NØ", "ØNØ", "Ø", "ØSØ", "SØ", "SSØ",
        "S", "SSV", "SV", "VSV", "V", "VNV", "NV", "NNV",
    ]
    try:
        i = int((float(deg) % 360) / 22.5 + 0.5) % 16
        return labels[i]
    except Exception:
        _LOGGER.error("Kunne ikke konvertere gradverdi '%s' til kardinal retning", deg)
        return None

def _trim_series(series: Any, max_points: int = 72) -> Any:
    """Trim tide series to avoid recorder attribute size limit.

    Keeps the full time span by down-sampling evenly if the list is long.
    """
    if not isinstance(series, list):
        return series

    n = len(series)
    if n <= max_points:
        return series

    step = math.ceil(n / max_points)
    out = series[::step]

    # Ensure we always include the last point (end of horizon)
    if out and out[-1] != series[-1]:

        if len(out) >= max_points:
            out[-1] = series[-1]
        else:
            out.append(series[-1])

    return out[:max_points]


SENSORS: list[SensorDesc] = [
    # Luft / MET
    SensorDesc("cloud_area_fraction", "Skylag (% areal)", "skylag_areal", PERCENTAGE, None, "mdi:weather-cloudy"),
    SensorDesc("precipitation_amount_1h", "Nedbør 1t", "nedbor_1t", UnitOfLength.MILLIMETERS, None, "mdi:weather-pouring"),
    SensorDesc("wind_speed", "Vindhastighet", "windhastighet", UnitOfSpeed.METERS_PER_SECOND, None, "mdi:weather-windy"),
    SensorDesc("wind_speed_of_gust", "Vindkast", "windkast", UnitOfSpeed.METERS_PER_SECOND, None, "mdi:weather-windy"),
    SensorDesc(
        "wind_from_direction",
        "Vindretning",
        "vindretning",
        None,
        None,
        "mdi:compass-rose",
        value_fn=lambda data: _deg_to_cardinal_16(data.get("wind_from_direction")) if data and data.get("wind_from_direction") is not None else None,
    ),
    SensorDesc("air_temperature", "Lufttemperatur", "lufttemperatur", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, "mdi:thermometer"),
    SensorDesc("relative_humidity", "Luftfuktighet", "luftfuktighet", PERCENTAGE, SensorDeviceClass.HUMIDITY, "mdi:water-percent"),
    SensorDesc("pressure_at_sea_level", "Lufttrykk (MSL)", "lufttrykk_msl", UnitOfPressure.HPA, SensorDeviceClass.ATMOSPHERIC_PRESSURE, "mdi:gauge"),

    # Hav / MET + Havvarsel
    SensorDesc("sea_water_temperature", "Sjøtemperatur", "sjotemperatur", UnitOfTemperature.CELSIUS, SensorDeviceClass.TEMPERATURE, "mdi:coolant-temperature"),
    SensorDesc("sea_water_speed", "Strømhastighet", "stromhastighet", UnitOfSpeed.METERS_PER_SECOND, None, "mdi:arrow-projectile"),
    SensorDesc(
        "sea_water_to_direction",
        "Strømmens retning (mot)",
        "strommens_retning_mot",
        None,
        None,
        "mdi:compass-rose",
        value_fn=lambda data: _deg_to_cardinal_16(data.get("sea_water_to_direction")) if data and data.get("sea_water_to_direction") is not None else None,
    ),
    SensorDesc("sea_surface_wave_height", "Signifikant bølgehøyde", "signifikant_bolgehoyde", UnitOfLength.METERS, None, "mdi:waves"),
    SensorDesc(
        "sea_surface_wave_from_direction",
        "Bølgenes retning (fra)",
        "bolgenes_retning_fra",
        None,
        None,
        "mdi:compass-rose",
        value_fn=lambda data: _deg_to_cardinal_16(data.get("sea_surface_wave_from_direction")) if data and data.get("sea_surface_wave_from_direction") is not None else None,
    ),
    SensorDesc(
        "sea_water_salinity",
        "Saltholdighet (psu)",
        "saltholdighet_psu",
        "psu",
        None,
        "mdi:beaker",
        value_fn=lambda data: round(float(data.get("sea_water_salinity")), 2) if data and data.get("sea_water_salinity") is not None else None,
    ),

    # Tide (Kartverket)
    SensorDesc("tide_prediction", "Tidevann (prediksjon)", "tidevann_prediksjon", "cm", None, "mdi:waves-arrow-right"),
]


async def async_setup_entry(
    hass: HomeAssistant,
    entry: ConfigEntry,
    async_add_entities: AddEntitiesCallback,
) -> None:
    data = hass.data[DOMAIN][entry.entry_id]
    coordinator = data["coordinator"]

    entities = [HavOgVindSensor(coordinator, entry, desc) for desc in SENSORS]

    # Domenedata ligger allerede i hass.data[DOMAIN] fra __init__.py
    domain_data: dict[str, Any] = hass.data[DOMAIN]
    global_data: dict[str, Any] = domain_data.setdefault("_global", {})
    if not global_data.get("stations_sensor_added"):
        entities.append(HavOgVindStationsSensor(hass))
        global_data["stations_sensor_added"] = True


    # Legg til én felles proxy-sensorgjeng (sensor.hav_vind_*) (kun én gang per HA-instans)
    if not global_data.get("proxy_sensors_added"):
        entities.extend(build_proxy_entities(hass))
        global_data["proxy_sensors_added"] = True

    async_add_entities(entities)


class HavOgVindSensor(CoordinatorEntity, SensorEntity):
    _attr_has_entity_name = True

    def __init__(self, coordinator, entry: ConfigEntry, desc: SensorDesc) -> None:
        super().__init__(coordinator)
        self._entry = entry
        self._desc = desc

        # Visningsnavn (uten å bake inn entry.title)
        self._attr_name = desc.name

        # Stabil unique_id
        self._attr_unique_id = f"{entry.entry_id}_{desc.data_key}"

        # Viktig: styr entity_id til det proxyen forventer:
        # sensor.hav_og_vind_<stasjon>_<object_id>
        station_slug = slugify(entry.title)
        self._attr_suggested_object_id = f"{DOMAIN}_{station_slug}_{desc.object_id}"

        self._attr_icon = desc.icon
        self._attr_device_class = desc.device_class
        self._attr_native_unit_of_measurement = desc.unit

    @property
    def native_value(self) -> Any:
        data: dict = self.coordinator.data or {}
        if self._desc.value_fn:
            try:
                return self._desc.value_fn(data)
            except Exception as e:
                _LOGGER.error("Feil ved prosessering av verdi for %s: %s", self._desc.data_key, e)
                return None
        return data.get(self._desc.data_key)

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {"attribution": "Data: MET Norway / Havvarsel / Kartverket"}
        data: dict = self.coordinator.data or {}

        # timestamps
        if self._desc.data_key.startswith("sea_") and "ocean_time" in data:
            attrs["ocean_time"] = data["ocean_time"]
        if self._desc.data_key in (
            "wind_speed", "wind_speed_of_gust", "wind_from_direction",
            "air_temperature", "relative_humidity", "pressure_at_sea_level",
            "cloud_area_fraction", "precipitation_amount_1h",
        ) and "wind_time" in data:
            attrs["wind_time"] = data["wind_time"]

        # forecast (kun relevante)
        fc_key_map = {
            "wind_speed": "wind_speed_forecast",
            "wind_speed_of_gust": "wind_speed_of_gust_forecast",
            "wind_from_direction": "wind_from_direction_forecast",
            "air_temperature": "air_temperature_forecast",
            "relative_humidity": "relative_humidity_forecast",
            "pressure_at_sea_level": "pressure_at_sea_level_forecast",
            "cloud_area_fraction": "cloud_area_fraction_forecast",
            "precipitation_amount_1h": "precipitation_amount_1h_forecast",
            "sea_surface_wave_height": "sea_surface_wave_height_forecast",
            "sea_water_speed": "sea_water_speed_forecast",
            "sea_surface_wave_from_direction": "sea_surface_wave_from_direction_forecast",
            "sea_water_to_direction": "sea_water_to_direction_forecast",
            "sea_water_temperature": "sea_water_temperature_forecast",
            "sea_water_salinity": "sea_water_salinity_forecast",
        }
        k = fc_key_map.get(self._desc.data_key)
        if k and k in data:
            attrs[k] = data[k]

        if self._desc.data_key == "sea_water_temperature":
            for extra in ("sea_water_temperature_source", "nearest_grid_lon", "nearest_grid_lat"):
                if extra in data:
                    attrs[extra] = data[extra]

        if self._desc.data_key == "sea_water_salinity" and "salinity_time" in data:
            attrs["salinity_time"] = data["salinity_time"]

        if self._desc.data_key.startswith("tide_") or self._desc.data_key == "tide_prediction":
            if "tide_location_name" in data:
                attrs["tide_location_name"] = data["tide_location_name"]
            # hold dette “lett” (serier kommer fra api.py-fiksen under)
            for key in ("tide_observation_series", "tide_prediction_series", "tide_forecast_series"):
                if key in data:
                    attrs[key] = _trim_series(data[key])

        return attrs

    @property
    def device_info(self) -> dict[str, Any]:
        return {
            "identifiers": {(DOMAIN, self._entry.entry_id)},
            "name": self._entry.title,
            # Litt mer nøytralt, og unngår at det ser ut som du "er" MET/Kartverket
            "manufacturer": "Hav og vind (MET / Havvarsel / Kartverket)",
            # Peker til repo/README (mest relevant for bruker og review)
            "configuration_url": "https://github.com/Howard0000/home-assistant-hav-og-vind",
        }

class HavOgVindStationsSensor(SensorEntity):
    """Eksponerer alle Hav og vind-lokasjoner (config entries) som liste i attributt.

    - State = antall stasjoner (alltid gyldig tall)
    - attributes.stations = sortert liste av entry.title
    """

    _attr_has_entity_name = True
    _attr_name = "Stasjoner"
    _attr_unique_id = "hav_og_vind_stasjoner"
    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_icon = "mdi:map-marker-multiple"

    def __init__(self, hass: HomeAssistant) -> None:
        self._hass = hass
        self._unsub = None

    @property
    def native_value(self) -> int:
        return len(self._stations())

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        return {"stations": self._stations()}

    def _stations(self) -> list[str]:
        entries = self._hass.config_entries.async_entries(DOMAIN)
        names = [e.title for e in entries if e.title]
        uniq = list(dict.fromkeys(names))  # unik, bevarer rekkefølge
        uniq.sort()
        return uniq

    async def async_added_to_hass(self) -> None:
        # Oppdater jevnlig (fanger opp nye/slettede lokasjoner uten restart)
        self._unsub = async_track_time_interval(
            self._hass, lambda _now: self.schedule_update_ha_state(), timedelta(seconds=30)
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub:
            self._unsub()
            self._unsub = None

