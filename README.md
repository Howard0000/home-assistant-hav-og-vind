# Havvarsel – Home Assistant-integrasjon (IMR, JSON)
Henter **sjøtemperatur (°C)** og **saltholdighet (PSU)** fra **Havvarsel (IMR)** via **JSON** (raskere og enklere enn XML).
Hvis API-et returnerer ekstra felter i samme serie (vind/strøm), eksponeres også disse.

## Funksjoner
- GUI‑oppsett (config flow): navn, lat/lon, intervall, prognoselengde
- Multi‑døgn forecast: `forecast_series_temp` / `forecast_series_sal`
- Auto‑deteksjon av vind/strøm i “bundlet” JSON (legger til sensorer ved behov)
- HACS‑klar

## Dekningsområde
Integrasjonen er relevant for **Norge, Sverige og Danmark** (Havvarsel-modellens dekningsområde).  
![Dekningskart](image/dekning.png)

## Lovelace – ApexCharts (temp + salinitet)
```yaml
type: custom:apexcharts-card
graph_span: 4d
now:
  show: true
series:
  - entity: sensor.<navn>_sjotemperatur
    name: Sjøtemp
    data_generator: |
      const s = entity.attributes.forecast_series_temp || [];
      return s.map(p => [p.time, p.value]);
  - entity: sensor.<navn>_saltholdighet
    name: Saltholdighet
    yaxis_id: sal
    data_generator: |
      const s = entity.attributes.forecast_series_sal || [];
      return s.map(p => [p.time, p.value]);
yaxis:
  - id: temp
  - id: sal
    opposite: true
```

## Viktig
- Sett `USER_AGENT` i `custom_components/havvarsel/const.py` med kontaktinfo (IMR krever dette).
- HACS: legg repoet til som *Custom repository* (Integration) og installer derfra.
