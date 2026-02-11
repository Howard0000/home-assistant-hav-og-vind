# Hav og vind for Home Assistant

**Norsk** · [English](README.en.md)

![HACS](https://img.shields.io/badge/HACS-Default-orange.svg)

En moderne og brukervennlig integrasjon for å hente **vær-, hav- og tidevannsdata**
fra **MET Norway**, **Havvarsel** og **Kartverket** inn i Home Assistant.

Integrasjonen lar deg:
- legge til **flere lokasjoner**
- velge **aktiv stasjon** via en dropdown
- bruke **proxy-sensorer** som automatisk følger valgt stasjon
- vise både **nåverdier og prognoser** for vind, bølger, strøm, temperatur, saltholdighet og tidevann

Dette er en *custom component* som konfigureres fullt ut via Home Assistant sitt UI –  
ingen YAML kreves for grunnoppsett.

![Dekningskart](images/dekning.png)

---

## Funksjoner

### 🌍 Flere lokasjoner
- Legg til så mange lokasjoner du vil (én config entry per sted)
- Hver lokasjon får egne sensorer basert på koordinater

### 📍 Aktiv stasjon (global)
- Én global dropdown: **“Aktiv stasjon”**
- Proxy-sensorene (`sensor.hav_vind_*`) viser alltid data fra valgt stasjon
- Perfekt for dashboards, grafer og automasjoner som skal være stasjons-uavhengige

### 🌬️ Vær (MET Norway)
- Vindhastighet
- Vindkast
- Vindretning
- Lufttemperatur
- Luftfuktighet
- Lufttrykk (MSL)
- Skylag
- Nedbør (1t)
- Prognoser for de fleste verdier

### 🌊 Hav (MET + Havvarsel)
- Sjøtemperatur (primært fra Havvarsel, fallback til MET Ocean)
- Strømhastighet og strømretning
- Signifikant bølgehøyde og bølgeretning
- Saltholdighet
- Prognoser der tilgjengelig

### 🌒 Tidevann (Kartverket)
- Nåverdi / prediksjon
- Prognoseserier
- Observasjoner (der tilgjengelig)
- Serier trimmes automatisk for å unngå HA sine attributt-begrensninger

### 🧭 Proxy-sensorer (for dashboard-bruk)
F.eks:
- `sensor.hav_vind_vindhastighet`
- `sensor.hav_vind_sjotemperatur`
- `sensor.hav_vind_bolgehoyde`
- `sensor.hav_vind_tidevann`

Disse følger automatisk valgt **Aktiv stasjon**.

---

## 📥 Krav

- Home Assistant 2024.x eller nyere  
- HACS installert (anbefalt)

---

## 📦 Installasjon (HACS)

1. Åpne **HACS → Integrations**
2. Søk etter **Hav og vind**
3. Klikk **Install**
4. Start Home Assistant på nytt om nødvendig

---

## ⚙️ Konfigurasjon

1. Gå til **Innstillinger → Enheter og tjenester**
2. Klikk **Legg til integrasjon**
3. Søk etter **Hav og vind**
4. Fyll inn:
   - Navn på lokasjon
   - Breddegrad
   - Lengdegrad
5. Fullfør

Gjenta for flere lokasjoner om ønskelig.

### Endre oppdateringsintervall
- Gå til **Innstillinger → Enheter og tjenester → Hav og vind → Konfigurer**
- Juster **Oppdateringsintervall (minutter)**

---

## 📊 Sensorer og enheter

Hver lokasjon opprettes som en egen **Enhet** i Home Assistant, med sensorer for:
- Vær (MET)
- Hav (MET + Havvarsel)
- Tidevann (Kartverket)

I tillegg opprettes:
- Én global **“Aktiv stasjon”** select-entity
- En rekke **proxy-sensorer** (`sensor.hav_vind_*`) som følger valgt stasjon

---

## 🧠 Datakilder

- **MET Norway** – vær og hav (OceanForecast)
- **Havvarsel** – sjøtemperatur og saltholdighet
- **Kartverket** – tidevann

Alle data hentes direkte fra åpne, offentlige API-er.

---

## 🛠 Feilsøking

- Sjekk **Innstillinger → System → Logger** for:
- Hvis en sensor er `unavailable`, sjekk:
- At valgt stasjon finnes
- At API-et leverer data for området
- Nettverk / internettilgang

---

## 🙏 Anerkjennelser

Utviklet og vedlikeholdt av [@Howard0000](https://github.com/Howard0000).  
KI-assistent brukt til feilsøking og dokumentasjon.

---

## 📄 Lisens

MIT License

---

## 🏷 Varemerker og navn

- **MET Norway**, **Kartverket** og **Havvarsel** sine navn og tjenester tilhører respektive eiere  
- Brukes kun for identifikasjon av datakilder

Dette er et uoffisielt community-prosjekt og er ikke utviklet, støttet eller godkjent av
MET Norway, Kartverket eller Havvarsel.

---

## ⚠️ Ansvarsfraskrivelse

Denne integrasjonen leverer **informasjons- og beslutningsstøtte** basert på åpne datakilder.

All bruk skjer på eget ansvar.  
Data kan være forsinket, ufullstendig eller feil.

Ikke bruk denne integrasjonen som eneste beslutningsgrunnlag for sikkerhetskritiske formål
(sjøfart, værkritiske operasjoner, etc.).

