# Dashboard – Hav og vind

Denne mappen inneholder et **eksempel på dashboard-oppsett** for Hav og vind-integrasjonen.

Dashboard-filen ligger **utenfor `custom_components/`** for å:
- holde selve integrasjonen ren og ryddig
- gjøre det enkelt å kopiere/tilpasse dashboardet til eget oppsett
- unngå at UI-oppsett blandes inn i kodebasen

---

## ✅ Anbefalt oppsett

- Dashboardet peker kun på **proxy-entiteter** (med faste `entity_id`-er), f.eks:
  - `sensor.hav_vind_vindhastighet`
  - `sensor.hav_vind_sjotemperatur`
  - `sensor.hav_vind_bolgehoyde`
  - `sensor.hav_vind_tidevann`
- Du velger aktiv stasjon i dropdown:
  - **Hav og vind – Aktiv stasjon**
- Når du legger til nye stasjoner:
  - ✅ Du trenger **ikke** å endre dashboardet  
  - 👉 Bare velg ønsket stasjon i dropdown

Dette gjør dashboardet **stasjons-uavhengig** og enkelt å vedlikeholde.

---

## 📁 Filer

- `lovelace_hav_og_vind.yaml`  
  Et ferdig eksempel på view/dashboard i YAML-format som kan:
  - kopieres rett inn i Home Assistant
  - importeres eller tilpasses etter eget behov

---

## ⚠️ Merk

Dashboard-filen er:
- valgfri
- kun et eksempel / startpunkt
- ikke nødvendig for at integrasjonen skal fungere


