# custom_components/hav_og_vind/api.py
from __future__ import annotations

import asyncio
import datetime as dt
import logging
from typing import Any, Dict, Optional

from aiohttp import ClientResponseError, ClientSession

from .const import USER_AGENT, OCEAN_URL, WIND_URL

_LOGGER = logging.getLogger(__name__)


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


def _first_ts_at_or_after(timeseries: list[dict], now_iso: str) -> Optional[dict]:
    """Finner første tidspunkt i en tidsserie som er lik eller etter gitt tidspunkt."""
    if not timeseries:
        return None
    for it in timeseries:
        t = it.get("time")
        if isinstance(t, str) and t >= now_iso:
            return it
    return timeseries[0]


class HavvarselApi:
    """Henter vind + hav fra MET."""

    def __init__(self, session: ClientSession) -> None:
        self._session = session

    async def _get_json(self, url: str, params: dict[str, Any]) -> dict:
        """Utfører et GET-kall til API-et og returnerer JSON."""
        headers = {
            "User-Agent": USER_AGENT,
            "Accept": "application/json",
            "Accept-Encoding": "identity",   # unngå gzip-varnish quirks
            "Host": "api.met.no",            # hjelper enkelte proxy-oppsett
            "Cache-Control": "no-cache",
        }

        _LOGGER.debug("Calling MET API: %s with params: %s", url, params)

        async with self._session.get(url, params=params, headers=headers, timeout=30) as resp:
            try:
                resp.raise_for_status()
            except ClientResponseError as e:
                text = await resp.text()
                _LOGGER.warning(
                    "MET-kall feilet %s (%s) %s?%s\nSvar: %s",
                    resp.status, e.message, url, resp.url.query_string, text[:500]
                )
                raise
            return await resp.json()

    async def _parse_ocean(self, ocean: dict, now_iso: str) -> Dict[str, Any]:
        """Parserer havdata fra oceanforecast/2.0/complete API-svaret."""
        out: Dict[str, Any] = {}
        ts = (ocean or {}).get("properties", {}).get("timeseries", [])
        item = _first_ts_at_or_after(ts, now_iso)
        details = (((item or {}).get("data") or {}).get("instant") or {}).get("details") or {}

        out["sea_water_temperature"] = details.get("sea_water_temperature")
        out["sea_water_speed"] = details.get("sea_water_speed")
        out["sea_water_to_direction"] = details.get("sea_water_to_direction")
        out["sea_surface_wave_height"] = details.get("sea_surface_wave_height")
        out["sea_surface_wave_from_direction"] = details.get("sea_surface_wave_from_direction")
        # Saltholdighet hentes separat fra Havvarsel (ikke her)
        out["ocean_time"] = (item or {}).get("time")

        # --- NYTT: prognoser (opptil 24 punkter fra og med nå) ---
        wave_fc: list[dict] = []
        current_fc: list[dict] = []
        count = 0
        for it in ts:
            t = it.get("time")
            if not isinstance(t, str) or t < now_iso:
                continue
            det = (((it.get("data") or {}).get("instant") or {}).get("details") or {})
            h = det.get("sea_surface_wave_height")
            s = det.get("sea_water_speed")
            if h is not None:
                wave_fc.append({"time": t, "value": h})
            if s is not None:
                current_fc.append({"time": t, "value": s})
            if h is not None or s is not None:
                count += 1
                if count >= 24:
                    break
        if wave_fc:
            out["sea_surface_wave_height_forecast"] = wave_fc
        if current_fc:
            out["sea_water_speed_forecast"] = current_fc
        # ---------------------------------------------------------

        return out

    async def _parse_wind(self, wind: dict, now_iso: str) -> Dict[str, Any]:
        """Parserer vinddata fra locationforecast/2.0/compact API-svaret."""
        out: Dict[str, Any] = {}
        ts = (wind or {}).get("properties", {}).get("timeseries", [])
        item = _first_ts_at_or_after(ts, now_iso)
        details = (((item or {}).get("data") or {}).get("instant") or {}).get("details") or {}

        out["wind_speed"] = details.get("wind_speed")
        out["wind_speed_of_gust"] = details.get("wind_speed_of_gust")
        out["wind_from_direction"] = details.get("wind_from_direction")
        if isinstance(out.get("wind_from_direction"), (int, float)):
            out["wind_from_cardinal"] = _deg_to_cardinal_16(float(out["wind_from_direction"]))

        out["wind_time"] = (item or {}).get("time")

        # --- NYTT: prognose (opptil 24 punkter fra og med nå) ---
        wind_fc: list[dict] = []
        count = 0
        for it in ts:
            t = it.get("time")
            if not isinstance(t, str) or t < now_iso:
                continue
            det = (((it.get("data") or {}).get("instant") or {}).get("details") or {})
            v = det.get("wind_speed")
            if v is not None:
                wind_fc.append({"time": t, "value": v})
                count += 1
                if count >= 24:
                    break
        if wind_fc:
            out["wind_speed_forecast"] = wind_fc
        # --------------------------------------------------------

        return out

    async def _fetch_salinity(self, lat: float, lon: float) -> Dict[str, Any]:
        """Henter saltholdighet spesifikt fra Havvarsel-v2 'dataprojection'."""
        salinity_url = (
            f"https://api.havvarsel.no/apis/duapi/havvarsel/v2/dataprojection/salinity/{lon}/{lat}"
        )

        # bruk hel time slik at alle kilder peker på samme timeslot
        now_iso = dt.datetime.utcnow().replace(minute=0, second=0, microsecond=0).isoformat() + "Z"
        salinity_params = {"depth": 0, "after": now_iso}

        headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}

        _LOGGER.debug("Calling Havvarsel Salinity API: %s with params: %s", salinity_url, salinity_params)

        async with self._session.get(salinity_url, params=salinity_params, headers=headers, timeout=30) as resp:
            try:
                resp.raise_for_status()
            except ClientResponseError as e:
                text = await resp.text()
                _LOGGER.warning(
                    "Havvarsel Salinity API kall feilet %s (%s) %s?%s\nSvar: %s",
                    resp.status, e.message, salinity_url, resp.url.query, text[:500]
                )
                return {}

            try:
                data = await resp.json()

                series = (data or {}).get("timeseries")
                if not series:
                    series = (data or {}).get("data") or []

                if not isinstance(series, list) or not series:
                    _LOGGER.warning("Salinity: tomt svar (after=%s)", now_iso)
                    return {}

                # Normaliser tid: bruk 'time' (ISO) hvis finnes, ellers 'raw_time/rawTime' (ms epoch)
                def _norm_time(it: dict) -> Optional[str]:
                    t = it.get("time")
                    if isinstance(t, str):
                        return t
                    rt = it.get("raw_time") or it.get("rawTime")
                    if isinstance(rt, (int, float)):
                        return dt.datetime.utcfromtimestamp(rt / 1000).replace(microsecond=0).isoformat() + "Z"
                    return None

                # sorter, finn valgt punkt (>= nå), og bygg også forecast-liste
                items: list[tuple[dict, str]] = []
                for it in series:
                    nt = _norm_time(it)
                    if nt:
                        items.append((it, nt))
                items.sort(key=lambda x: x[1])

                if not items:
                    _LOGGER.warning("Salinity: ingen gyldige tidsstempler i data (after=%s)", now_iso)
                    return {}

                chosen = None
                last_before = None
                for it, ts_iso in items:
                    if ts_iso >= now_iso and chosen is None:
                        chosen = (it, ts_iso)
                        break
                    last_before = (it, ts_iso)
                if chosen is None:
                    chosen = last_before

                first, t = chosen  # type: ignore[misc]

                def _find_salinity(it: dict) -> Optional[float]:
                    for kv in it.get("data") or []:
                        if kv.get("key") == "salinity":
                            return kv.get("value")
                    return None

                val = _find_salinity(first)

                # bygg forecast (opptil 24 punkter frem i tid)
                forecast: list[dict] = []
                for it, ts_iso in items:
                    if ts_iso < now_iso:
                        continue
                    fv = _find_salinity(it)
                    if fv is not None:
                        forecast.append({"time": ts_iso, "value": fv})
                        if len(forecast) >= 24:
                            break

                out: Dict[str, Any] = {"salinity_time": t}
                if val is not None:
                    out["sea_water_salinity"] = val
                if forecast:
                    out["sea_water_salinity_forecast"] = forecast
                return out

            except Exception as e:
                _LOGGER.error("Feil ved parsing av Havvarsel Salinity API svar: %s", e)
                return {}

    async def fetch(self, lat: float, lon: float) -> Dict[str, Any]:
        """Henter all nødvendig data fra METs API."""
        # rund ned til hel time så alle kilder bruker samme timeslot
        now_iso = dt.datetime.utcnow().replace(minute=0, second=0, microsecond=0).isoformat() + "Z"

        result: Dict[str, Any] = {}

        # 1) vind
        wind_params = {"lat": lat, "lon": lon}
        wind = await self._get_json(WIND_URL, wind_params)
        result.update(await self._parse_wind(wind, now_iso))

        # 2) hav (bølger/strøm/temperatur)
        ocean_params = {"lon": lon, "lat": lat}
        await asyncio.sleep(0.2)
        try:
            ocean = await self._get_json(OCEAN_URL, ocean_params)
            result.update(await self._parse_ocean(ocean, now_iso))
        except Exception as e:
            _LOGGER.warning("Kunne ikke hente havdata fra oceanforecast/2.0: %s", e)

        # 3) saltholdighet fra Havvarsel
        salinity_data = await self._fetch_salinity(lat, lon)
        result.update(salinity_data)

        return result
