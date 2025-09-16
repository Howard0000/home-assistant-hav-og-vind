from __future__ import annotations

from typing import Any
from aiohttp import ClientSession

class HavvarselApi:
    def __init__(self, session: ClientSession, user_agent: str):
        self._session = session
        self._ua = user_agent

    async def fetch_projection(self, lon: float, lat: float) -> dict[str, Any] | None:
        url = f"https://api.havvarsel.no/apis/duapi/havvarsel/v2/temperatureprojection/{lon}/{lat}"
        headers = {"User-Agent": self._ua, "Accept": "application/json"}
        async with self._session.get(url, headers=headers, timeout=30) as resp:
            if resp.status != 200:
                return None
            return await resp.json()
