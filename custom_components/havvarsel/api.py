from __future__ import annotations

from typing import Any, List
from aiohttp import ClientSession
from .const import API_BASE, ENDPOINTS

class HavvarselApi:
    def __init__(self, session: ClientSession, user_agent: str):
        self._session = session
        self._ua = user_agent

    async def _get_json(self, path: str) -> Any:
        url = API_BASE + path
        headers = {"User-Agent": self._ua, "Accept": "application/json"}
        async with self._session.get(url, headers=headers, timeout=30) as resp:
            if resp.status != 200:
                return None
            return await resp.json()

    async def fetch_variable(self, lon: float, lat: float, variable: str):
        tmpl = ENDPOINTS.get(variable)
        if not tmpl:
            return None
        path = tmpl.format(lon=lon, lat=lat)
        return await self._get_json(path)

    @staticmethod
    def merge_series_by_time(*series: List[dict]) -> List[dict]:
        """
        Slår sammen flere serier på tid. Støtter to former:
        A) {"data":[{"rawTime": <ms>, "value": <num>}, ...], "metadata": {...}}
        B) [{"raw_time": <ms>, "temperature":..., "salinity":..., "wind_length":..., ...}, ...]
        Returnerer: liste av dict med "raw_time" + funnede variabler.
        """
        merged = {}

        def put(ms: int, key: str, val):
            d = merged.setdefault(ms, {"raw_time": ms})
            d[key] = val

        for s in series:
            if not s:
                continue
            if isinstance(s, dict) and isinstance(s.get("data"), list):
                # Forsøk å navngi variabel basert på metadata
                meta = s.get("metadata", {})
                varname = (meta.get("name") or meta.get("standard_name") or "value").lower()
                key = "temperature" if "temp" in varname else ("salinity" if "sal" in varname else varname)
                for p in s["data"]:
                    ms = p.get("rawTime") or p.get("raw_time")
                    val = p.get("value")
                    if ms is None or val is None:
                        continue
                    try:
                        ms = int(ms)
                        val = float(val)
                    except Exception:
                        pass
                    put(ms, key, val)
            elif isinstance(s, list):
                for p in s:
                    ms = p.get("raw_time") or p.get("rawTime")
                    if ms is None:
                        continue
                    try:
                        ms = int(ms)
                    except Exception:
                        continue
                    rec = merged.setdefault(ms, {"raw_time": ms})
                    for k, v in p.items():
                        if k in ("raw_time", "rawTime") or v is None:
                            continue
                        rec[k] = v
        return [merged[k] for k in sorted(merged.keys())]
