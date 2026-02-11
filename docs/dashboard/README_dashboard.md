# Dashboard – Hav og vind

Denne mappen inneholder **eksempel på dashboard-oppsett** for Hav og vind-integrasjonen.

Dashboard-filene ligger **utenfor `custom_components/`** for å:
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

Dette gjør dashboardet **stasjons-uavhengig** og veldig enkelt å vedlikeholde.

---

## 📁 Filer

- `Dashboard.js`  
  Dine eksisterende dashboard-notater / byggefil.  
  Ligger her for å holde selve integrasjonen “ren”.

- `lovelace_hav_og_vind.yaml`  
  (Valgfritt) Et ferdig eksempel på view/dashboard i YAML-format som kan:
  - kopieres rett inn i Home Assistant
  - importeres eller tilpasses etter eget behov

---

## 💡 Tips

- Bruk alltid **proxy-sensorene** i dashboardet – ikke stasjonsspesifikke sensorer  
- Da slipper du å oppdatere kort, grafer og views når du:
  - legger til nye stasjoner
  - bytter aktiv stasjon
  - rydder i entiteter

---

## ⚠️ Merk

Dashboard-filene her er ment som:
- inspirasjon
- eksempeloppsett
- startpunkt for eget dashboard

De er **ikke påkrevd** for at integrasjonen skal fungere.

