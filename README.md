# Havvarsel – Home Assistant-integrasjon (IMR)
Enkel HACS‑klar integrasjon som henter **sjøtemperatur (°C)** og **saltholdighet (PSU)** fra **Havvarsel (IMR)**.
Støtter flere lokasjoner via GUI (lat/lon), og eksponerer flere døgn med prognoser for pene grafer i Lovelace.

> **Data-kilde:** Havvarsel API (IMR): `https://api.havvarsel.no/...`  
> **Lisens/bruk:** Følg Havvarsel/IMR sine vilkår. Husk å sette en *User-Agent* med kontaktinfo i `const.py`.

## Installere via HACS (Custom repo)
1. Åpne **HACS → Integrations → ⋮ → Custom repositories**.
2. Lim inn repo‑URL (ditt GitHub‑repo), velg **Integration**.
3. Installer **Havvarsel (IMR)** og restart Home Assistant.
4. Legg til integrasjonen: **Settings → Devices & services → Add integration → Havvarsel**.

## Legg til lokasjon
I dialogen skriver du **Navn**, **Latitude**, **Longitude** og ev. **Oppdateringsintervall** + **Forecast timer**.

## Sensorer
- `sjøtemperatur` (°C)
- `saltholdighet` (PSU)

Begge har attributter:
- `forecast_series_temp` / `forecast_series_sal` = liste `{time, value}` for inntil *forecast_hours* frem.
- `model_time` = første punkt i serien.

## Lovelace – ApexCharts (multi‑døgn temperatur + salinitet)
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
      return s.map(p => [new Date(p.time).getTime(), p.value]);
  - entity: sensor.<navn>_saltholdighet
    name: Saltholdighet
    yaxis_id: sal
    data_generator: |
      const s = entity.attributes.forecast_series_sal || [];
      return s.map(p => [new Date(p.time).getTime(), p.value]);
yaxis:
  - id: temp
    decimalsInFloat: 1
  - id: sal
    opposite: true
    decimalsInFloat: 1
```

## Konfigurasjon
- **User‑Agent** settes i `custom_components/havvarsel/const.py`. Legg inn din kontakt (epost/URL).
- **Oppdateringsintervall** (sek) og **Forecast timer** kan endres i **Options** etterpå.

## Ikoner
Legg dine `icon.png` og `icon@2x.png` i `custom_components/havvarsel/` (de brukes av HACS / UI).

## Endringslogg
Se `CHANGELOG.md`.
