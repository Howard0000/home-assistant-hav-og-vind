# Dashboard – Hav og vind

This folder contains a **ready-to-use example dashboard** for the Hav og vind integration.

The dashboard file is kept **outside `custom_components/`** to:
- keep the integration code clean and focused
- make it easy to copy and adapt the dashboard to your own setup
- avoid mixing UI configuration with the integration codebase

> 💡 **Short version:** The integration works without this dashboard, but the **entire design (proxy sensors + active station)** is made to shine when used with this dashboard.

---

## ✅ Recommended setup

- The dashboard only uses **proxy entities** (with stable `entity_id`s), for example:
  - `sensor.hav_vind_vindhastighet`
  - `sensor.hav_vind_sjotemperatur`
  - `sensor.hav_vind_bolgehoyde`
  - `sensor.hav_vind_tidevann`

- You select the active station using the dropdown:
  - `select.hav_og_vind_aktiv_stasjon` (**Hav og vind – Active station**)

- When you add new locations:
  - ✅ You **do not** need to change the dashboard
  - 👉 Just pick the desired station in the dropdown

This makes the dashboard **station-independent** and very easy to maintain.

---

## 📁 Files

- `lovelace_hav_og_vind.yaml`  
  A complete example view/dashboard in YAML format.

---

## 📌 Requirements for the dashboard

The dashboard uses some common HACS cards:

- `custom:button-card`
- `custom:apexcharts-card`
- Mushroom cards

> If you don’t use these, you can still use the integration – but you will need to adapt the dashboard.

---

## ⚙️ How to use it

This example is intended for **Lovelace YAML / Raw mode**.

1. Open Home Assistant → **Dashboards**
2. Create a new dashboard (YAML mode) or open the Raw editor
3. Paste the contents of `lovelace_hav_og_vind.yaml`
4. Make sure the integration is installed and you have added at least one location
5. Select the desired station in **Hav og vind – Active station**

---

## ⚠️ Note

The dashboard is:
- optional (the integration works without it)
- meant as an example / starting point
- designed to show the **full benefit** of proxy sensors and the active station concept
