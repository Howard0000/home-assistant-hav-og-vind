DOMAIN = "havvarsel"
DEFAULT_SCAN_INTERVAL = 1800  # 30 min
DEFAULT_FORECAST_HOURS = 120  # 5 døgn
# Stier per variabel. Flere kan legges til senere (f.eks. current, wind hvis tilgjengelig som egne endepunkt).
ENDPOINTS = {
    "temperature": "temperatureprojection/{lon}/{lat}",
    "salinity":    "salinityprojection/{lon}/{lat}",
}
API_BASE = "https://api.havvarsel.no/apis/duapi/havvarsel/v2/"
USER_AGENT = "homeassistant-havvarsel (contact@example.com)"  # <-- Sett din kontaktinfo
