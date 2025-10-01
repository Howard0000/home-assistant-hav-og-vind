# Hav og vind Lovelace Dashboard Kort

Dette er et konfigurerbart Lovelace Dashboard kort for Home Assistant som lar deg vise data fra din 'Hav og vind' integrasjon for forskjellige lokasjoner i ett og samme kort. Du kan enkelt bytte mellom lokasjonene ved hjelp av en rullegardinmeny.

## Funksjoner

*   Viser aktuelle værdata (sjøtemperatur, vindhastighet, vindretning, etc.) for valgt lokasjon.
*   Enkel veksling mellom dine konfigurerte lokasjoner via en rullegardinliste.
*   Automatisk generering av sensor-IDer basert på stedsnavnet du har gitt integrasjonen.

## Forutsetninger

For å bruke dette kortet, trenger du:

1.  **Home Assistant Community Store (HACS)**: Hvis du ikke allerede har det, installer HACS. Følg instruksjonene på [HACS offisielle nettside](https://hacs.xyz/).
2.  **`multiple-entity-row` Custom Card**: Dette kortet brukes for å vise flere attributter fra en dynamisk valgt entitet.
    *   I Home Assistant, gå til **HACS** -> **Frontend**.
    *   Klikk på 'Utforsk og last ned repositorier' (Explore & Download Repositories).
    *   Søk etter "Multiple-entity-row" og installer det.
    *   **Start Home Assistant på nytt** etter installasjon for å sikre at kortet lastes inn.
3.  **'Hav og vind' Home Assistant Integrasjon**: Din 'Hav og vind' integrasjon må være installert og konfigurert med de lokasjonene du ønsker å vise i kortet.

## Oppsett

Følg disse stegene for å sette opp kortet:

### 1. Opprett en `input_select` Helper

Denne helperen vil fungere som rullegardinlisten for å velge lokasjon i kortet ditt.

*   I Home Assistant, gå til **Innstillinger** > **Enheter og tjenester** > **Hjelpemidler** (Helpers).
*   Klikk på **Opprett hjelpemiddel** (Create Helper).
*   Velg **Rullegardinliste** (Dropdown).
*   Gi den et **Navn**: For eksempel, skriv `Hav og Vind Sted`. Home Assistant vil automatisk tildele den `entity_id: input_select.hav_og_vind_sted`. **Det er viktig at denne `entity_id` er nøyaktig `input_select.hav_og_vind_sted` slik at kortet kan referere til den.**
*   Under **Alternativer** (Options), legg inn de *nøyaktige* stedsnavnene du brukte da du konfigurerte 'Hav og vind' integrasjonen din. Dette må stemme overens med 'Navn' du ga hver lokasjon under integrasjonsoppsettet (f.eks. `Strømtangen Fyr`, `Færder Fyr`, `Hvaler`).

### 2. Legg til Kortet i Lovelace Dashboard

Nå skal du legge til selve kortet i ditt Home Assistant dashbord.

*   Naviger til dashbordet ditt i Home Assistant der du vil legge til kortet.
*   Klikk på de tre prikkene i øvre høyre hjørne og velg "Rediger dashbord".
*   Klikk på den blå "Legg til kort" (Add Card) knappen.
*   Bla ned og velg "Manuell kort" (Manual Card) for å lime inn YAML-konfigurasjonen.
*   **Kopier innholdet fra `hav_og_vind_dashboard_card.yaml`** (eller filen du har kalt den) og lim det inn i kodeeditoren.
*   **VIKTIG: Juster 'Fallback' Sensorer!**
    *   I den innsatte YAML-koden vil du se linjer som dette:
        ```yaml
        {% else %}
          sensor.hav_og_vind_stromtangen_fyr_sea_water_temperature # Erstatt denne!
        {% endif %}
        ```
    *   Du MÅ erstatte `sensor.hav_og_vind_stromtangen_fyr_sea_water_temperature` (og lignende linjer for andre sensorer) med den faktiske `entity_id`en for en av dine konfigurerte lokasjoner. Dette sikrer at kortet viser gyldige data selv om ingen lokasjon er valgt i rullegardinlisten, eller hvis et ugyldig valg er gjort.
    *   For å finne en gyldig `entity_id`: Gå til **Utviklerverktøy** > **Tilstander** i Home Assistant, og søk etter en av dine `hav_og_vind` sensorer (f.eks. `sensor.hav_og_vind_stromtangen_fyr_vindhastighet`). Velg en som fallback.
*   Klikk på "Lagre" (Save).
*   Klikk "Ferdig" (Done) i øvre høyre hjørne for å avslutte redigeringsmodus.

Gratulerer! Du har nå et dynamisk Hav- og Vinddata kort. Velg et sted fra rullegardinlisten, og se dataene oppdateres.

## Feilsøking

*   **Kortet viser "Entity not available":**
    *   Dobbeltsjekk at 'multiple-entity-row' er installert og at du har startet Home Assistant på nytt.
    *   Sørg for at `entity_id` for din `input_select` nøyaktig er `input_select.hav_og_vind_sted`.
    *   Sørg for at 'Alternativer' i din `input_select` helper nøyaktig stemmer overens med navnene du ga lokasjonene dine i 'Hav og vind' integrasjonen.
    *   Sjekk `entity_id`ene for dine faktiske `hav_og_vind` sensorer (i Utviklerverktøy > Tilstander) og sammenlign med hvordan de konstrueres i YAML-malen.
    *   Sørg for at fallback-sensorene du brukte er gyldige og eksisterer.
*   **Norske tegn fungerer ikke / feil sensor vises:**
    *   Sørg for at stedsnavnene i din `input_select` helper er skrevet akkurat som de er i integrasjonen din (f.eks. "Strømtangen Fyr"). Jinja2-malen håndterer konverteringen for `entity_id`.

---
