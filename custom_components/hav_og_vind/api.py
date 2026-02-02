from __future__ import annotations

import asyncio
import datetime as dt
import logging
from typing import Any, Dict, Optional, List
import xml.etree.ElementTree as ET

from aiohttp import ClientSession

from .const import USER_AGENT, OCEAN_URL, WIND_URL, HAVVARSEL_TEMP_URL_FMT, HAVVARSEL_SALINITY_URL_FMT

_LOGGER = logging.getLogger(__name__)

# Kartverket (tide via lat/lon)
KARTVERKET_TIDE_XML = (
    "https://vannstand.kartverket.no/tideapi.php"
    "?lat={lat}&lon={lon}&fromtime={fromtime}&totime={totime}"
    "&datatype=all&refcode=cd&lang=no&interval=10&dst=0&tzone=&tide_request=locationdata"
)

# ---------- felles helpers ----------
def _closest_ts(timeseries: List[dict], now_iso: str) -> Optional[dict]:
    if not timeseries:
        return None
    first_after = None
    last_before = None
    for it in timeseries:
        t = it.get("time")
        if not isinstance(t, str):
            continue
        if t >= now_iso and first_after is None:
            first_after = it
            break
        last_before = it
    return first_after or last_before or timeseries[0]

def _to_iso_z(dtobj: dt.datetime) -> str:
    return dtobj.replace(tzinfo=dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

# ---------- API-klient ----------
class HavOgVindApi:
    """Henter MET (vind/hav + luft/“vær”), Havvarsel (temperatur + saltholdighet) og Kartverket (tidevann)."""

    def __init__(self, session: ClientSession) -> None:
        self._session = session

    async def _get_json(self, url: str, params: dict[str, Any], *, add_host_header: bool = False) -> dict:
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Accept-Encoding": "identity",
            "Cache-Control": "no-cache",
        }
        if add_host_header:
            headers["Host"] = "api.met.no"
        async with self._session.get(url, params=params, headers=headers, timeout=30) as resp:
            resp.raise_for_status()
            return await resp.json()

    # -------------------- MET: vind + luft/“vær” --------------------
    async def _parse_wind(self, wind: dict, now_iso: str) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        ts = (wind or {}).get("properties", {}).get("timeseries", []) or []
        item = _closest_ts(ts, now_iso)

        def _blocks(node: dict) -> tuple[dict, dict, dict]:
            data = (node or {}).get("data") or {}
            instant = (data.get("instant") or {}).get("details") or {}
            next_1h = (data.get("next_1_hours") or {}).get("details") or {}
            next_6h = (data.get("next_6_hours") or {}).get("details") or {}
            return instant, next_1h, next_6h

        inst, n1, n6 = _blocks(item or {})

        out["wind_speed"] = inst.get("wind_speed")
        out["wind_from_direction"] = inst.get("wind_from_direction")
        gust = inst.get("wind_speed_of_gust")
        if gust is None:
            gust = n1.get("wind_speed_of_gust", n6.get("wind_speed_of_gust"))
        out["wind_speed_of_gust"] = gust
        out["wind_time"] = (item or {}).get("time")

        out["air_temperature"] = inst.get("air_temperature")
        out["relative_humidity"] = inst.get("relative_humidity")
        apsl = inst.get("air_pressure_at_sea_level")
        if apsl is not None:
            out["pressure_at_sea_level"] = apsl
        out["cloud_area_fraction"] = inst.get("cloud_area_fraction")
        pa1 = n1.get("precipitation_amount")
        if pa1 is not None:
            out["precipitation_amount_1h"] = pa1

        # forecast-serier (24)
        wind_fc: List[dict] = []
        gust_fc: List[dict] = []
        dir_fc:  List[dict] = []
        temp_fc: List[dict] = []
        prec1_fc: List[dict] = []
        rh_fc: List[dict] = []
        msl_fc: List[dict] = []
        cloud_fc: List[dict] = []

        for it in ts:
            t = it.get("time")
            if not isinstance(t, str) or t < now_iso:
                continue
            i, n1b, n6b = _blocks(it)
            v = i.get("wind_speed")
            d = i.get("wind_from_direction")
            g = i.get("wind_speed_of_gust") or n1b.get("wind_speed_of_gust", n6b.get("wind_speed_of_gust"))
            temp = i.get("air_temperature")
            p1 = n1b.get("precipitation_amount")
            rh = i.get("relative_humidity")
            msl = i.get("air_pressure_at_sea_level")
            cloud = i.get("cloud_area_fraction")

            if v is not None and len(wind_fc) < 24: wind_fc.append({"time": t, "value": v})
            if g is not None and len(gust_fc) < 24: gust_fc.append({"time": t, "value": g})
            if d is not None and len(dir_fc) < 24:  dir_fc.append({"time": t, "value": d})
            if temp is not None and len(temp_fc) < 24: temp_fc.append({"time": t, "value": temp})
            if p1 is not None and len(prec1_fc) < 24: prec1_fc.append({"time": t, "value": float(p1)})
            if rh is not None and len(rh_fc) < 24: rh_fc.append({"time": t, "value": rh})
            if msl is not None and len(msl_fc) < 24: msl_fc.append({"time": t, "value": msl})
            if cloud is not None and len(cloud_fc) < 24: cloud_fc.append({"time": t, "value": cloud})

            if (len(wind_fc) >= 24 and len(gust_fc) >= 24 and len(dir_fc) >= 24
                and len(temp_fc) >= 24 and len(prec1_fc) >= 24
                and len(rh_fc) >= 24 and len(msl_fc) >= 24 and len(cloud_fc) >= 24):
                break

        if wind_fc: out["wind_speed_forecast"] = wind_fc
        if gust_fc: out["wind_speed_of_gust_forecast"] = gust_fc
        if dir_fc:  out["wind_from_direction_forecast"] = dir_fc
        if temp_fc: out["air_temperature_forecast"] = temp_fc
        if prec1_fc: out["precipitation_amount_1h_forecast"] = prec1_fc
        if rh_fc: out["relative_humidity_forecast"] = rh_fc
        if msl_fc: out["pressure_at_sea_level_forecast"] = msl_fc
        if cloud_fc: out["cloud_area_fraction_forecast"] = cloud_fc

        return out

    # -------------------- MET: hav (bølger/strøm + temp-fallback) --------------------
    async def _parse_ocean(self, ocean: dict, now_iso: str) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        ts = (ocean or {}).get("properties", {}).get("timeseries", []) or []
        item = _closest_ts(ts, now_iso)
        details = ((item or {}).get("data") or {}).get("instant", {}).get("details") or {}

        # OBS: oceanforecast bruker "sea_water_temperature"
        out["sea_water_temperature"] = details.get("sea_water_temperature")
        out["sea_water_speed"] = details.get("sea_water_speed")
        out["sea_water_to_direction"] = details.get("sea_water_to_direction")
        out["sea_surface_wave_height"] = details.get("sea_surface_wave_height")
        out["sea_surface_wave_from_direction"] = details.get("sea_surface_wave_from_direction")
        out["ocean_time"] = (item or {}).get("time")

        wave_fc: List[dict] = []
        current_fc: List[dict] = []
        temp_fc: List[dict] = []
        wave_dir_fc: List[dict] = []
        current_dir_fc: List[dict] = []

        for it in ts:
            t = it.get("time")
            if not isinstance(t, str) or t < now_iso:
                continue
            det = ((it.get("data") or {}).get("instant") or {}).get("details") or {}
            h = det.get("sea_surface_wave_height")
            s = det.get("sea_water_speed")
            temp = det.get("sea_water_temperature")
            wave_dir = det.get("sea_surface_wave_from_direction")
            cur_dir = det.get("sea_water_to_direction")

            if h is not None and len(wave_fc) < 24: wave_fc.append({"time": t, "value": h})
            if s is not None and len(current_fc) < 24: current_fc.append({"time": t, "value": s})
            if temp is not None and len(temp_fc) < 24: temp_fc.append({"time": t, "value": temp})
            if wave_dir is not None and len(wave_dir_fc) < 24: wave_dir_fc.append({"time": t, "value": wave_dir})
            if cur_dir is not None and len(current_dir_fc) < 24: current_dir_fc.append({"time": t, "value": cur_dir})

            if (len(wave_fc) >= 24 and len(current_fc) >= 24 and len(temp_fc) >= 24
                and len(wave_dir_fc) >= 24 and len(current_dir_fc) >= 24):
                break

        if wave_fc: out["sea_surface_wave_height_forecast"] = wave_fc
        if current_fc: out["sea_water_speed_forecast"] = current_fc
        if temp_fc: out["sea_water_temperature_forecast"] = temp_fc
        if wave_dir_fc: out["sea_surface_wave_from_direction_forecast"] = wave_dir_fc
        if current_dir_fc: out["sea_water_to_direction_forecast"] = current_dir_fc
        return out

    # -------------------- Havvarsel: temperatur --------------------
    async def _fetch_temperature_projection(self, lat: float, lon: float, depth: int = 0) -> Dict[str, Any]:
        params = {"depth": depth}
        headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        try:
            url = HAVVARSEL_TEMP_URL_FMT.format(lon=lon, lat=lat)
            async with self._session.get(url, params=params, headers=headers, timeout=30) as resp:
                resp.raise_for_status()
                js = await resp.json()
        except Exception as e:
            _LOGGER.warning("Havvarsel temperatureprojection feilet: %s", e)
            return {}

        variables = js.get("variables") or []
        data: List[dict] = (variables[0].get("data") if variables else None) or []
        if not data:
            return {}

        now_ms = int(dt.datetime.now(dt.timezone.utc).timestamp() * 1000)
        best = min(
            (p for p in data if p.get("rawTime") is not None and p.get("value") is not None),
            key=lambda p: abs(int(p["rawTime"]) - now_ms),
            default=None,
        )

        out: Dict[str, Any] = {"sea_water_temperature_source": "havvarsel"}

        if best:
            t0 = dt.datetime.fromtimestamp(int(best["rawTime"]) / 1000, tz=dt.timezone.utc)
            out["sea_water_temperature"] = round(float(best["value"]), 2)
            out["ocean_time"] = _to_iso_z(t0)

        # Forecast (24 fram)
        fc: List[dict] = []
        for p in data:
            rt, val = p.get("rawTime"), p.get("value")
            if rt is None or val is None or int(rt) < now_ms:
                continue
            t0 = dt.datetime.fromtimestamp(int(rt) / 1000, tz=dt.timezone.utc)
            fc.append({"time": _to_iso_z(t0), "value": round(float(val), 2)})
            if len(fc) >= 24:
                break
        if fc:
            out["sea_water_temperature_forecast"] = fc

        # Nærmeste grid-punkt
        cgp = js.get("closestGridPointWithData") or {}
        if "lon" in cgp and "lat" in cgp:
            out["nearest_grid_lon"] = cgp["lon"]
            out["nearest_grid_lat"] = cgp["lat"]

        # Valgfri forhåndsvisning (nyttig feilsøking)
        preview: List[dict] = []
        for p in data[:24]:
            rt, val = p.get("rawTime"), p.get("value")
            if rt is None or val is None:
                continue
            t0 = dt.datetime.fromtimestamp(int(rt) / 1000, tz=dt.timezone.utc)
            preview.append({"time": _to_iso_z(t0), "value": round(float(val), 2)})
        if preview:
            out["sea_water_temperature_raw_preview"] = preview

        return out

    # -------------------- Havvarsel: saltholdighet --------------------
    async def _fetch_salinity(self, lat: float, lon: float) -> Dict[str, Any]:
        base = HAVVARSEL_SALINITY_URL_FMT.format(lon=lon, lat=lat)
        now = dt.datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        after = (now - dt.timedelta(hours=12)).strftime("%Y-%m-%d")
        before = (now + dt.timedelta(days=2)).strftime("%Y-%m-%d")
        params = {"after": after, "before": before, "depth": 0}
        headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
        try:
            async with self._session.get(base, params=params, headers=headers, timeout=30) as resp:
                resp.raise_for_status()
                js = await resp.json()
        except Exception as e:
            _LOGGER.warning("Salinity request failed: %s", e)
            return {}

        raw = js.get("data") or js.get("timeseries") or []
        if not isinstance(raw, list) or not raw:
            return {}

        def _iso_from_node(dp: dict) -> Optional[str]:
            t = dp.get("time")
            if isinstance(t, str): 
                return t
            rt = dp.get("raw_time") or dp.get("rawTime")
            if isinstance(rt, (int, float)):
                if rt > 10**12: 
                    rt = rt / 1000.0
                return dt.datetime.utcfromtimestamp(rt).replace(microsecond=0).isoformat() + "Z"
            return None

        def _read_sal(dp: dict) -> Optional[float]:
            if isinstance(dp.get("value"), (int, float, str)):
                try: 
                    return float(dp["value"])
                except Exception:
                    pass
            for kv in dp.get("data") or []:
                if kv.get("key") == "salinity" and kv.get("value") is not None:
                    try:
                        return float(kv["value"])
                    except Exception:
                        return None
            return None

        items: List[tuple[str, float]] = []
        for dp in raw:
            ts = _iso_from_node(dp); val = _read_sal(dp)
            if ts and val is not None: 
                items.append((ts, val))
        if not items: 
            return {}

        items.sort(key=lambda x: x[0])
        now_iso = now.isoformat() + "Z"
        chosen = None; last_before = None
        for t, v in items:
            if t >= now_iso and chosen is None: 
                chosen = (t, v); break
            last_before = (t, v)
        if chosen is None: 
            chosen = last_before

        cur_t, cur_v = chosen  # type: ignore[misc]
        fc: List[dict] = []
        for t, v in items:
            if t >= now_iso:
                fc.append({"time": t, "value": v})
                if len(fc) >= 24: 
                    break

        out: Dict[str, Any] = {"salinity_time": cur_t, "sea_water_salinity": round(float(cur_v), 2)}
        if fc: 
            out["sea_water_salinity_forecast"] = fc
        return out

    # -------------------- Kartverket: tide --------------------
    async def _fetch_tide_by_latlon(self, lat: float, lon: float) -> Dict[str, Any]:
        fromtime = (dt.datetime.utcnow() - dt.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
        totime = (dt.datetime.utcnow() + dt.timedelta(days=1)).strftime("%Y-%m-%dT%H:%M:%S")
        url = KARTVERKET_TIDE_XML.format(lat=lat, lon=lon, fromtime=fromtime, totime=totime)
        headers = {"User-Agent": USER_AGENT, "Accept": "application/xml"}
        try:
            async with self._session.get(url, headers=headers, timeout=30) as resp:
                resp.raise_for_status()
                xml_text = await resp.text()
        except Exception as e:
            _LOGGER.warning("Tide XML request failed: %s", e)
            return {}
        try:
            root = ET.fromstring(xml_text)
        except ET.ParseError as e:
            _LOGGER.error("Tide XML parse error: %s", e)
            return {}
        tide_data = {"observation": [], "prediction": [], "forecast": []}
        series_map = {
            "observation": "tide_observation_series",
            "prediction": "tide_prediction_series",
            "forecast": "tide_forecast_series",
        }
        out: Dict[str, Any] = {}
        for data in root.findall(".//data"):
            data_type = data.attrib.get("type")
            if data_type not in tide_data:
                continue
            for wl in data.findall("waterlevel"):
                time_s = wl.attrib.get("time")
                val_s = wl.attrib.get("value")
                if time_s is None or val_s is None:
                    continue
                try:
                    val = float(val_s)
                except Exception:
                    continue
                tide_data[data_type].append({"time": time_s, "level": val})
        for k, arr in tide_data.items():
            if arr:
                out[series_map[k]] = [{"time": it["time"], "value": it["level"]} for it in arr]

        def _parse_iso(s: str) -> Optional[dt.datetime]:
            try: 
                return dt.datetime.fromisoformat(s).replace(tzinfo=dt.timezone.utc)
            except Exception: 
                return None

        now = dt.datetime.now(dt.timezone.utc)

        def _latest_past(arr: List[dict]) -> Optional[float]:
            best_t = None; best_v = None
            for it in arr:
                tt = _parse_iso(it["time"])
                if tt and tt <= now:
                    if best_t is None or tt > best_t:
                        best_t, best_v = tt, it["level"]
            return best_v

        def _first_future(arr: List[dict]) -> Optional[float]:
            for it in arr:
                tt = _parse_iso(it["time"])
                if tt and tt >= now:
                    return it["level"]
            return None

        if tide_data["observation"]: out["tide_observation"] = _latest_past(tide_data["observation"])
        if tide_data["prediction"]:  out["tide_prediction"]  = _first_future(tide_data["prediction"])
        if tide_data["forecast"]:    out["tide_forecast"]    = _first_future(tide_data["forecast"])
        return out

    # -------------------- Samlet fetch (UTEN FROST) --------------------
    async def fetch(self, lat: float, lon: float, *, name: str) -> Dict[str, Any]:
        now = dt.datetime.utcnow().replace(minute=0, second=0, microsecond=0)
        now_iso = now.isoformat() + "Z"
        result: Dict[str, Any] = {}

        # 1) Vind + luft/“vær”
        try:
            wind = await self._get_json(WIND_URL, {"lat": lat, "lon": lon}, add_host_header=True)
            result.update(await self._parse_wind(wind, now_iso))
        except Exception as e:
            _LOGGER.warning("Wind request failed: %s", e)

        # 2) Sjøtemperatur fra Havvarsel
        try:
            result.update(await self._fetch_temperature_projection(lat, lon, depth=0))
        except Exception as e:
            _LOGGER.warning("Havvarsel temperatureprojection parse failed: %s", e)

        # 3) Hav (MET) – bølger/strøm + TEMP fallback
        await asyncio.sleep(0.2)
        try:
            ocean = await self._get_json(OCEAN_URL, {"lon": lon, "lat": lat}, add_host_header=True)
            ocean_part = await self._parse_ocean(ocean, now_iso)

            # Fallback temp hvis Havvarsel ikke svarte
            if result.get("sea_water_temperature") is None and ocean_part.get("sea_water_temperature") is not None:
                result["sea_water_temperature"] = ocean_part["sea_water_temperature"]
                if ocean_part.get("sea_water_temperature_forecast"):
                    result["sea_water_temperature_forecast"] = ocean_part["sea_water_temperature_forecast"]
                result["sea_water_temperature_source"] = "met_ocean"

            # Alltid ta med øvrige havfelter
            for k in (
                "sea_water_speed", "sea_water_to_direction",
                "sea_surface_wave_height", "sea_surface_wave_from_direction",
                "ocean_time", "sea_surface_wave_height_forecast",
                "sea_water_speed_forecast", "sea_surface_wave_from_direction_forecast",
                "sea_water_to_direction_forecast",
            ):
                if ocean_part.get(k) is not None:
                    result[k] = ocean_part[k]
        except Exception as e:
            _LOGGER.warning("Ocean request failed: %s", e)

        # 4) Saltholdighet
        try:
            result.update(await self._fetch_salinity(lat, lon))
        except Exception as e:
            _LOGGER.warning("Salinity parse failed: %s", e)

        # 5) Tide
        try:
            tide = await self._fetch_tide_by_latlon(lat, lon)
            if tide:
                tide["tide_location_name"] = name
                result.update(tide)
        except Exception as e:
            _LOGGER.warning("Tide fetch failed: %s", e)

        return result