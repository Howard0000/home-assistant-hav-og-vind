from __future__ import annotations

DOMAIN = "hav_og_vind"

# Oppdateringsintervall (minutter) brukt av koordinatoren
DEFAULT_SCAN_MINUTES = 30

CONF_SCAN_INTERVAL_MINUTES = "scan_interval_minutes"


USER_AGENT = "HavOgVind/0.1 (Home Assistant; contact: 146569636+Howard0000@users.noreply.github.com)"


OCEAN_URL = "https://api.met.no/weatherapi/oceanforecast/2.0/complete"
WIND_URL = "https://api.met.no/weatherapi/locationforecast/2.0/complete"


HAVVARSEL_TEMP_URL_FMT = "https://api.havvarsel.no/apis/duapi/havvarsel/v2/temperatureprojection/{lon}/{lat}"

HAVVARSEL_SALINITY_URL_FMT = "https://api.havvarsel.no/apis/duapi/havvarsel/v2/dataprojection/salinity/{lon}/{lat}"
