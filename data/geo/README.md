# UK ITL1 region boundaries (`uk_itl1.topojson`)

Boundaries for the 12 UK ITL1 regions, simplified for a browser choropleth (D3 + topojson-client).

| | |
|---|---|
| File | `uk_itl1.topojson` (71 KB, TopoJSON, WGS84 lon/lat, quantized) |
| TopoJSON object | `regions` (one GeometryCollection, 12 geometries) |
| Feature `id` | ITL1 code, e.g. `TLC` |
| Properties | `name` (the exact region names in `BRIEF.md`), `code` (ITL1 `TLC`..`TLN`), `nuts1_2018` (`UKC`..`UKN`) |
| Preview | `preview.png` |

```js
const topo = await d3.json("data/geo/uk_itl1.topojson");
const regions = topojson.feature(topo, topo.objects.regions);   // 12 features
const proj = d3.geoMercator().fitSize([w, h], regions);        // or geoAlbers().rotate([4.4,0]).center([0,55.4]).parallels([50,60])
```

| code | nuts1_2018 | name |
|---|---|---|
| TLC | UKC | North East |
| TLD | UKD | North West |
| TLE | UKE | Yorkshire and The Humber |
| TLF | UKF | East Midlands |
| TLG | UKG | West Midlands |
| TLH | UKH | East of England |
| TLI | UKI | London |
| TLJ | UKJ | South East |
| TLK | UKK | South West |
| TLL | UKL | Wales |
| TLM | UKM | Scotland |
| TLN | UKN | Northern Ireland |

ITL1 regions have exactly the same boundaries as the NUTS1 (2018) regions. The codes differ only in prefix (`TL` instead of `UK`). The 12 European Electoral Regions also share these boundaries.

## Source

- **What:** `geogNUTS2018UK.json` from the ONS Digital Content team's repository **ONSvisual/topojson_boundaries**
  (https://github.com/ONSvisual/topojson_boundaries, branch `master`). The file was fetched from
  `https://raw.githubusercontent.com/ONSvisual/topojson_boundaries/master/geogNUTS2018UK.json` on 2026-10-22.
  sha256 `68109a376c78a7b3c0165d0ad23668ce25faf685804a42ae330f91ec870a8895`, 220,282 bytes.
  The repository was archived (read-only) in October 2025 and has no version tags, so the hash above identifies the file.
- **Contents of the source file:** a TopoJSON object `nuts3` with 179 UK NUTS3 areas (`AREACD`, `AREANM`), in WGS84.
  The repository README says the files come from the ONS Open Geography Portal (BDY_NUTS1 / NUTS boundaries).
  The codes are mostly NUTS 2018. The file also contains the 2021 Northamptonshire split (`UKF24`/`UKF25`).
  This doesn't affect the region (level 1) boundaries.
- **Why not an npm/PyPI package:** I searched the npm registry and the web for a package that ships ONS-derived
  ITL1/NUTS1/EER geometry. The candidates were `uk-atlas`, `uk-topojson`, `nuts-atlas`, `nuts-geojson` and `@onsvisual/*`. Several don't exist, and the rest either contain no geometry or fetch it at runtime (`eurostat-map`, `@mailwoman/nuts-lookup`).
  The only UK package with geometry (`echarts-united-kingdom-js@0.0.1`) holds 2016 Westminster constituencies with no region lookup.
  `raw.githubusercontent.com` turned out to be reachable through the proxy, so I used the ONS team's own published TopoJSON. It is a more direct ONS source than a third-party package.

## Licence and required attribution

The repository has no LICENSE file. The boundaries come from the ONS Open Geography Portal and are published under the
**Open Government Licence v3.0** (https://www.nationalarchives.gov.uk/doc/open-government-licence/version/3/).
OGL requires an attribution statement. Use this one in the dashboard footer or credits:

> Source: Office for National Statistics licensed under the Open Government Licence v.3.0.
> Contains OS data © Crown copyright and database right [year].
> Contains LPS Intellectual Property © Crown copyright and database right [year]. This information is licensed under the terms of the Open Government Licence.

The LPS (Land & Property Services) line covers the Northern Ireland boundaries. Under ONS guidance, `[year]` is the year of the boundary data.
The source file doesn't state its release date, so use `2021`. That is the latest vintage of codes it contains (the Northamptonshire ITL3 split).
Alternatively, write "2018–2021".

## Processing steps

Tools: mapshaper 0.7.95 (npm, installed with `--ignore-scripts`), d3-geo 3.1.1 and topojson-client 3.1.0 for validation, Python shapely 2.2.0 and matplotlib 3.11.2 for the preview.
The downloaded file was handled as data only. No code from it was executed.

1. Download `geogNUTS2018UK.json` (179 NUTS3 polygons) into a scratch folder.
2. Dissolve NUTS3 to NUTS1 on the first three characters of `AREACD`. NUTS3 nests exactly within NUTS1, so this gives 12 regions.
   Shared borders become shared TopoJSON arcs, so neighbouring regions have no gaps or overlaps.
   ```
   mapshaper -i geogNUTS2018UK.json -proj init=wgs84 \
     -each "nuts1=AREACD.slice(0,3)" -dissolve nuts1 \
     -each "name=({UKC:'North East',...,UKN:'Northern Ireland'})[nuts1], code='TL'+nuts1.slice(2), nuts1_2018=nuts1" \
     -filter-fields code,name,nuts1_2018 -rename-layers regions -o full.topojson format=topojson
   ```
   The unsimplified result was 134 KB.
3. Simplify with `-simplify weighted 50% keep-shapes`, then `-sort code`, and output TopoJSON with `id-field=code`.
   The result is 71 KB. `keep-shapes` keeps every island, including Shetland, Orkney, the Western Isles, the Isles of Scilly, the Isle of Wight and Anglesey.
   Simplifying also removed three tiny (<0.001 km²) slivers and a ring self-intersection near Shetland that were in the source. The output is valid in shapely.
4. Validate with d3-geo:
   - exactly 12 features, all 12 names match `BRIEF.md`
   - bounds lon -8.650 to 1.763, lat 49.882 to 60.846
   - every feature has a small spherical area, so ring winding is correct for D3
   - areas (km²): London 1,583; Wales 20,744; Scotland 78,259; NI 14,250. These are consistent with published land areas, so the coastline is clipped and not the extent of the realm.
5. Render `preview.png` with matplotlib and check it visually.

## Caveats

- The source is a generalised boundary set intended for web mapping. It is fine for choropleths but not for area calculation or spatial joins.
- The Isle of Man and the Channel Islands are not part of the UK and are not included.
- In small renders London is tiny. Consider an inset, or use a tile/hex layout alongside the map.
