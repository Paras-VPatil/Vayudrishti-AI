/**
 * export_modis_aod.js
 * Google Earth Engine script — exports MODIS Terra MOD04_3K Aerosol Optical Depth
 * for a given date range and region of interest to Google Drive.
 *
 * Usage: Paste into GEE Code Editor and click Run, or execute via earthengine CLI.
 */

// ── Configuration ──────────────────────────────────────────────────────────────
var START_DATE = '2024-01-01';
var END_DATE   = '2024-01-31';
var SCALE      = 3000;          // 3 km native resolution
var DRIVE_DIR  = 'vayudrishti_modis_aod';

// India bounding box (approx.)
var REGION = ee.Geometry.Rectangle([68.0, 6.5, 97.5, 37.5]);

// ── Load MODIS MOD04_3K collection ────────────────────────────────────────────
var modis = ee.ImageCollection('MODIS/061/MOD04_3K')
  .filterDate(START_DATE, END_DATE)
  .filterBounds(REGION)
  .select([
    'Optical_Depth_Land_And_Ocean',   // AOD 550 nm (best-coverage composite)
    'Optical_Depth_055',              // AOD 550 nm (deep-blue + dark-target)
    'AOD_QA',                         // Quality assurance bitmap
    'Scattering_Angle',
    'Solar_Zenith',
    'Sensor_Zenith'
  ]);

print('MODIS image count:', modis.size());

// ── Scale factors (from MODIS product spec) ───────────────────────────────────
var scaleAOD = function(image) {
  var aod = image
    .select('Optical_Depth_Land_And_Ocean')
    .multiply(0.001)
    .rename('aod_550nm');
  var aod055 = image
    .select('Optical_Depth_055')
    .multiply(0.001)
    .rename('aod_470nm');
  var qa = image.select('AOD_QA').rename('aod_qa');
  return aod.addBands(aod055).addBands(qa)
    .copyProperties(image, ['system:time_start']);
};

var scaled = modis.map(scaleAOD);

// ── Monthly composite (median) ────────────────────────────────────────────────
var monthly = scaled.median().clip(REGION);

// ── Visualisation (optional — for Code Editor map preview) ────────────────────
Map.centerObject(REGION, 5);
Map.addLayer(monthly.select('aod_550nm'), {min: 0, max: 1, palette: ['blue','yellow','red']}, 'AOD 550nm');

// ── Export to Google Drive ────────────────────────────────────────────────────
Export.image.toDrive({
  image:       monthly,
  description: 'modis_aod_' + START_DATE + '_to_' + END_DATE,
  folder:      DRIVE_DIR,
  fileNamePrefix: 'modis_aod_monthly',
  region:      REGION,
  scale:       SCALE,
  crs:         'EPSG:4326',
  maxPixels:   1e10
});

print('Export task submitted. Check Tasks panel.');
