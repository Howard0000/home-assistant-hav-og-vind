from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
import math
from typing import Any

from homeassistant.components.sensor import SensorEntity
from homeassistant.core import HomeAssistant, callback
from homeassistant.helpers.entity import EntityCategory
from homeassistant.helpers.event import async_track_state_change_event, async_track_time_interval
from homeassistant.util import slugify

# Primary (HACS / out-of-the-box)
SELECT_ENTITY_ID = "select.hav_og_vind_aktiv_stasjon"
# Fallback (legacy dashboard/YAML)
INPUT_SELECT_ENTITY_ID = "input_select.hav_og_vind_stasjon"

_INVALID_STATES = {"unknown", "unavailable", "none", ""}


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


@dataclass(frozen=True)
class ProxySpec:
    """Specification for one proxy sensor."""
    name: str
    unique_id: str
    icon: str | None = None
    unit: str | None = None
    # suffixes (first match wins). Tried as:
    #   sensor.hav_og_vind_<slug>_<suffix>
    #   sensor.<slug>_<suffix>
    suffixes: tuple[str, ...] = ()
    # forecast attributes to passthrough from source entity
    passthrough_attrs: tuple[str, ...] = ()


PROXIES: tuple[ProxySpec, ...] = (
    ProxySpec(
        name="Hav vind skydekke",
        unique_id="hav_vind_skydekke",
        icon="mdi:weather-partly-cloudy",
        unit="%",
        suffixes=("cloud_area_fraction", "skylag_areal"),
        passthrough_attrs=("cloud_area_fraction_forecast",),
    ),
    ProxySpec(
        name="Hav vind nedbor 1t",
        unique_id="hav_vind_nedbor_1t",
        icon="mdi:weather-rainy",
        unit="mm",
        suffixes=("precipitation_amount_1h", "nedbor_1t"),
        passthrough_attrs=("precipitation_amount_1h_forecast",),
    ),
    ProxySpec(
        name="Hav vind vindhastighet",
        unique_id="hav_vind_vindhastighet",
        icon="mdi:weather-windy",
        unit="m/s",
        suffixes=("wind_speed", "vindhastighet"),
        passthrough_attrs=("wind_speed_forecast", "wind_from_direction_forecast"),
    ),
    ProxySpec(
        name="Hav vind vindretning",
        unique_id="hav_vind_vindretning",
        icon="mdi:compass",
        suffixes=("wind_from_direction", "vindretning"),
        passthrough_attrs=("wind_from_direction_forecast",),
    ),
    ProxySpec(
        name="Hav vind vindkast",
        unique_id="hav_vind_vindkast",
        icon="mdi:weather-windy",
        unit="m/s",
        suffixes=("wind_speed_of_gust", "vindkast"),
        passthrough_attrs=("wind_speed_of_gust_forecast",),
    ),
    ProxySpec(
        name="Hav vind stromhastighet",
        unique_id="hav_vind_stromhastighet",
        icon="mdi:current-ac",
        unit="m/s",
        suffixes=("sea_water_speed", "stromhastighet"),
        passthrough_attrs=(
            "sea_water_speed_forecast",
            "sea_water_current_speed_forecast",
            "current_speed_forecast",
            "sea_current_speed_forecast",
        ),
    ),
    ProxySpec(
        name="Hav vind stromretning",
        unique_id="hav_vind_stromretning",
        icon="mdi:arrow-right-bold",
        suffixes=("sea_water_to_direction", "strommens_retning_mot"),
        passthrough_attrs=("sea_water_to_direction_forecast",),
    ),
    ProxySpec(
        name="Hav vind bolgeretning",
        unique_id="hav_vind_bolgeretning",
        icon="mdi:waves-arrow-right",
        suffixes=("sea_surface_wave_from_direction", "bolgenes_retning_fra"),
        passthrough_attrs=("sea_surface_wave_from_direction_forecast",),
    ),
    ProxySpec(
        name="Hav vind sjotemperatur",
        unique_id="hav_vind_sjotemperatur",
        icon="mdi:thermometer-water",
        unit="°C",
        suffixes=("sea_water_temperature", "sjotemperatur"),
        passthrough_attrs=("sea_water_temperature_forecast",),
    ),
    ProxySpec(
        name="Hav vind saltholdighet",
        unique_id="hav_vind_saltholdighet",
        icon="mdi:shaker-outline",
        unit="PSU",
        suffixes=("sea_water_salinity", "saltholdighet_psu"),
        passthrough_attrs=("sea_water_salinity_forecast",),
    ),
    ProxySpec(
        name="Hav vind lufttemperatur",
        unique_id="hav_vind_lufttemperatur",
        icon="mdi:thermometer",
        unit="°C",
        suffixes=("air_temperature", "lufttemperatur"),
        passthrough_attrs=("air_temperature_forecast",),
    ),
    ProxySpec(
        name="Hav vind luftfuktighet",
        unique_id="hav_vind_luftfuktighet",
        icon="mdi:water-percent",
        unit="%",
        suffixes=("relative_humidity", "luftfuktighet"),
        passthrough_attrs=("relative_humidity_forecast",),
    ),
    ProxySpec(
        name="Hav vind lufttrykk msl",
        unique_id="hav_vind_lufttrykk_msl",
        icon="mdi:gauge",
        unit="hPa",
        suffixes=("pressure_at_sea_level", "lufttrykk_msl"),
        passthrough_attrs=("pressure_at_sea_level_forecast",),
    ),
)


def _get_selected_station(hass: HomeAssistant) -> str | None:
    """Return selected station name.

    Primary: select.hav_og_vind_aktiv_stasjon (HACS/out-of-the-box)
    Fallback: input_select.hav_og_vind_stasjon (legacy dashboard/YAML)
    """
    for ent_id in (SELECT_ENTITY_ID, INPUT_SELECT_ENTITY_ID):
        st = hass.states.get(ent_id)
        if not st:
            continue
        val = (st.state or "").strip()
        if val and val not in _INVALID_STATES:
            return val
    return None


def _pick_source_entity_id(hass: HomeAssistant, station_slug: str, suffixes: tuple[str, ...]) -> str | None:
    """Pick first existing (non-invalid) source entity for a given station and suffix list."""
    candidates: list[str] = []
    for suf in suffixes:
        candidates.append(f"sensor.hav_og_vind_{station_slug}_{suf}")
        candidates.append(f"sensor.{station_slug}_{suf}")

    for ent_id in candidates:
        st = hass.states.get(ent_id)
        if st and st.state not in _INVALID_STATES:
            return ent_id
    return None


class HavOgVindProxySensor(SensorEntity):
    """Proxy sensor that forwards state + selected attributes from the chosen station."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_should_poll = False

    def __init__(self, hass: HomeAssistant, spec: ProxySpec) -> None:
        self.hass = hass
        self.spec = spec
        self._attr_name = spec.name
        self._attr_unique_id = spec.unique_id
        if spec.icon:
            self._attr_icon = spec.icon
        if spec.unit:
            self._attr_native_unit_of_measurement = spec.unit

        # Keep stable entity_id style (matches your old YAML proxies: sensor.hav_vind_*)
        self._attr_suggested_object_id = spec.unique_id

        self._unsub_select = None
        self._unsub_timer = None

    @property
    def available(self) -> bool:
        station = _get_selected_station(self.hass)
        if not station:
            return False
        station_slug = slugify(station)
        ent = _pick_source_entity_id(self.hass, station_slug, self.spec.suffixes)
        return ent is not None

    @property
    def native_value(self) -> Any:
        station = _get_selected_station(self.hass)
        if not station:
            return None
        station_slug = slugify(station)
        ent = _pick_source_entity_id(self.hass, station_slug, self.spec.suffixes)
        if not ent:
            return None

        st = self.hass.states.get(ent)
        if not st:
            return None

        # Cast to number when we have a unit (helps graphs/cards that expect numeric values)
        if self.spec.unit is not None:
            try:
                return float(st.state)
            except Exception:
                return None

        return st.state

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        attrs: dict[str, Any] = {}

        station = _get_selected_station(self.hass)
        if not station:
            attrs["source_entity_id"] = ""
            return attrs

        station_slug = slugify(station)
        ent = _pick_source_entity_id(self.hass, station_slug, self.spec.suffixes)
        attrs["source_entity_id"] = ent or ""

        if ent and self.hass.states.get(ent):
            st = self.hass.states.get(ent)
            for a in self.spec.passthrough_attrs:
                attrs[a] = st.attributes.get(a)
        else:
            for a in self.spec.passthrough_attrs:
                attrs[a] = None

        return attrs

    async def async_added_to_hass(self) -> None:
        @callback
        def _on_select_change(_event) -> None:
            self.async_write_ha_state()

        # Update on both select + input_select changes (migration friendly)
        self._unsub_select = async_track_state_change_event(
            self.hass,
            [SELECT_ENTITY_ID, INPUT_SELECT_ENTITY_ID],
            _on_select_change,
        )

        # Periodic refresh to reflect source sensor changes
        self._unsub_timer = async_track_time_interval(
            self.hass, lambda _now: self.schedule_update_ha_state(), timedelta(seconds=30)
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub_select:
            self._unsub_select()
            self._unsub_select = None
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None


class HavOgVindTidevannProxySensor(SensorEntity):
    """Proxy for tidevann. Henter state + serier fra tidevann_prediksjon-sensoren."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_should_poll = False
    _attr_name = "Hav vind tidevann"
    _attr_unique_id = "hav_vind_tidevann"
    _attr_icon = "mdi:waves"
    _attr_native_unit_of_measurement = "cm"
    _attr_suggested_object_id = "hav_vind_tidevann"

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._unsub_select = None
        self._unsub_timer = None

    def _src_pred(self, st_slug: str) -> str | None:
        ent1 = f"sensor.hav_og_vind_{st_slug}_tidevann_prediksjon"
        ent2 = f"sensor.{st_slug}_tidevann_prediksjon"
        for ent in (ent1, ent2):
            st = self.hass.states.get(ent)
            if st and st.state not in _INVALID_STATES:
                return ent
        return None

    @property
    def available(self) -> bool:
        station = _get_selected_station(self.hass)
        if not station:
            return False
        return self._src_pred(slugify(station)) is not None

    @property
    def native_value(self) -> float | None:
        station = _get_selected_station(self.hass)
        if not station:
            return None
        src = self._src_pred(slugify(station))
        if not src:
            return None
        st = self.hass.states.get(src)
        if not st or st.state in _INVALID_STATES:
            return None
        try:
            return float(st.state)
        except Exception:
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        station = _get_selected_station(self.hass)
        if not station:
            return {"source_entity_id": ""}

        src = self._src_pred(slugify(station))
        out: dict[str, Any] = {"source_entity_id": src or ""}

        if src:
            st = self.hass.states.get(src)
            if st:
                out["tide_prediction_series"] = _trim_series(st.attributes.get("tide_prediction_series"))
                out["tide_forecast_series"] = _trim_series(st.attributes.get("tide_forecast_series"))
                out["tide_observation_series"] = _trim_series(st.attributes.get("tide_observation_series"))
                return out

        out["tide_prediction_series"] = None
        out["tide_forecast_series"] = None
        out["tide_observation_series"] = None
        return out

    async def async_added_to_hass(self) -> None:
        @callback
        def _on_select_change(_event) -> None:
            self.async_write_ha_state()

        self._unsub_select = async_track_state_change_event(
            self.hass,
            [SELECT_ENTITY_ID, INPUT_SELECT_ENTITY_ID],
            _on_select_change,
        )
        self._unsub_timer = async_track_time_interval(
            self.hass,
            lambda _now: self.schedule_update_ha_state(),
            timedelta(seconds=30),
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub_select:
            self._unsub_select()
            self._unsub_select = None
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None



class HavOgVindBolgehoydeProxySensor(SensorEntity):
    """Special proxy for significant wave height with float state + forecast attrs."""

    _attr_entity_category = EntityCategory.DIAGNOSTIC
    _attr_should_poll = False
    _attr_name = "Hav vind bolgehoyde"
    _attr_unique_id = "hav_vind_bolgehoyde"
    _attr_icon = "mdi:waves"
    _attr_native_unit_of_measurement = "m"
    _attr_suggested_object_id = "hav_vind_bolgehoyde"

    def __init__(self, hass: HomeAssistant) -> None:
        self.hass = hass
        self._unsub_select = None
        self._unsub_timer = None

    def _src(self, st_slug: str) -> str | None:
        ent1 = f"sensor.hav_og_vind_{st_slug}_signifikant_bolgehoyde"
        ent2 = f"sensor.{st_slug}_signifikant_bolgehoyde"
        if self.hass.states.get(ent1) and self.hass.states.get(ent1).state not in _INVALID_STATES:
            return ent1
        if self.hass.states.get(ent2) and self.hass.states.get(ent2).state not in _INVALID_STATES:
            return ent2
        return None

    @property
    def available(self) -> bool:
        station = _get_selected_station(self.hass)
        if not station:
            return False
        return self._src(slugify(station)) is not None

    @property
    def native_value(self) -> float | None:
        station = _get_selected_station(self.hass)
        if not station:
            return None
        src = self._src(slugify(station))
        if not src or not self.hass.states.get(src):
            return None
        try:
            return float(self.hass.states.get(src).state)
        except Exception:
            return None

    @property
    def extra_state_attributes(self) -> dict[str, Any]:
        station = _get_selected_station(self.hass)
        if not station:
            return {"source_entity_id": ""}

        src = self._src(slugify(station))
        out: dict[str, Any] = {"source_entity_id": src or ""}

        if src and self.hass.states.get(src):
            st = self.hass.states.get(src)
            out["sea_surface_wave_height_forecast"] = st.attributes.get("sea_surface_wave_height_forecast")
            out["significant_wave_height_forecast"] = st.attributes.get("significant_wave_height_forecast")
            out["wave_height_forecast"] = st.attributes.get("wave_height_forecast")
        else:
            out["sea_surface_wave_height_forecast"] = None
            out["significant_wave_height_forecast"] = None
            out["wave_height_forecast"] = None

        return out

    async def async_added_to_hass(self) -> None:
        @callback
        def _on_select_change(_event) -> None:
            self.async_write_ha_state()

        self._unsub_select = async_track_state_change_event(
            self.hass,
            [SELECT_ENTITY_ID, INPUT_SELECT_ENTITY_ID],
            _on_select_change,
        )
        self._unsub_timer = async_track_time_interval(
            self.hass, lambda _now: self.schedule_update_ha_state(), timedelta(seconds=30)
        )

    async def async_will_remove_from_hass(self) -> None:
        if self._unsub_select:
            self._unsub_select()
            self._unsub_select = None
        if self._unsub_timer:
            self._unsub_timer()
            self._unsub_timer = None


def build_proxy_entities(hass: HomeAssistant) -> list[SensorEntity]:
    """Build all proxy entities (sensor.hav_vind_*)."""
    entities: list[SensorEntity] = [HavOgVindProxySensor(hass, spec) for spec in PROXIES]
    entities.append(HavOgVindTidevannProxySensor(hass))
    entities.append(HavOgVindBolgehoydeProxySensor(hass))
    return entities
