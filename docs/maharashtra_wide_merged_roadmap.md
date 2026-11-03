Vayudrishti-AI: Maharashtra-wide Merged Roadmap

Built from your repo zip, your OpenAQ/GEE notebook and the 5-member/4-week plan. Prepared 3 Nov 2026.

Goal: turn the Pune-only, mock-data prototype into a real-data, Maharashtra-wide, deployed, explainable AQI platform with a clean shadcn/ui front end and live maps, and make every number on your resume defensible.

1. Read this first: what the audit found

I read the repo and notebook. I did not run the test suite, so the “28/28 passing” claim is unverified. These issues must be fixed before anything goes on a resume.

#

Finding

Evidence

Fix

1

Headline results come from synthetic data and are circular.

mock_data/generate_mock_data.py builds aqi = aod*180 + noise, then pm25 = 0.75*aqi + noise. So “satellite beats weather-only: R² 0.78 vs −0.05” is true by construction.

Retrain everything on real OpenAQ/CPCB pairs. Delete the mock-based tables from README and docs.

2

Forecast table is not physically plausible.

+1 h persistence MAE of 113 µg/m³. On a real hourly PM2.5 series, last-hour persistence is far more accurate. The mock rows are not a real time series.

Build forecasts from a true time-ordered station series with lag features; judge against persistence and seasonal-naive.

3

The API and heatmap fabricate inputs.

api/services/data_service.py invents weather and satellite values from distance to Pune centre. The map is a formula run through a model.

Replace with a feature store fed by real ingestion (Phase 5).

4

Pieces missing from the zip.

No trained weights (only feature_list.txt), no schemas/ folder, no frontend/package.json, no LICENSE file despite the MIT badge.

Commit a training script that regenerates weights; add schemas, package.json, LICENSE.

5

Boundary-layer height source looks wrong.

export_era5.js says it exports boundary-layer height from ECMWF/ERA5_LAND/HOURLY. As far as I know, ERA5-Land has no boundary-layer-height band. Please verify in the GEE catalog.

Get PBLH from ERA5 single levels (Copernicus CDS) or a weather API that provides it.

6

Pune-only, wide-open API.

Hard-coded Pune bounding box; CORS allow_origins=["*"].

Maharashtra config; restrict CORS to your domain.

What is genuinely good and worth keeping: the CPCB NAQI engine (src/domain/aqi.py), the KD-tree spatio-temporal matcher, leakage-aware CV splitters, the uncertainty/reliability module, the SHAP narrative generator, the Docker layout, and your notebook’s real OpenAQ v3 + Open-Meteo + MCD19A2 pulls. The notebook is your only real data today, so it becomes the spine of the merged project.

2. How the two plans merge

Your team doc defines owners A–E and a Day-1 schema contract. The repo already implements most of that structure, but on mock data. The merge keeps the ownership model and replaces mock inputs with real ones. If you work solo or in a smaller team, one person simply holds several letters.

Team-plan workstream

Repo location today

Status

Merge action

B Satellite & fusion

ingestion/satellite/, src/ingestion/satellite.py, src/models/fusion/ (empty)

GEE scripts exist, unrun at scale; fusion model not built

Run for Maharashtra; build the fusion model

A AQI & domain

src/domain/aqi.py, docs/

Solid

Add unit tests from official breakpoint tables; write source-attribution text

C Forecast & XAI

training/, src/features/, src/explainability/, src/models/uncertainty.py

Code exists; results are mock

Retrain on real series; add conformal intervals and ablation

D GIS, weather, map

src/ingestion/osm.py, weather.py, src/spatial/interpolation.py

IDW only; Pune grid

Statewide grid; regression-kriging; live map layer

E API, UI, PM

api/, frontend/, Docker

Works on fake features; plain JSX

Real feature store, TypeScript + shadcn/ui, CI/CD, deploy

Ground truth from your notebook: station inventory via OpenAQ v3 /locations, hourly /sensors/{id}/hours pulls with pagination, IST conversion, and a “≥12 measurements per day” validity rule. Promote this from notebook cells into src/ingestion/openaq.py, and keep the API key in environment variables only (never in the repo or notebook output).

3. Target architecture (Maharashtra)

OpenAQ v3 / CPCB ──┐Sentinel-5P NO2,SO2,CO,O3 (GEE) ──┤MODIS MAIAC AOD, MCD19A2 (GEE) ──┼─► Ingestion jobs ─► Raw storeERA5 / weather API (incl. PBLH) ──┤                        │OSM roads, buildings, industry ──┘                        ▼                                        Pair & feature builder (KD-tree, windows)                                                          │                         ┌────────────────────────────────┤                         ▼                                ▼                 Fusion model (PM2.5 now)        Forecast model (+1…+72 h)                         │ residuals at stations          │                         ▼                                ▼                 Regression-kriging ──► 1 km statewide surface + uncertainty                                                          │                                   Hourly PNG overlays + value grids ─► Object storage                                                          │                                   FastAPI (reads latest) ─► React + shadcn/ui + live map

Scale check: Maharashtra is about 308,000 km², so a 1 km grid is roughly 300k cells. Do not ship that as GeoJSON polygons. Publish one colour-mapped PNG (about 900 × 700 px) plus a compact value array per hour, and use a lookup endpoint for clicks. This keeps the map fast and the hosting cheap.

Honesty rule for “hyperlocal”: Maharashtra has few monitors outside big cities. Every map cell must carry an uncertainty band and a distance-to-nearest-station reliability score (your uncertainty.py already does this). Label the product “estimated” and show confidence.

4. Phased roadmap (about 6 weeks)

Phase 0: Merge and clean (Days 1–2) — Owner: E, review by all

Create one repo. Move notebook logic into src/ingestion/openaq.py; keep the notebook as notebooks/00_openaq_exploration.ipynb with outputs cleared and secrets removed.

Delete or quarantine mock-based result tables. Keep mock_data/ only for unit tests, clearly labelled.

Add the missing pieces: schemas/, LICENSE, frontend/package.json, .env.example.

Replace Pune constants with configs/region_maharashtra.yaml (bbox about 72.6–80.9°E, 15.6–22.1°N, city list, state boundary file).

Set up GitHub: milestones per phase, one issue per row below, CI running pytest and ruff.

Exit: clean clone installs and tests pass; README no longer shows mock numbers.

Phase 1: Real data spine (Week 1) — Owners: B, D, E

Stations: query OpenAQ for all PM2.5 locations inside the Maharashtra bbox, paginate, build stations.parquet with provider, coordinates, first/last timestamp and PM2.5 sensor IDs. Report the true station count by city.

History: pull hourly PM2.5 (plus NO2, SO2, CO, O3, PM10 where available) per station; QA for stuck values, negatives, gaps; keep a data-quality report.

Satellite: run GEE exports for MAIAC AOD, TROPOMI NO2/SO2/CO/O3 and aerosol index over the bbox. Record product versions.

Weather: hourly temperature, humidity, wind u/v, pressure, precipitation and boundary-layer height from a verified source.

Static GIS: OSM road density, building density, distance to major roads and industry; elevation; land cover.

Exit: make data reproduces raw files and a data catalog with row counts and date coverage.

Phase 2: Real training pairs (Week 2) — Owner: B (with D)

Pair each station-hour with the satellite pixel at the station (and a small-buffer mean). Use your KD-tree matcher; log pair counts per season.

Add features: AOD/PBLH, wind components, cyclic hour/month, satellite-age-in-hours, AOD-missing flag.

Expect heavy AOD gaps in monsoon (June–September). Design for it rather than dropping those rows.

Exit: one script builds canonical_dataset.parquet from raw; the data-quality report lists missingness by month and city.

Phase 3: Fusion model with honest evaluation (Week 3) — Owners: B, C

Models: Ridge baseline, then LightGBM/XGBoost; keep RF as a comparison.

Validation, in increasing difficulty: (1) chronological holdout; (2) leave-station-out GroupKFold; (3) leave-city-out (train on Pune and Mumbai, test on Nagpur or Nashik). Report all three.

Ablation on real data: weather-only, weather+GIS, +AOD, +TROPOMI, full. Report whatever it shows, including “satellite helps little” if that is the result.

Also train an AOD-free fallback model for cloudy hours.

Metrics: R², RMSE, MAE, bias, plus AQI-category accuracy.

Exit: metrics report generated by a script, committed with the config and git commit hash that produced it.

Phase 4: Forecasting, uncertainty, explanation (Week 4) — Owners: C, A

Direct multi-horizon LightGBM (+1, +6, +12, +24, +48, +72 h) using lags, rolling means, weather forecast features and time features.

Baselines to beat: persistence and seasonal-naive (same hour yesterday). Say plainly where you do not beat them; short horizons are hard to beat.

Uncertainty: split-conformal prediction (or quantile regression) for 90% intervals; report empirical coverage.

Explainability: SHAP TreeExplainer on the chosen model; domain text from A (for example, high NO2 with low wind suggests traffic accumulation; high AOD with shallow boundary layer suggests trapped aerosol).

Exit: forecast table versus both baselines, calibration plot, and 20 hand-checked explanation examples.

Phase 5: Statewide surface, feature store, live pipeline (Week 5) — Owners: D, E

Regression-kriging: fusion-model prediction as the trend, ordinary kriging of station residuals as the correction, producing a 1 km surface and kriging variance. Compare against IDW and report the cross-validated difference.

Hourly job (scheduled): fetch latest OpenAQ readings and weather, carry forward the latest satellite composite with an age feature, predict, write PNG overlays, value arrays and station JSON to object storage. Forecast layers for +1 to +72 h on the same schedule.

API v2 (FastAPI): /stations, /aqi/point, /forecast/point, /explain/point, /layers (latest overlay URLs and bounds), /health with data freshness. Remove any synthetic fallback; if data is stale, say so.

Exit: the API serves real, time-stamped values for all of Maharashtra with a visible “data as of” time.

Phase 6: UI, deploy, polish (Week 6) — Owners: E, all

Build the UI (section 6), deploy (section 7), record a demo, write the model card and README, final scope freeze.

Exit: public URL works from a phone; README has an architecture diagram, real metrics and a limitations section.

5. Algorithms: what to use and why

Problem

Method

Why it is defensible

Satellite-to-surface PM2.5

LightGBM/XGBoost with AOD, PBLH, TROPOMI, weather, GIS

Standard in satellite-PM2.5 literature; handles missing values and interactions

Cloud-gapped AOD

Missing-aware model plus AOD-free fallback and age feature

Honest handling of monsoon gaps

Spatial generalisation

Leave-station-out and leave-city-out CV

Prevents the optimistic scores random splits give

Continuous map

Regression-kriging (trend + residual kriging)

Uses station ground truth to correct the model; gives variance

Forecast

Direct multi-horizon gradient boosting; LSTM/TFT only as a stretch

Strong, fast, explainable; deep models need more data than you likely have

Intervals

Split-conformal prediction

Distribution-free, with measurable coverage

Explanation

SHAP plus domain-rule narrative

Answers “why is it high here, now?”

Index

CPCB NAQI sub-indices, dominant pollutant

Matches the official Indian scheme

Stretch only if ahead: CNN super-resolution sharpening, Graph/ST-GNN across stations. Do not add them to the resume unless they beat the simpler model on held-out data.

6. UI/UX spec (shadcn/ui, clean, live maps)

Stack: React + TypeScript + Vite + Tailwind + shadcn/ui; TanStack Query for data fetching and polling; react-leaflet (or MapLibre GL) for maps; shadcn Chart (Recharts) for time series.

One main screen, three panels:

Map (centre, full height): real basemap tiles (CARTO or Stadia free tier, with attribution; do not hammer the public OSM tile server). Layers: the PM2.5/AQI overlay as an image overlay with adjustable opacity, live CPCB station markers coloured by NAQI category, and a district boundary outline. Click anywhere for a point lookup.

Top bar: city/district Select (Command-style search across Maharashtra), pollutant Tabs (AQI, PM2.5, NO2), and a “Live · updated 14 min ago” Badge that turns amber when data is stale.

Right side Sheet/Card (on click): AQI number and category, dominant pollutant, 90% interval, reliability badge, 72 h forecast chart, and the plain-language “Why is it high here?” explanation with the top three SHAP drivers.

Bottom: a shadcn Slider time scrubber for now → +72 h that swaps the overlay.

Components to use: Card, Tabs, Select, Command, Sheet, Badge, Slider, Skeleton, Tooltip, Alert, Toggle, Chart. Use shadcn’s default neutral theme with light/dark toggle. Use the official CPCB colour scale only for AQI, and nothing decorative.

Quality bar: loading skeletons, empty and error states, a legend, keyboard-accessible controls, mobile layout where the right panel becomes a bottom drawer, and a visible “estimated, not official” note with a link to the methodology page.

7. Deployment plan

Piece

Suggested home

Notes

Front end

Vercel or Cloudflare Pages

Static Vite build; set API URL via env

API

Render, Fly.io or Railway (Docker)

Keeps models in memory; mostly serves precomputed layers, so it stays small

Hourly pipeline

GitHub Actions cron or a small worker

Scheduled runs can lag; show “data as of”

Layers and arrays

Cloudflare R2, S3 or Supabase Storage

Small PNGs and arrays; set cache headers

Station history (optional)

Postgres/PostGIS (Neon, Supabase)

Only if you add history charts

Models

GitHub Releases or Hugging Face Hub

Versioned, pulled at container start

Secrets

Host secret managers

OpenAQ key, GEE service account; never committed

Free-tier limits change, so check each provider’s current terms before relying on them.

CI/CD: on every push run ruff, pytest and the front-end build; on merge to main build the Docker image and deploy. Tag releases (v0.1, v1.0). Restrict CORS to your front-end domain, add basic rate limiting, and add a /health check used by the host.

GEE note: non-commercial use of Earth Engine needs a registered Cloud project; use a service account for scheduled jobs.

8. Resume-ready packaging

What recruiters and reviewers look for: a live link, a clear README, reproducible results, and honest limitations.

README: one-paragraph problem, architecture diagram, screenshots/GIF, live demo link, real metrics table, limitations, how to run in one command.

Model card: data sources and dates, validation protocol, known failure modes (monsoon cloud gaps, sparse stations), intended use.

Reproducibility: make data, make train, make eval, make serve; config and commit hash stored with each metrics report.

Tests: NAQI breakpoints, schema validation, matcher, leakage guards, API contract.

Resume bullets (fill the blanks only with numbers from your real metrics report):

Built an end-to-end PM2.5 estimation platform for Maharashtra fusing Sentinel-5P, MODIS MAIAC AOD, weather and OSM features with N CPCB stations; achieved leave-city-out R² of __ and MAE of __ µg/m³.

Implemented regression-kriging to produce a 1 km statewide surface with calibrated 90% intervals (empirical coverage __%).

Delivered 72 h forecasts that beat persistence by __% at +24 h; added SHAP-based plain-language explanations.

Deployed with Docker, GitHub Actions CI/CD and an hourly data pipeline; React/TypeScript/shadcn/ui front end with live maps.

Do not claim: results from the mock data, “hyperlocal street-level accuracy” without leave-station-out evidence, or live coverage of areas without nearby monitors.

9. Risks and mitigations

Risk

Mitigation

Few stations outside big cities

Report per-city metrics; show reliability and uncertainty; scope claims accordingly

Monsoon cloud cover removes AOD

AOD-free fallback model; satellite-age feature

Satellite data latency

Use latest composite with age flag; never present it as real time

OpenAQ rate limits or gaps

Cache raw pulls, back off, record provider per station

GEE quota or auth issues

Export in monthly chunks; service account; resumable jobs

Scope creep

Weekly Friday 20-min checkpoint; freeze scope at Week 5

Weak real results

Report them honestly; a clear evaluation of a modest model is still a strong portfolio piece

10. First ten actions this week

Rotate any OpenAQ key that appeared in notebook output; move it to .env.

Merge repo and notebook into one clean repo; add schemas/, LICENSE, package.json.

Remove mock-based numbers from README and docs.

Pull the Maharashtra station inventory from OpenAQ and publish the real station count by city.

Verify the ERA5/PBLH source in the GEE catalog and pick a replacement.

Run the GEE exports for one pilot month over Maharashtra.

Build the first real station-satellite pair file and inspect missingness.

Train a first Ridge and LightGBM model with leave-station-out CV.

Scaffold the Vite + TypeScript + shadcn/ui app with a live basemap and station markers.

Set up CI and one deploy target so a public URL exists early; improve it each week.