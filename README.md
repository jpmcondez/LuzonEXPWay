# Luzon Expressway RFID & Toll Map

An interactive street map of Luzon's expressways, colored by the RFID each road reads: **Easytrip** (solid blue) or **Autosweep** (dashed orange). Pick an entry plaza and every exit shows its toll for your vehicle class. Pan to your exit and tap it to see the total and the breakdown by toll system.

## Put it on GitHub Pages

1. Upload the whole repo (unzipped) to a GitHub repository. At minimum you need `index.html` and `fares.csv`; the rest is needed to update fares.
2. Go to **Settings → Pages → Deploy from branch** and choose `main` and `/ (root)`.
3. Open `https://<user>.github.io/<repo>/`.

`index.html` also works opened straight from disk. In that case it uses the fare table embedded in the page instead of `fares.csv`.

## Features

- **Street base map.** OpenStreetMap by default on the hosted site, Esri Streets when the file is opened from disk (OSM blocks pages with no web address). OSM Humanitarian and CARTO Voyager / Light / Dark are also in the picker. None need an API key; the choice is remembered per browser.
- **RFID overlay.** Real expressway shapes from OpenStreetMap, colored by network. CLLEX (toll-free) is dotted gray. Roads the source article doesn't cover are thin gray.
- **Labelled toll plazas.** There are 84 named plazas. Names appear from zoom 11, or from zoom 10 once an entry is picked. Overlapping labels are hidden.
- **Tolls to every exit.** After you pick an entry, each exit label shows a chip:
  - green `₱411`: the toll is known
  - amber `₱670 + ?`: part of the trip is priced, part is missing
  - gray `₱?`: no fare yet

  A sortable list of all reachable exits, with km and toll, is in the side panel.
- **Breakdown.** Tap an exit and choose *Exit here*. The panel shows the total toll, the RFID verdict (Easytrip only / Autosweep only / both networks → One RFID), and each leg by toll system, with distance, fare and source note.
- **Vehicle classes 1, 2 and 3.**
- **Shareable links.** `#from=Balintawak&to=Rosario&class=2`
- **Editable fares.** See below.

## Fares

### What's loaded (November 2026)

| Toll system | Coverage | As of | Source |
|---|---|---|---|
| NLEX-SCTEX (incl. Harbor Link) | Full matrix, 30 plazas, classes 1–3 | Feb 2026 | TRB-approved integrated matrix as compiled by Expressway.PH |
| TPLEX | Full matrix, 11 plazas, classes 1–3 | TRB (undated) | trb.gov.ph TPLEX toll rate page |
| Skyway Stage 3 | Buendia ↔ Quirino/Nagtahan/Quezon Ave/Balintawak/NLEX | Jul 2021 ⚠ | trb.gov.ph Skyway Stage 3 page |
| Skyway-SLEX-MCX | Alabang–Calamba–Santo Tomas only | Jul 2026 | TRB 2nd-tranche announcement (via Philstar, TopGear, GMA) |
| STAR | Santo Tomas–Lipa, Santo Tomas–Batangas City | Jul 2026 | TRB 2nd-tranche announcement |
| CALAX | 6 plazas, classes 1–3 | Feb 2024 ⚠ | trb.gov.ph CALAX page; Subsection 3 (tolled since Aug 2026) missing |
| CAVITEX, NAIAX, NLEX Connector, Subic–Tipo | none yet | | Add from TRB |

Checks against published totals: Balintawak→Dau ₱411, Balintawak→Clark South ₱451, Balintawak→Rosario ₱981 (₱670 + ₱311), Balintawak→Urdaneta ₱886, Alabang→Batangas City ₱295 (₱174 + ₱121).

Fares older than 12 months, or marked OUTDATED, show **“may be outdated”** in the breakdown. The Fares panel also flags them with “check for update”.

### How a trip is priced

A trip is split into one **leg per toll system**, and each leg is looked up by entry and exit. Where a trip passes from one system into another, the handover point is named “*Other system* junction”. `data/plazas.csv` maps that name to the real plaza: for example, on NLEX-SCTEX “TPLEX junction” = **Tarlac**, and on TPLEX “NLEX-SCTEX junction” = **La Paz**. Balintawak → Rosario is then NLEX-SCTEX Balintawak→Tarlac ₱670 + TPLEX La Paz→Rosario ₱311.

Toll systems (`SYSTEM` table in `template.html`): NLEX-SCTEX (NLEX, SCTEX, Harbor Link), Skyway-SLEX-MCX (one integrated TRB matrix), Skyway Stage 3, STAR, TPLEX, CALAX, CAVITEX, NAIAX, NLEX Connector, Subic–Tipo. CLLEX is always free.

### Keeping fares current

The source of truth is **`fares/matrices/`**: one file per toll system and class, in the same layout as the TRB tables.

```
# system: TPLEX
# class: 1
# effective: 2026-02
# source: Toll Regulatory Board, trb.gov.ph/index.php/toll-rates/tplex-toll-rate
Exit \ Entry,La Paz,Victoria,Gerona,...
Victoria,30
Gerona,58,28
...
```

When the TRB announces new rates:

1. **In the page,** choose **Paste TRB matrix**. Pick the system and class, set the effective month, then paste the table copied from the TRB page or a spreadsheet. **Check** lists any plaza names it can't match. **Save** updates the map right away, in your browser, and also downloads the table as `<system>.class<N>.csv`.
2. **On GitHub,** upload that file into `fares/matrices/`, replacing the old one, and commit.
3. **The included GitHub Action** (`.github/workflows/fares.yml`) then rebuilds `fares.csv` and `index.html`, and everyone sees the new fares. To turn it on, go to **Settings → Actions → General → Workflow permissions** and choose **Read and write**.

If you don't want to use Actions, run this yourself and commit both files:

```
python3 scripts/matrices_to_fares.py
python3 scripts/make_page.py data/roads.json data/graph.json data/plazas.csv fares.csv template.html index.html
```

**Plaza names.** If the TRB uses a name the map doesn't know, for example a new interchange or a different spelling, add it to `data/plazas.csv`. You can add it as an alias of an existing plaza, or as a new plaza with `road,lat,lon` so the build places it on the road. The TRB's SLEX abbreviations (MAG, BIC, SUC, ALA, …) are already set up as aliases, so a pasted TRB SLEX table matches as-is.

**Quick fixes.** You can also type a missing amount straight into a trip's breakdown (*Save fare*), or use **Edit table** to bulk-edit the CSV. These edits stay in your browser until you save them into a matrix file.

## Rebuilding the map data

1. In [overpass-turbo](https://overpass-turbo.eu), run this query and export the result as GeoJSON to `data/export.geojson`:

   ```
   [out:json][timeout:180];
   (
     way["highway"="motorway"](13.5,119.8,16.6,121.8);
     way["highway"="motorway_link"](13.5,119.8,16.6,121.8);
     way["name"~"CLLEX|Central Luzon Link"](13.5,119.8,16.6,121.8);
     node["barrier"="toll_booth"](13.5,119.8,16.6,121.8);
     node["highway"="motorway_junction"](13.5,119.8,16.6,121.8);
   );
   out geom;
   ```

2. Extract the Philippines outline. Run `npm pack world-atlas@2`, then use `topojson-client` to take feature `608` from `countries-10m.json` and save it as `data/ph.json`.
3. Build:

   ```
   python3 scripts/build.py data/export.geojson data/ph.json data/roads.json
   python3 scripts/build2.py
   python3 scripts/make_page.py data/roads.json data/graph.json data/plazas.csv fares.csv template.html index.html
   ```

   `build2.py` reads `data/export.geojson` and `data/ph.json` and writes `data/graph.json`.

`scripts/build.py` holds the road → network table (`ROADS`) and the OSM-name → road mapping (`NAME`).

## Roadmap

1. Add the full Skyway-SLEX-MCX, STAR, CAVITEX, NAIAX, NLEX Connector and current CALAX matrices from the TRB.
2. Add all exits (`motorway_junction`) and ramps (`motorway_link`) so routing follows real interchanges.
3. Add address search that suggests the nearest plazas, using geocoding plus a check that skips plazas across water.
4. Add a "Prefer SLEX at-grade / Skyway" route option.
5. Add a One RFID toggle that shows a single-balance view.
6. Add a layer of RFID installation sites.
7. Add a return-trip total and an offline (PWA) mode.

## Known limitations

- 8 plazas that OpenStreetMap doesn't have (TPLEX La Paz, Victoria, Paniqui, Urdaneta, Pozorrubio; SCTEX Clark North, Bamban/New Clark City, Concepcion) are placed approximately. They are drawn with a dashed outline. Correct their `lat,lon` in `data/plazas.csv` and rebuild.
- A few aliases are assumptions and are marked in `data/plazas.csv`: Lawang Bato = Valenzuela, Santa Rosa City = Santa Rosa–Tagaytay, and CALAX Greenfield as the SLEX end.

- Distances are measured on the mapped roads. Gaps where ramps are missing are stitched together, so treat distances as approximate.
- The route is the shortest path. It may use Skyway where a driver would take SLEX at-grade, and the toll would differ.
- Short hops under 2 km between systems are treated as untolled ramps.
- The Skyway / Skyway Stage 3 split is approximate (at Buendia).
- Subic–Tipo isn't in the source article. It is shown as Easytrip because NLEX Corporation operates it.
- About 50 plazas have no name in OSM, so they can't be used as an entry or exit.
- The tile servers (CARTO, OSM) are free for light use. For heavy traffic, use your own tile provider.

## Sources

- RFID network per road and road lengths: Expressway.PH, *Autosweep vs Easytrip 2026* (updated 3 Oct 2026).
- Expressway geometry and toll plazas: © OpenStreetMap contributors, ODbL.
- Base map: © OpenStreetMap contributors, © CARTO.

Not affiliated with any toll operator or the TRB. Check tolls at the point of travel.
