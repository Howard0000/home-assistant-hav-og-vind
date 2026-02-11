# Dashboard – Hav og vind

Denne mappen inneholder et **ferdig eksempel-dashboard** for Hav og vind-integrasjonen.

Dashboard-filen ligger **utenfor `custom_components/`** for å:
- holde selve integrasjonen ren og ryddig
- gjøre det enkelt å kopiere/tilpasse dashboardet til eget oppsett
- unngå at UI-oppsett blandes inn i kodebasen

> 💡 **Kort sagt:** Integrasjonen fungerer uten dashboardet, men **hele oppsettet er laget for at dette dashboardet skal være enkelt å bruke og vedlikeholde** – uansett hvor mange lokasjoner du legger til.

---

## ✅ Anbefalt oppsett

- Dashboardet peker kun på **proxy-entiteter** (faste `entity_id`-er), f.eks:
  - `sensor.hav_vind_vindhastighet`
  - `sensor.hav_vind_sjotemperatur`
  - `sensor.hav_vind_bolgehoyde`
  - `sensor.hav_vind_tidevann`

- Du velger aktiv stasjon i dropdown:
  - `select.hav_og_vind_aktiv_stasjon` (**Hav og vind – Aktiv stasjon**)

- Når du legger til nye stasjoner:
  - ✅ Du trenger **ikke** å endre dashboardet
  - 👉 Bare velg ønsket stasjon i dropdown

Dette gjør dashboardet **stasjons-uavhengig**, og du slipper å vedlikeholde entity_id-er per lokasjon.

---

## 📁 Filer

- `lovelace_hav_og_vind.yaml`  
  Et ferdig eksempel på view/dashboard i YAML-format.

---

## 📌 Krav for å bruke dashboardet

Dashboardet bruker noen vanlige HACS-kort:

- `custom:button-card`
- `custom:apexcharts-card`
- Mushroom cards

> Hvis du ikke bruker disse, kan du fortsatt bruke integrasjonen – men da må dashboardet tilpasses.

---

## ⚙️ Hvordan ta det i bruk

Dette eksempelet er laget for **Lovelace YAML / Raw mode**.

1. Åpne Home Assistant → **Dashboards**
2. Opprett nytt dashboard (YAML mode) eller bruk Raw editor
3. Lim inn innholdet fra `lovelace_hav_og_vind.yaml`
4. Sørg for at integrasjonen er installert og at du har lagt til minst én lokasjon
5. Velg ønsket stasjon i **Hav og vind – Aktiv stasjon**

---

## ⚠️ Merk

Dashboardet er:
- valgfritt (integrasjonen fungerer uten)
- et eksempel / startpunkt
- laget for å vise **full nytte** av proxy-sensorene og aktiv stasjon


