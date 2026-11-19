# Luzon Expressway RFID & Toll Map

An interactive street map of Luzon's expressways, colored by the RFID each road reads: **Easytrip** (solid blue) or **Autosweep** (dashed orange). Pick an entry plaza and every exit shows its toll for your vehicle class. Pan to your exit and tap it to see the total and the breakdown by toll system.

## Put it on GitHub Pages

1. Commit `index.html` and `fares.csv` to the root of a repo.
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

## How fares work

A trip is split into **legs, one per toll system**. Each leg is priced from the fare table by its entry and exit. When a trip moves from one system into another, the handover point is named after the other system. For example, Balintawak → Rosario becomes:

| System | From | To | Class 1 |
|---|---|---|---|
| NLEX-SCTEX | Balintawak | TPLEX junction | ₱670 |
| TPLEX | NLEX-SCTEX junction | Rosario | ₱311 |
| **Total** | | | **₱981** |

The breakdown shows these exact names, so you always know what to type into the table.

### `fares.csv`

```
system,from,to,class1,class2,class3,note
NLEX-SCTEX,Balintawak,Dau,411,,,"Expressway.PH, TRB matrix 1 Feb 2026"
NAIAX,*,*,<class1>,<class2>,<class3>,flat rate (placeholder, not a real fare)
```

- A fare applies in both directions.
- `*` means any plaza. Use it for open-system or flat-rate roads, e.g. `SYSTEM,PlazaName,*` or `SYSTEM,*,*`. Exact entry–exit rows take priority over `*` rows.
- Plaza names are the map names without the "(road)" suffix. For example, "Sucat (SLEX)" is entered as `Sucat` with system `SLEX`.
- Lines starting with `#` are ignored.
- The **systems** are `NLEX-SCTEX, Subic–Tipo, TPLEX, SLEX, STAR, Skyway, Skyway Stage 3, CALAX, CAVITEX, NAIAX, MCX, NLEX Connector, Harbor Link, CLLEX` (CLLEX is always free). Which road belongs to which system is set in the `SYSTEM` table near the top of the script. NLEX and SCTEX are grouped as one system because the source quotes Balintawak → Tarlac as a single ₱670 fare. Edit the table if operators charge differently.

### Updating fares

- **In the page.** When a leg shows `₱?`, type the amount into the breakdown and choose *Save fare*. You can also use **Edit table** for bulk CSV editing, or **Import CSV**. Edits are kept in your browser (localStorage), and **Reset** discards them.
- **For everyone.** Choose **Download fares.csv**, commit it over the repo's `fares.csv`, and push. The page loads `fares.csv` on every visit. Browsers with local edits keep using those edits until they choose Reset.

### What's built in

Only the five figures quoted in the Expressway.PH article (TRB matrix, 1 Feb 2026, class 1):

- NLEX Balintawak → Dau: ₱411
- NLEX/SCTEX Balintawak → Tarlac: ₱670
- TPLEX La Paz → Rosario: ₱311
- STAR Calamba → Batangas: ₱135
- SLEX Magallanes → Calamba: ₱244. Magallanes isn't a plaza in the map data yet, so this row isn't used.

Everything else shows `₱?` until fares are added from the TRB or operator toll matrices.

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
   python3 scripts/make_page.py data/roads.json data/graph.json fares.csv template.html index.html
   ```

   `build2.py` reads `data/export.geojson` and `data/ph.json` and writes `data/graph.json`.

`scripts/build.py` holds the road → network table (`ROADS`) and the OSM-name → road mapping (`NAME`).

## Roadmap

1. Fill `fares.csv` from the TRB matrices for every system and class.
2. Add all exits (`motorway_junction`) and ramps (`motorway_link`) so routing follows real interchanges.
3. Add address search that suggests the nearest plazas, using geocoding plus a check that skips plazas across water.
4. Add a "Prefer SLEX at-grade / Skyway" route option.
5. Add a One RFID toggle that shows a single-balance view.
6. Add a layer of RFID installation sites.
7. Add a return-trip total and an offline (PWA) mode.

## Known limitations

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
