/**
 * export_era5.js
 * Google Earth Engine script — exports ERA5-Land hourly reanalysis variables
 * (wind, humidity, temperature, boundary-layer height, precipitation) to Drive.
 */

// ── Configuration ──────────────────────────────────────────────────────────────
var START_DATE = '2024-01-01';
var END_DATE   = '2024-01-31';
var SCALE      = 11132;   // ~0.1° ≈ 11 km (ERA5-Land resolution)
var DRIVE_DIR  = 'vayudrishti_era5';

var REGION = ee.Geometry.Rectangle([68.0, 6.5, 97.5, 37.5]);

// ── Load ERA5-Land hourly collection ─────────────────────────────────────────
var era5 = ee.ImageCollection('ECMWF/ERA5_LAND/HOURLY')
  .filterDate(START_DATE, END_DATE)
  .filterBounds(REGION)
  .select([
    'u_component_of_wind_10m',          // East-ward wind [m/s]
    'v_component_of_wind_10m',          // North-ward wind [m/s]
    '2m_temperature',                   // Air temperature [K]
    '2m_dewpoint_temperature',          // Dew-point temperature [K]
    'surface_pressure',                 // [Pa]
    'total_precipitation_hourly'        // [m]
  ]);

// ── Derived variables ─────────────────────────────────────────────────────────
var addDerived = function(image) {
  var u   = image.select('u_component_of_wind_10m');
  var v   = image.select('v_component_of_wind_10m');
  var T   = image.select('2m_temperature');
  var Td  = image.select('2m_dewpoint_temperature');
  var sp  = image.select('surface_pressure');
  var pr  = image.select('total_precipitation_hourly');

  // Wind speed & direction
  var ws  = u.pow(2).add(v.pow(2)).sqrt().rename('wind_speed_10m');
  var wd  = u.atan2(v).multiply(180 / Math.PI).add(360).mod(360).rename('wind_direction_10m');

  // Temperature in °C
  var T_C = T.subtract(273.15).rename('temperature_2m_celsius');

  // Relative humidity via Magnus formula approximation
  var rh  = Td.subtract(T).multiply(17.67 / 243.5)
    .exp().multiply(100).rename('relative_humidity_2m_pct');

  // Pressure in hPa
  var sp_hpa = sp.divide(100).rename('surface_pressure_hpa');

  // Precipitation in mm
  var pr_mm = pr.multiply(1000).rename('precipitation_1h_mm');

  return image
    .addBands(ws).addBands(wd).addBands(T_C)
    .addBands(rh).addBands(sp_hpa).addBands(pr_mm)
    .copyProperties(image, ['system:time_start']);
};

var processed = era5.map(addDerived);

// ── Daily median composite ────────────────────────────────────────────────────
var daily = processed.select([
  'wind_speed_10m', 'wind_direction_10m',
  'temperature_2m_celsius', 'relative_humidity_2m_pct',
  'surface_pressure_hpa', 'precipitation_1h_mm'
]).median().clip(REGION);

// ── Map preview ───────────────────────────────────────────────────────────────
Map.centerObject(REGION, 5);
Map.addLayer(daily.select('relative_humidity_2m_pct'),
  {min: 0, max: 100, palette: ['red','yellow','blue']}, 'Relative Humidity');

// ── Export ────────────────────────────────────────────────────────────────────
Export.image.toDrive({
  image:          daily,
  description:    'era5_' + START_DATE + '_to_' + END_DATE,
  folder:         DRIVE_DIR,
  fileNamePrefix: 'era5_daily_median',
  region:         REGION,
  scale:          SCALE,
  crs:            'EPSG:4326',
  maxPixels:      1e10
});

print('ERA5 export task submitted.');
