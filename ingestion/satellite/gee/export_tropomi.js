/**
 * export_tropomi.js
 * Google Earth Engine script — exports Sentinel-5P TROPOMI L2 trace-gas columns
 * (NO₂, SO₂, CO, O₃, UV Aerosol Index) to Google Drive.
 */

// ── Configuration ──────────────────────────────────────────────────────────────
var START_DATE = '2024-01-01';
var END_DATE   = '2024-01-31';
var SCALE      = 3500;   // ~3.5 km (TROPOMI pixel width)
var DRIVE_DIR  = 'vayudrishti_tropomi';

var REGION = ee.Geometry.Rectangle([68.0, 6.5, 97.5, 37.5]);

// ── Helper: load, QA-filter, and select a single TROPOMI product ──────────────
function loadTROPOMI(collection, band, qaThreshold, scaleFactor, outName) {
  return ee.ImageCollection(collection)
    .filterDate(START_DATE, END_DATE)
    .filterBounds(REGION)
    .filter(ee.Filter.gte('qa_value', qaThreshold))
    .select(band)
    .map(function(img) {
      return img.multiply(scaleFactor).rename(outName)
        .copyProperties(img, ['system:time_start']);
    });
}

// ── Load each product ─────────────────────────────────────────────────────────
var no2 = loadTROPOMI(
  'COPERNICUS/S5P/OFFL/L3_NO2',
  'tropospheric_NO2_column_number_density',
  0.75, 1e6, 'no2_tropospheric_column_umolm2'  // converted µmol/m²
);

var so2 = loadTROPOMI(
  'COPERNICUS/S5P/OFFL/L3_SO2',
  'SO2_column_number_density',
  0.5, 1e6, 'so2_column_umolm2'
);

var co = loadTROPOMI(
  'COPERNICUS/S5P/OFFL/L3_CO',
  'CO_column_number_density',
  0.5, 1, 'co_column_molm2'
);

var o3 = loadTROPOMI(
  'COPERNICUS/S5P/OFFL/L3_O3',
  'O3_column_number_density',
  0.5, 1, 'o3_column_molm2'
);

var aai = ee.ImageCollection('COPERNICUS/S5P/OFFL/L3_AER_AI')
  .filterDate(START_DATE, END_DATE)
  .filterBounds(REGION)
  .select('absorbing_aerosol_index')
  .map(function(img) {
    return img.rename('uv_aerosol_index')
      .copyProperties(img, ['system:time_start']);
  });

// ── Monthly median composites ─────────────────────────────────────────────────
var combined = no2.median().clip(REGION)
  .addBands(so2.median().clip(REGION))
  .addBands(co.median().clip(REGION))
  .addBands(o3.median().clip(REGION))
  .addBands(aai.median().clip(REGION));

// ── Map preview ───────────────────────────────────────────────────────────────
Map.centerObject(REGION, 5);
Map.addLayer(combined.select('no2_tropospheric_column_umolm2'),
  {min: 0, max: 200, palette: ['white','yellow','orange','red']}, 'NO₂');

// ── Export ────────────────────────────────────────────────────────────────────
Export.image.toDrive({
  image:          combined,
  description:    'tropomi_' + START_DATE + '_to_' + END_DATE,
  folder:         DRIVE_DIR,
  fileNamePrefix: 'tropomi_monthly',
  region:         REGION,
  scale:          SCALE,
  crs:            'EPSG:4326',
  maxPixels:      1e10
});

print('TROPOMI export task submitted.');
