# Home Assistant – Hav og vind

Dette er en uoffisiell Home Assistant-integrasjon som henter data for **vær, vind, bølger, strøm, sjøtemperatur, saltholdighet** og **tidevann** basert på valgt posisjon.

- Vær/vind: MET Locationforecast
- Hav: MET Oceanforecast
- Sjøtemp/saltholdighet: havvarsel.no
- Tidevann: Kartverket (vannstand/tide)

## Dashboard

Integrasjonen er laget for å brukes sammen med et ferdig dashboard-oppsett.

Se `docs/dashboard/` for filer og forklaring.

## Installasjon

1. Installer via HACS (når repoet er publisert), eller kopier `custom_components/hav_og_vind/` til Home Assistant.
2. Legg til integrasjonen via **Innstillinger → Enheter og tjenester → Legg til integrasjon**.
3. Velg posisjon (lat/lon).

## Stasjonsvalg (dropdown)

Integrasjonen oppretter én global dropdown **“Aktiv stasjon”**. Dashboardet bruker proxy-entiteter som peker på valgt stasjon, slik at du kan legge til nye stasjoner uten å endre dashboardet.

## Personvern / vilkår

API-ene krever en fornuftig User-Agent. Denne integrasjonen sender en User-Agent som identifiserer prosjektet.
