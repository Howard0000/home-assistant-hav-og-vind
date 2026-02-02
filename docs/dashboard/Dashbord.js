button_card_templates:
  weather_tile:
    show_icon: false
    show_state: false
    show_name: true
    show_label: true
    tap_action:
      action: none
    hold_action:
      action: more-info
    double_tap_action:
      action: more-info
    styles:
      card:
        - text-align: center
        - padding: 18px 14px
        - border-radius: 18px
        - display: flex
        - flex-direction: column
        - justify-content: center
        - align-items: center
        - min-height: 170px
      name:
        - font-size: 18px
        - font-weight: 700
        - line-height: 1.1
        - margin-top: 6px
        - margin-bottom: 6px
      label:
        - margin-top: 4px
        - font-size: 14px
        - line-height: 1.6
        - white-space: normal
    triggers_update:
      - select.hav_og_vind_aktiv_stasjon
      - sensor.hav_vind_skydekke
      - sensor.hav_vind_nedbor_1t
      - sensor.hav_vind_vindhastighet
      - sensor.hav_vind_vindretning
      - sensor.hav_vind_stromretning
      - sensor.hav_vind_stromhastighet
      - sensor.hav_vind_bolgeretning
    name: |-
      [[[
        const h = Number(variables?.h || 0);
        const title = variables?.title_text || (h ? `+${h} t` : 'Vær Nå');

        const s = (e)=>states[e];
        const pfx = 'sensor.hav_vind_';

        const tIso = new Date(Date.now() + h*3600000).toISOString();

        const pick = (arr)=> {
          if (!Array.isArray(arr)) return null;

          const t = new Date(tIso).getTime();
          let best = null;
          let bestTs = -Infinity;

          for (const x of arr) {
            if (!x?.time || x?.value == null) continue;
            const ts = new Date(x.time).getTime();
            if (ts <= t && ts > bestTs) {
              bestTs = ts;
              best = x.value;
            }
          }
          return best;
        };

        // Sky (forecast -> prosent)
        let c = Number(pick(s(pfx+'skydekke')?.attributes?.cloud_area_fraction_forecast));
        if (!Number.isFinite(c)) c = Number(s(pfx+'skydekke')?.state) || 0;
        const cloudPct = Number.isFinite(c) ? (c > 1 ? c : c * 100) : 0;

        // Nedbør (forecast)
        let p = Number(pick(s(pfx+'nedbor_1t')?.attributes?.precipitation_amount_1h_forecast));
        if (!Number.isFinite(p)) p = Number(s(pfx+'nedbor_1t')?.state) || 0;

        const emoji =
          p >= 4 ? '🌧️' :
          p >= 1 ? '🌦️' :
          (cloudPct < 20 ? '☀️' : cloudPct < 60 ? '🌤️' : '☁️');

        return `<div style="font-size:52px;line-height:1;margin-bottom:6px">${emoji}</div>${title}`;
      ]]]
    label: |-
      [[[
        const s = (e)=>states[e];
        const pfx = 'sensor.hav_vind_';

        const h = Number(variables?.h || 0);
        const tIso = new Date(Date.now() + h*3600000).toISOString();

        const pick = (arr)=> {
          if (!Array.isArray(arr)) return null;

          const t = new Date(tIso).getTime();
          let best = null;
          let bestTs = -Infinity;

          for (const x of arr) {
            if (!x?.time || x?.value == null) continue;
            const ts = new Date(x.time).getTime();
            if (ts <= t && ts > bestTs) {
              bestTs = ts;
              best = x.value;
            }
          }
          return best;
        };

        const dirs = ['N','NØ','Ø','SØ','S','SV','V','NV'];
        const dir = (deg)=> dirs[Math.floor(((Number(deg)||0)+22.5)/45)%8];

        // Sky
        let c = Number(pick(s(pfx+'skydekke')?.attributes?.cloud_area_fraction_forecast));
        if (!Number.isFinite(c)) c = Number(s(pfx+'skydekke')?.state) || 0;
        const cloud = (c>1 ? c : c*100).toFixed(0);

        // Nedbør
        let p = Number(pick(s(pfx+'nedbor_1t')?.attributes?.precipitation_amount_1h_forecast));
        if (!Number.isFinite(p)) p = Number(s(pfx+'nedbor_1t')?.state) || 0;

        // Vind
        let ws = Number(pick(s(pfx+'vindhastighet')?.attributes?.wind_speed_forecast));
        if (!Number.isFinite(ws)) ws = Number(s(pfx+'vindhastighet')?.state) || 0;

        const wd_deg =
          pick(s(pfx+'vindretning')?.attributes?.wind_from_direction_forecast) ??
          pick(s(pfx+'vindhastighet')?.attributes?.wind_from_direction_forecast) ??
          s(pfx+'vindretning')?.state;

        const wd = dir(wd_deg);

        // Strømhastighet – prøv flere forecast-nøkler
        const speedKeys = [
          'sea_water_speed_forecast',
          'sea_water_current_speed_forecast',
          'current_speed_forecast',
          'sea_current_speed_forecast'
        ];
        const src = s(pfx+'stromhastighet');
        const spArr = speedKeys.map(k => src?.attributes?.[k]).find(a => Array.isArray(a)) || [];

        let cs = Number(pick(spArr));
        if (!Number.isFinite(cs)) cs = Number(src?.state);
        const csTxt = Number.isFinite(cs) ? `${cs.toFixed(1)} m/s` : '';

        // Strømretning
        const cd_src = s(pfx+'stromretning');
        const cd_deg =
          pick(cd_src?.attributes?.sea_water_to_direction_forecast) ??
          cd_src?.state;
        const cd = dir(cd_deg);

        // Bølgeretning
        const wv_src = s(pfx+'bolgeretning');
        const wd2_deg =
          pick(wv_src?.attributes?.sea_surface_wave_from_direction_forecast) ??
          wv_src?.state;
        const wd2 = dir(wd2_deg);

        return `
          ☁️ Skydekke: ${cloud}%<br>
          🌧️ Regn: ${p.toFixed(1)} mm<br>
          🧭 Vind: ${wd} ${ws.toFixed(1)} m/s<br>
          🔶 Strøm: ${cd}${csTxt ? ' ' + csTxt : ''}<br>
          🌊 Bølger: ${wd2}
        `;
      ]]]
views:
  - title: Home
    cards:
      - type: vertical-stack
        cards:
          - type: custom:mushroom-title-card
            title: 🌥️ Vær nå
          - type: custom:button-card
            template: weather_tile
            variables:
              h: 0
              title_text: Vær Nå
      - type: vertical-stack
        cards:
          - type: custom:mushroom-title-card
            title: 🌬️ Vind
          - type: custom:apexcharts-card
            graph_span: 24h
            span:
              offset: +23h
            now:
              show: true
              label: Nå
            header:
              show: true
              title: 🌬️ Vindhastighet & kast (prognose)
              show_states: true
              colorize_states: true
            apex_config:
              chart:
                height: 230
                toolbar:
                  show: false
                sparkline:
                  enabled: false
              xaxis:
                type: datetime
                labels:
                  show: true
              stroke:
                curve: smooth
              grid:
                show: true
                strokeDashArray: 3
                yaxis:
                  lines:
                    show: true
                xaxis:
                  lines:
                    show: false
                padding:
                  left: 12
                  right: 6
                  bottom: 6
              markers:
                size: 0
                strokeWidth: 0
                hover:
                  size: 0
              tooltip:
                shared: true
                intersect: false
                'y':
                  formatter: |
                    EVAL:(v)=> v!=null ? `${Number(v).toFixed(1)} m/s` : '–'
            yaxis:
              - decimals: 0
                apex_config:
                  title:
                    text: m/s
            series:
              - entity: sensor.hav_vind_vindkast
                name: Vindkast
                color: '#fb8c00'
                stroke_width: 4
                show:
                  legend_value: false
                  in_header: false
                  extremas: true
                data_generator: >
                  const nowTs = Date.now();

                  const arr = entity && entity.attributes ?
                  (entity.attributes.wind_speed_of_gust_forecast || []) : [];

                  if (!Array.isArray(arr)) return [];

                  const pts = arr
                    .filter(e => e && e.time && e.value != null)
                    .map(e => [new Date(e.time).getTime(), Number(e.value)])
                    .sort((a, b) => a[0] - b[0]);

                  let lastBefore = null;

                  for (const p of pts) {
                    if (p[0] <= nowTs) lastBefore = p;
                    else break;
                  }

                  const out = pts.filter(p => p[0] >= nowTs); if (lastBefore)
                  out.unshift(lastBefore);

                  return out;
              - entity: sensor.hav_vind_vindhastighet
                name: Vindhastighet
                color: '#1e88e5'
                stroke_width: 4
                show:
                  legend_value: false
                  in_header: false
                  extremas: true
                data_generator: >
                  const nowTs = Date.now();

                  const arr = entity && entity.attributes ?
                  (entity.attributes.wind_speed_forecast || []) : [];

                  if (!Array.isArray(arr)) return [];

                  const pts = arr
                    .filter(e => e && e.time && e.value != null)
                    .map(e => [new Date(e.time).getTime(), Number(e.value)])
                    .sort((a, b) => a[0] - b[0]);

                  let lastBefore = null;

                  for (const p of pts) {
                    if (p[0] <= nowTs) lastBefore = p;
                    else break;
                  }

                  const out = pts.filter(p => p[0] >= nowTs); if (lastBefore)
                  out.unshift(lastBefore);

                  return out;
              - entity: sensor.hav_vind_vindhastighet
                name: Nå
                show:
                  in_chart: false
                  in_header: true
                  legend_value: false
                data_generator: >
                  const nowTs = Date.now();

                  const arr = entity && entity.attributes ?
                  (entity.attributes.wind_speed_forecast || []) : [];

                  if (!Array.isArray(arr) || arr.length === 0) return [];

                  const pts = arr
                    .filter(e => e && e.time && e.value != null)
                    .map(e => [new Date(e.time).getTime(), Number(e.value)])
                    .sort((a, b) => a[0] - b[0]);

                  let lastBefore = null;

                  for (const p of pts) {
                    if (p[0] <= nowTs) lastBefore = p;
                    else break;
                  }

                  const p = lastBefore ? lastBefore : pts[0]; return [[p[0],
                  p[1]]];
      - type: vertical-stack
        cards:
          - type: custom:mushroom-title-card
            title: 🌤️ Vær om 3 timer
          - type: custom:button-card
            template: weather_tile
            variables:
              h: 3
              title_text: +3 t
      - type: vertical-stack
        cards:
          - type: custom:mushroom-title-card
            title: 🌡️ Sjøtemperatur
          - type: custom:apexcharts-card
            graph_span: 24h
            span:
              offset: +23h
            now:
              show: true
              label: Nå
            header:
              show: true
              title: 🌡️ Sjøtemperatur (prognose)
              show_states: true
            apex_config:
              chart:
                height: 230
                toolbar:
                  show: false
                sparkline:
                  enabled: false
              xaxis:
                type: datetime
                labels:
                  show: true
              stroke:
                curve: smooth
              legend:
                show: true
              grid:
                show: true
                strokeDashArray: 3
                yaxis:
                  lines:
                    show: true
                xaxis:
                  lines:
                    show: false
                padding:
                  left: 12
                  right: 6
                  bottom: 6
              markers:
                size: 0
                strokeWidth: 0
                hover:
                  size: 0
              tooltip:
                'y':
                  formatter: |
                    EVAL:(v)=> v!=null ? `${Number(v).toFixed(1)} °C` : '–'
            yaxis:
              - decimals: 1
                apex_config:
                  title:
                    text: °C
            series:
              - entity: sensor.hav_vind_sjotemperatur
                name: Sjøtemperatur
                color: '#e53935'
                stroke_width: 4
                show:
                  legend_value: false
                  in_header: false
                  extremas: true
                data_generator: >
                  const nowTs = Date.now();

                  const arr = entity && entity.attributes ?
                  (entity.attributes.sea_water_temperature_forecast || []) : [];

                  if (!Array.isArray(arr)) return [];

                  const pts = arr
                    .filter(e => e && e.time && e.value != null)
                    .map(e => [new Date(e.time).getTime(), Number(e.value)])
                    .sort((a, b) => a[0] - b[0]);

                  let lastBefore = null; for (const p of pts) {
                    if (p[0] <= nowTs) lastBefore = p;
                    else break;
                  }

                  const out = pts.filter(p => p[0] >= nowTs); if (lastBefore)
                  out.unshift(lastBefore);

                  return out;
              - entity: sensor.hav_vind_sjotemperatur
                name: Nå
                show:
                  in_chart: false
                  in_header: true
                  legend_value: false
                data_generator: >
                  const nowTs = Date.now();

                  const arr = entity && entity.attributes ?
                  (entity.attributes.sea_water_temperature_forecast || []) : [];

                  if (!Array.isArray(arr) || arr.length === 0) return [];

                  const pts = arr
                    .filter(e => e && e.time && e.value != null)
                    .map(e => [new Date(e.time).getTime(), Number(e.value)])
                    .sort((a, b) => a[0] - b[0]);

                  let lastBefore = null; for (const p of pts) {
                    if (p[0] <= nowTs) lastBefore = p;
                    else break;
                  }

                  const p = lastBefore ? lastBefore : pts[0]; return [[p[0],
                  p[1]]];
      - type: vertical-stack
        cards:
          - type: custom:mushroom-title-card
            title: 🌤️ Vær om 12 timer og 24 timer
          - type: grid
            columns: 2
            square: false
            cards:
              - type: custom:button-card
                template: weather_tile
                variables:
                  h: 12
                  title_text: +12 t
              - type: custom:button-card
                template: weather_tile
                variables:
                  h: 24
                  title_text: +24 t
      - type: vertical-stack
        cards:
          - type: custom:mushroom-title-card
            title: 🌧️ Nedbør
          - type: custom:apexcharts-card
            graph_span: 24h
            span:
              offset: +23h
            now:
              show: true
              label: Nå
            header:
              show: true
              title: 🌧️ Nedbør (prognose)
              show_states: true
            apex_config:
              chart:
                height: 230
                toolbar:
                  show: false
                sparkline:
                  enabled: false
              xaxis:
                type: datetime
                labels:
                  show: true
              stroke:
                curve: smooth
              legend:
                show: true
              grid:
                show: true
                strokeDashArray: 3
                yaxis:
                  lines:
                    show: true
                xaxis:
                  lines:
                    show: false
                padding:
                  left: 12
                  right: 6
                  bottom: 6
              plotOptions:
                bar:
                  columnWidth: 60%
              tooltip:
                'y':
                  formatter: |
                    EVAL:(v)=> v!=null ? `${Number(v).toFixed(1)} mm` : '–'
            yaxis:
              - decimals: 1
                apex_config:
                  title:
                    text: mm
            series:
              - entity: sensor.hav_vind_nedbor_1t
                name: Nedbør
                type: column
                color: '#42a5f5'
                stroke_width: 2
                show:
                  legend_value: false
                  in_header: false
                  extremas: true
                data_generator: >
                  const nowTs = Date.now();

                  const arr = entity && entity.attributes ?
                  (entity.attributes.precipitation_amount_1h_forecast || []) :
                  [];

                  if (!Array.isArray(arr)) return [];

                  const pts = arr
                    .filter(e => e && e.time && e.value != null)
                    .map(e => [new Date(e.time).getTime(), Number(e.value)])
                    .sort((a, b) => a[0] - b[0]);

                  let lastBefore = null; for (const p of pts) {
                    if (p[0] <= nowTs) lastBefore = p;
                    else break;
                  }

                  const out = pts.filter(p => p[0] >= nowTs); if (lastBefore)
                  out.unshift(lastBefore);

                  return out;
              - entity: sensor.hav_vind_nedbor_1t
                name: Nå
                show:
                  in_chart: false
                  in_header: true
                  legend_value: false
                data_generator: >
                  const nowTs = Date.now();

                  const arr = entity && entity.attributes ?
                  (entity.attributes.precipitation_amount_1h_forecast || []) :
                  [];

                  if (!Array.isArray(arr) || arr.length === 0) return [];

                  const pts = arr
                    .filter(e => e && e.time && e.value != null)
                    .map(e => [new Date(e.time).getTime(), Number(e.value)])
                    .sort((a, b) => a[0] - b[0]);

                  let lastBefore = null; for (const p of pts) {
                    if (p[0] <= nowTs) lastBefore = p;
                    else break;
                  }

                  const p = lastBefore ? lastBefore : pts[0]; return [[p[0],
                  p[1]]];
      - type: vertical-stack
        cards:
          - type: custom:mushroom-title-card
            title: 🧂 Saltholdighet
          - type: custom:apexcharts-card
            graph_span: 24h
            span:
              offset: +23h
            now:
              show: true
              label: Nå
            header:
              show: true
              title: 🧂 Saltholdighet (prognose)
              show_states: true
            apex_config:
              chart:
                height: 230
                toolbar:
                  show: false
                sparkline:
                  enabled: false
              xaxis:
                type: datetime
                labels:
                  show: true
              stroke:
                curve: smooth
              legend:
                show: true
              grid:
                show: true
                strokeDashArray: 3
                yaxis:
                  lines:
                    show: true
                xaxis:
                  lines:
                    show: false
                padding:
                  left: 12
                  right: 6
                  bottom: 6
              markers:
                size: 0
                strokeWidth: 0
                hover:
                  size: 0
              tooltip:
                'y':
                  formatter: |
                    EVAL:(v)=> v!=null ? `${Number(v).toFixed(2)} PSU` : '–'
            yaxis:
              - decimals: 1
                apex_config:
                  title:
                    text: PSU
            series:
              - entity: sensor.hav_vind_saltholdighet
                name: Saltholdighet
                color: '#e53935'
                stroke_width: 4
                show:
                  legend_value: false
                  in_header: false
                  extremas: true
                data_generator: >
                  const nowTs = Date.now();

                  const arr = entity && entity.attributes ?
                  (entity.attributes.sea_water_salinity_forecast || []) : [];

                  if (!Array.isArray(arr)) return [];

                  const pts = arr
                    .filter(e => e && e.time && e.value != null)
                    .map(e => [new Date(e.time).getTime(), Number(e.value)])
                    .sort((a, b) => a[0] - b[0]);

                  let lastBefore = null; for (const p of pts) {
                    if (p[0] <= nowTs) lastBefore = p;
                    else break;
                  }

                  const out = pts.filter(p => p[0] >= nowTs); if (lastBefore)
                  out.unshift(lastBefore);

                  return out;
              - entity: sensor.hav_vind_saltholdighet
                name: Nå
                show:
                  in_chart: false
                  in_header: true
                  legend_value: false
                data_generator: >
                  const nowTs = Date.now();

                  const arr = entity && entity.attributes ?
                  (entity.attributes.sea_water_salinity_forecast || []) : [];

                  if (!Array.isArray(arr) || arr.length === 0) return [];

                  const pts = arr
                    .filter(e => e && e.time && e.value != null)
                    .map(e => [new Date(e.time).getTime(), Number(e.value)])
                    .sort((a, b) => a[0] - b[0]);

                  let lastBefore = null; for (const p of pts) {
                    if (p[0] <= nowTs) lastBefore = p;
                    else break;
                  }

                  const p = lastBefore ? lastBefore : pts[0]; return [[p[0],
                  p[1]]];
      - type: vertical-stack
        cards:
          - type: custom:mushroom-title-card
            title: 🌡️ Lufttemperatur
          - type: custom:apexcharts-card
            graph_span: 24h
            span:
              offset: +23h
            now:
              show: true
              label: Nå
            header:
              show: true
              title: 🌡️ Lufttemperatur (prognose)
              show_states: true
            apex_config:
              chart:
                height: 230
                toolbar:
                  show: false
                sparkline:
                  enabled: false
              xaxis:
                type: datetime
                labels:
                  show: true
              stroke:
                curve: smooth
              legend:
                show: true
              grid:
                show: true
                strokeDashArray: 3
                yaxis:
                  lines:
                    show: true
                xaxis:
                  lines:
                    show: false
                padding:
                  left: 12
                  right: 6
                  bottom: 6
              markers:
                size: 0
                strokeWidth: 0
                hover:
                  size: 0
              tooltip:
                'y':
                  formatter: |
                    EVAL:(v)=> v!=null ? `${Number(v).toFixed(1)} °C` : '–'
            yaxis:
              - decimals: 1
                apex_config:
                  title:
                    text: °C
            series:
              - entity: sensor.hav_vind_lufttemperatur
                name: Lufttemperatur
                color: '#e53935'
                stroke_width: 4
                show:
                  legend_value: false
                  in_header: false
                  extremas: true
                data_generator: >
                  const nowTs = Date.now();

                  const arr = entity && entity.attributes ?
                  (entity.attributes.air_temperature_forecast || []) : [];

                  if (!Array.isArray(arr)) return [];

                  const pts = arr
                    .filter(e => e && e.time && e.value != null)
                    .map(e => [new Date(e.time).getTime(), Number(e.value)])
                    .sort((a, b) => a[0] - b[0]);

                  let lastBefore = null; for (const p of pts) {
                    if (p[0] <= nowTs) lastBefore = p;
                    else break;
                  }

                  const out = pts.filter(p => p[0] >= nowTs); if (lastBefore)
                  out.unshift(lastBefore);

                  return out;
              - entity: sensor.hav_vind_lufttemperatur
                name: Nå
                show:
                  in_chart: false
                  in_header: true
                  legend_value: false
                data_generator: >
                  const nowTs = Date.now();

                  const arr = entity && entity.attributes ?
                  (entity.attributes.air_temperature_forecast || []) : [];

                  if (!Array.isArray(arr) || arr.length === 0) return [];

                  const pts = arr
                    .filter(e => e && e.time && e.value != null)
                    .map(e => [new Date(e.time).getTime(), Number(e.value)])
                    .sort((a, b) => a[0] - b[0]);

                  let lastBefore = null; for (const p of pts) {
                    if (p[0] <= nowTs) lastBefore = p;
                    else break;
                  }

                  const p = lastBefore ? lastBefore : pts[0]; return [[p[0],
                  p[1]]];
      - type: vertical-stack
        cards:
          - type: custom:mushroom-title-card
            title: 🌊 Tidevann
          - type: custom:apexcharts-card
            graph_span: 36h
            span:
              offset: +24h
            now:
              show: true
              label: Nå
            header:
              show: true
              title: 🌊 Tidevannsnivå
              show_states: true
            apex_config:
              chart:
                height: 230
                toolbar:
                  show: false
                sparkline:
                  enabled: false
              xaxis:
                type: datetime
                labels:
                  show: true
              stroke:
                curve: smooth
              grid:
                show: true
                strokeDashArray: 3
                yaxis:
                  lines:
                    show: true
                xaxis:
                  lines:
                    show: false
                padding:
                  left: 12
                  right: 6
                  bottom: 6
              tooltip:
                'y':
                  formatter: |
                    EVAL:(v)=> v!=null ? `${Number(v).toFixed(1)} cm` : '–'
            yaxis:
              - decimals: 0
                apex_config:
                  title:
                    text: cm
            series:
              - entity: sensor.hav_vind_tidevann
                name: Tabell
                color: '#ffb74d'
                stroke_width: 3
                show:
                  extremas: false
                  in_header: before_now
                  legend_value: false
                data_generator: >
                  const arr = entity?.attributes?.tide_prediction_series ?? [];
                  return Array.isArray(arr)
                    ? arr
                      .filter(e => e?.time && e?.value != null)
                      .map(e => [new Date(e.time).getTime(), Number(e.value)])
                    : [];
              - entity: sensor.hav_vind_tidevann
                name: Prognose
                color: '#1565c0'
                stroke_width: 4
                show:
                  extremas: true
                  in_header: before_now
                  legend_value: false
                data_generator: >
                  const arr = entity?.attributes?.tide_forecast_series ?? [];
                  return Array.isArray(arr)
                    ? arr
                      .filter(e => e?.time && e?.value != null)
                      .map(e => [new Date(e.time).getTime(), Number(e.value)])
                    : [];
              - entity: sensor.hav_vind_tidevann
                name: Observasjon
                color: '#e53935'
                stroke_width: 2
                extend_to: false
                show:
                  extremas: false
                  in_header: true
                  legend_value: false
                data_generator: >
                  const nowTs = Date.now(); const arr =
                  entity?.attributes?.tide_observation_series ?? []; return
                  Array.isArray(arr)
                    ? arr
                      .filter(e => e?.time && e?.value != null && new Date(e.time).getTime() <= nowTs)
                      .map(e => [new Date(e.time).getTime(), Number(e.value)])
                    : [];
      - type: vertical-stack
        cards:
          - type: custom:mushroom-title-card
            title: 🌊 Bølgehøyde
          - type: custom:apexcharts-card
            graph_span: 24h
            span:
              offset: +23h
            now:
              show: true
              label: Nå
            header:
              show: true
              title: 🌊 Bølgehøyde (prognose)
              show_states: true
            apex_config:
              chart:
                height: 230
                toolbar:
                  show: false
                sparkline:
                  enabled: false
              xaxis:
                type: datetime
                labels:
                  show: true
              stroke:
                curve: smooth
              legend:
                show: true
              grid:
                show: true
                strokeDashArray: 3
                yaxis:
                  lines:
                    show: true
                xaxis:
                  lines:
                    show: false
                padding:
                  top: 16
                  left: 12
                  right: 6
                  bottom: 6
              markers:
                size: 0
                strokeWidth: 0
                hover:
                  size: 0
              tooltip:
                'y':
                  formatter: |
                    EVAL:(v)=> v!=null ? `${Number(v).toFixed(1)} m` : "–"
            yaxis:
              - min: 0
                decimals: 1
            series:
              - entity: sensor.hav_vind_bolgehoyde
                name: Bølgehøyde
                color: '#e53935'
                stroke_width: 5
                extend_to: false
                show:
                  legend_value: false
                  in_header: false
                  extremas: true
                data_generator: |
                  const nowTs = Date.now();
                  const keys = [
                    'sea_surface_wave_height_forecast',
                    'significant_wave_height_forecast',
                    'wave_height_forecast'
                  ];

                  const arr = keys
                    .map(k => entity && entity.attributes ? entity.attributes[k] : null)
                    .find(a => Array.isArray(a)) || [];

                  const pts = arr
                    .filter(e => e && e.time && e.value != null)
                    .map(e => [new Date(e.time).getTime(), Number(e.value)])
                    .sort((a, b) => a[0] - b[0]);

                  let lastBefore = null;
                  for (const p of pts) {
                    if (p[0] <= nowTs) lastBefore = p;
                    else break;
                  }

                  const out = pts.filter(p => p[0] >= nowTs);
                  if (lastBefore) out.unshift(lastBefore);
                  return out;
              - entity: sensor.hav_vind_bolgehoyde
                name: Nå
                show:
                  in_chart: false
                  in_header: true
                  legend_value: false
                data_generator: |
                  const nowTs = Date.now();
                  const keys = [
                    'sea_surface_wave_height_forecast',
                    'significant_wave_height_forecast',
                    'wave_height_forecast'
                  ];

                  const arr = keys
                    .map(k => entity && entity.attributes ? entity.attributes[k] : null)
                    .find(a => Array.isArray(a)) || [];

                  if (!Array.isArray(arr) || arr.length === 0) return [];

                  const pts = arr
                    .filter(e => e && e.time && e.value != null)
                    .map(e => [new Date(e.time).getTime(), Number(e.value)])
                    .sort((a, b) => a[0] - b[0]);

                  let lastBefore = null;
                  for (const p of pts) {
                    if (p[0] <= nowTs) lastBefore = p;
                    else break;
                  }

                  const p = lastBefore ? lastBefore : pts[0];
                  return [[p[0], p[1]]];
      - type: vertical-stack
        cards:
          - type: custom:mushroom-title-card
            title: 💧 Luftfuktighet
          - type: custom:apexcharts-card
            graph_span: 24h
            span:
              offset: +23h
            now:
              show: true
              label: Nå
            header:
              show: true
              title: 💧 Luftfuktighet (prognose)
              show_states: true
            apex_config:
              chart:
                height: 230
                toolbar:
                  show: false
                sparkline:
                  enabled: false
              xaxis:
                type: datetime
                labels:
                  show: true
              stroke:
                curve: smooth
              legend:
                show: true
              grid:
                show: true
                strokeDashArray: 3
                yaxis:
                  lines:
                    show: true
                xaxis:
                  lines:
                    show: false
                padding:
                  left: 12
                  right: 6
                  bottom: 6
              markers:
                size: 0
                strokeWidth: 0
                hover:
                  size: 0
              tooltip:
                'y':
                  formatter: |
                    EVAL:(v)=> v!=null ? `${Number(v).toFixed(1)} %` : '–'
              yaxis:
                - tickAmount: 5
                  forceNiceScale: true
                  decimalsInFloat: 0
                  labels:
                    formatter: |
                      EVAL:(v)=> `${Math.round(v)}`
            yaxis:
              - id: fukt
                decimals: 0
                opposite: false
            series:
              - entity: sensor.hav_vind_luftfuktighet
                name: Luftfuktighet
                yaxis_id: fukt
                color: '#e53935'
                stroke_width: 5
                extend_to: false
                show:
                  legend_value: false
                  in_header: false
                  extremas: true
                data_generator: >
                  const nowTs = Date.now();

                  const arr = entity && entity.attributes ?
                  (entity.attributes.relative_humidity_forecast || []) : [];

                  if (!Array.isArray(arr)) return [];

                  const pts = arr
                    .filter(e => e && e.time && e.value != null)
                    .map(e => [new Date(e.time).getTime(), Number(e.value)])
                    .sort((a, b) => a[0] - b[0]);

                  let lastBefore = null; for (const p of pts) {
                    if (p[0] <= nowTs) lastBefore = p;
                    else break;
                  }

                  const out = pts.filter(p => p[0] >= nowTs); if (lastBefore)
                  out.unshift(lastBefore);

                  return out;
              - entity: sensor.hav_vind_luftfuktighet
                name: Nå
                show:
                  in_chart: false
                  in_header: true
                  legend_value: false
                data_generator: >
                  const nowTs = Date.now();

                  const arr = entity && entity.attributes ?
                  (entity.attributes.relative_humidity_forecast || []) : [];

                  if (!Array.isArray(arr) || arr.length === 0) return [];

                  const pts = arr
                    .filter(e => e && e.time && e.value != null)
                    .map(e => [new Date(e.time).getTime(), Number(e.value)])
                    .sort((a, b) => a[0] - b[0]);

                  let lastBefore = null; for (const p of pts) {
                    if (p[0] <= nowTs) lastBefore = p;
                    else break;
                  }

                  const p = lastBefore ? lastBefore : pts[0]; return [[p[0],
                  p[1]]];
      - type: vertical-stack
        cards:
          - type: custom:mushroom-title-card
            title: 🧭 Lufttrykk (MSL)
          - type: custom:apexcharts-card
            graph_span: 24h
            span:
              offset: +23h
            now:
              show: true
              label: Nå
            header:
              show: true
              title: 🧭 Lufttrykk (MSL) (prognose)
              show_states: true
            apex_config:
              chart:
                height: 230
                toolbar:
                  show: false
                sparkline:
                  enabled: false
              xaxis:
                type: datetime
                labels:
                  show: true
              stroke:
                curve: smooth
              legend:
                show: true
              grid:
                show: true
                strokeDashArray: 3
                yaxis:
                  lines:
                    show: true
                xaxis:
                  lines:
                    show: false
                padding:
                  left: 12
                  right: 6
                  bottom: 6
              markers:
                size: 0
                strokeWidth: 0
                hover:
                  size: 0
              tooltip:
                'y':
                  formatter: |
                    EVAL:(v)=> v!=null ? `${Number(v).toFixed(1)} hPa` : '–'
              yaxis:
                - tickAmount: 5
                  forceNiceScale: true
                  decimalsInFloat: 1
                  labels:
                    formatter: |
                      EVAL:(v)=> `${Number(v).toFixed(1)}`
            yaxis:
              - id: trykk
                decimals: 1
                opposite: false
            series:
              - entity: sensor.hav_vind_lufttrykk_msl
                name: Lufttrykk
                yaxis_id: trykk
                color: '#e53935'
                stroke_width: 5
                extend_to: false
                show:
                  legend_value: false
                  in_header: false
                  extremas: true
                data_generator: >
                  const nowTs = Date.now();

                  const arr = entity && entity.attributes ?
                  (entity.attributes.pressure_at_sea_level_forecast || []) : [];

                  if (!Array.isArray(arr)) return [];

                  const pts = arr
                    .filter(e => e && e.time && e.value != null)
                    .map(e => [new Date(e.time).getTime(), Number(e.value)])
                    .sort((a, b) => a[0] - b[0]);

                  let lastBefore = null; for (const p of pts) {
                    if (p[0] <= nowTs) lastBefore = p;
                    else break;
                  }

                  const out = pts.filter(p => p[0] >= nowTs); if (lastBefore)
                  out.unshift(lastBefore);

                  return out;
              - entity: sensor.hav_vind_lufttrykk_msl
                name: Nå
                show:
                  in_chart: false
                  in_header: true
                  legend_value: false
                data_generator: >
                  const nowTs = Date.now();

                  const arr = entity && entity.attributes ?
                  (entity.attributes.pressure_at_sea_level_forecast || []) : [];

                  if (!Array.isArray(arr) || arr.length === 0) return [];

                  const pts = arr
                    .filter(e => e && e.time && e.value != null)
                    .map(e => [new Date(e.time).getTime(), Number(e.value)])
                    .sort((a, b) => a[0] - b[0]);

                  let lastBefore = null; for (const p of pts) {
                    if (p[0] <= nowTs) lastBefore = p;
                    else break;
                  }

                  const p = lastBefore ? lastBefore : pts[0]; return [[p[0],
                  p[1]]];
    badges:
      - type: custom:mushroom-entity-card
        entity: select.hav_og_vind_aktiv_stasjon
        name: Hav & Vind – valgt stasjon
        icon: mdi:map-marker
