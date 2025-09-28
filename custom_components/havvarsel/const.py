# custom_components/hav_og_vind/const.py
from __future__ import annotations

DOMAIN = "hav_og_vind"

DEFAULT_SCAN_MINUTES = 30
USER_AGENT = "HavOgVind/0.1 (Home Assistant; contact: 146569636+Howard0000@users.noreply.github.com)"

OCEAN_URL = "https://api.met.no/weatherapi/oceanforecast/2.0/complete"
WIND_URL = "https://api.met.no/weatherapi/locationforecast/2.0/compact"

# Konstanter for sensorer (fra din plan)
# Disse vil bli brukt i sensor.py, men det er ofte ryddig å ha dem her også hvis de er globale
# Selv om de defineres i sensor.py, er det greit å ha dem i tankene.
