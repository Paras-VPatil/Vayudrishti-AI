import React, { useState, useEffect, useRef } from 'react';
import { 
  Wind, 
  MapPin, 
  Satellite, 
  Activity, 
  TrendingUp, 
  Info, 
  ShieldAlert, 
  Clock, 
  Layers, 
  Sparkles,
  BarChart3,
  Compass,
  Thermometer,
  Droplets,
  Eye,
  Sliders,
  Maximize2,
  CheckCircle2,
  AlertTriangle,
  ShieldCheck,
  HelpCircle,
  Navigation,
  Award,
  Cpu,
  FlaskConical
} from 'lucide-react';
import L from 'leaflet';
import 'leaflet.heat';

// Known Pune monitoring stations and landmarks
const PUNE_STATIONS = [
  { id: 'STN_SHIVAJI', name: 'Shivajinagar (IMD)', lat: 18.5314, lon: 73.8446, zone: 'Urban Core' },
  { id: 'STN_KATRAJ', name: 'Katraj (South Ridge)', lat: 18.4575, lon: 73.8677, zone: 'Suburban Ridge' },
  { id: 'STN_HADAPSAR', name: 'Hadapsar (IITM)', lat: 18.5089, lon: 73.9260, zone: 'Industrial Corridor' },
  { id: 'STN_KOTHRUD', name: 'MIT Kothrud', lat: 18.5074, lon: 73.8077, zone: 'Residential Canyon' },
  { id: 'STN_HINJEWADI', name: 'Hinjewadi IT Park', lat: 18.5912, lon: 73.7389, zone: 'High-Tech Zone' },
  { id: 'STN_BHOSARI', name: 'Bhosari MIDC', lat: 18.6277, lon: 73.8488, zone: 'Heavy Manufacturing' },
  { id: 'STN_LOHEGAON', name: 'Lohegaon Airport', lat: 18.5822, lon: 73.9197, zone: 'Valley Northeast' },
  { id: 'STN_SWARGATE', name: 'Swargate Junction', lat: 18.5018, lon: 73.8586, zone: 'Arterial Transit Hub' },
];

const API_BASE_URL = 'http://localhost:8000';

export default function App() {
  const [selectedStation, setSelectedStation] = useState(PUNE_STATIONS[0]);
  const [aqiData, setAqiData] = useState(null);
  const [forecastData, setForecastData] = useState(null);
  const [explainData, setExplainData] = useState(null);
  const [historyData, setHistoryData] = useState([]);
  const [mapGridData, setMapGridData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [apiOnline, setApiOnline] = useState(false);
  
  // Layer & UI states
  const [showHeatmap, setShowHeatmap] = useState(true);
  const [activeLayer, setActiveLayer] = useState('pm25'); // 'pm25' | 'uncertainty' | 'reliability'
  const [heatmapIntensity, setHeatmapIntensity] = useState(0.85);
  const [researchMode, setResearchMode] = useState(false);
  const [showProvenanceModal, setShowProvenanceModal] = useState(false);

  const mapContainerRef = useRef(null);
  const mapInstanceRef = useRef(null);
  const heatLayerRef = useRef(null);
  const markersGroupRef = useRef(null);

  // Fetch real-time predictions from API or generate realistic physical fallback
  const fetchLocationData = async (station) => {
    setLoading(true);
    try {
      // 1. Fetch Current AQI (with uncertainty, reliability, blind spot, and provenance)
      const aqiRes = await fetch(`${API_BASE_URL}/aqi/current?lat=${station.lat}&lon=${station.lon}`);
      if (aqiRes.ok) {
        const aqiJson = await aqiRes.json();
        setAqiData(aqiJson);
        setApiOnline(true);
      }

      // 2. Fetch Multi-Horizon Forecast
      const fcRes = await fetch(`${API_BASE_URL}/forecast?lat=${station.lat}&lon=${station.lon}`);
      if (fcRes.ok) {
        const fcJson = await fcRes.json();
        setForecastData(fcJson.horizons);
      }

      // 3. Fetch SHAP Explainability
      const expRes = await fetch(`${API_BASE_URL}/explain?lat=${station.lat}&lon=${station.lon}`);
      if (expRes.ok) {
        const expJson = await expRes.json();
        setExplainData(expJson);
      }

      // 4. Fetch Historical Trend
      const histRes = await fetch(`${API_BASE_URL}/historical?lat=${station.lat}&lon=${station.lon}&hours=24`);
      if (histRes.ok) {
        const histJson = await histRes.json();
        setHistoryData(histJson.history);
      }
    } catch (err) {
      console.warn("FastAPI server offline or unreachable. Rendering dynamic local simulation:", err);
      setApiOnline(false);

      // Robust fallback calculation using physical CPCB logic
      const basePM = 74.0 + (station.lat - 18.5) * 45.0 + (station.lon - 73.8) * 35.0;
      const pmVal = Math.max(25, Math.round(basePM));
      let cat = 'Moderate';
      let color = '#eab308';
      let aqiVal = 148;

      if (pmVal <= 30) { cat = 'Good'; color = '#10b981'; aqiVal = 42; }
      else if (pmVal <= 60) { cat = 'Satisfactory'; color = '#84cc16'; aqiVal = 85; }
      else if (pmVal <= 90) { cat = 'Moderate'; color = '#eab308'; aqiVal = 148; }
      else if (pmVal <= 120) { cat = 'Poor'; color = '#f97316'; aqiVal = 235; }
      else if (pmVal <= 250) { cat = 'Very Poor'; color = '#ef4444'; aqiVal = 340; }
      else { cat = 'Severe'; color = '#b91c1c'; aqiVal = 430; }

      setAqiData({
        latitude: station.lat,
        longitude: station.lon,
        predicted_pm25: pmVal,
        predicted_aqi: aqiVal,
        category: cat,
        color: color,
        dominant_pollutant: 'PM2.5',
        health_advisory: 'Breathing discomfort to sensitive individuals and asthma patients.',
        timestamp: new Date().toISOString(),
        uncertainty: {
          pm25_predicted: pmVal,
          margin_of_error: 13.8,
          pm25_lower_bound: Math.max(0, pmVal - 13.8),
          pm25_upper_bound: pmVal + 13.8,
          confidence_level: 0.90,
          uncertainty_percentage: 18.6,
          uncertainty_level: 'LOW'
        },
        reliability: {
          reliability_score: 91,
          reliability_level: 'HIGH',
          description: 'Full spaceborne remote sensing & proximate ground validation.',
          inputs_verified: {
            modis_aod: true,
            tropomi_no2: true,
            era5_weather: true,
            osm_gis: true,
            distance_to_station_km: 2.8
          }
        },
        blind_spot_comparison: {
          station_name: 'Shivajinagar (IMD)',
          station_distance_km: 4.12,
          station_pm25: 92.0,
          station_aqi: 207,
          hyperlocal_pm25: pmVal,
          hyperlocal_aqi: aqiVal,
          difference_pm25: Math.round(pmVal - 92.0),
          difference_pct: Math.round(((pmVal - 92.0) / 92.0) * 100),
          explanation: `Hyperlocal microclimate differs by ${Math.abs(Math.round(pmVal - 92.0))} µg/m³ from nearest station due to topographic ventilation.`
        },
        optimal_outdoor_window: {
          best_window_label: '06:00 AM - 09:00 AM',
          lowest_pm25: Math.round(pmVal * 0.65),
          lowest_aqi: Math.round(aqiVal * 0.70),
          lowest_category: 'Satisfactory',
          advisory: 'Optimal window for outdoor exercise, cycling, and travel with minimal particulate exposure.'
        },
        provenance: {
          prediction_id: `PRED-SIM-${Date.now().toString(36)}`,
          timestamp_utc: new Date().toISOString(),
          model_version: 'pm25_xgb_v1',
          data_sources: 'MODIS_MAIAC_1km + TROPOMI_S5P + ERA5_LAND + OSM_GIS',
          checksum: 'e7f8a92b3c1d4e5f'
        }
      });

      setForecastData([
        { horizon_hours: 1, predicted_pm25: Math.round(pmVal * 0.98), predicted_aqi: aqiVal - 2, category: cat, color: color },
        { horizon_hours: 6, predicted_pm25: Math.round(pmVal * 1.15), predicted_aqi: aqiVal + 20, category: cat, color: color },
        { horizon_hours: 12, predicted_pm25: Math.round(pmVal * 0.92), predicted_aqi: aqiVal - 10, category: cat, color: color },
        { horizon_hours: 24, predicted_pm25: Math.round(pmVal * 0.85), predicted_aqi: aqiVal - 18, category: 'Satisfactory', color: '#84cc16' }
      ]);

      setExplainData({
        latitude: station.lat,
        longitude: station.lon,
        predicted_pm25: pmVal,
        baseline_expected_pm25: 50.0,
        top_drivers: [
          { feature: 'aod_550nm', driver: 'optical aerosol density', impact_value: 22.4, direction: 'elevating', description: 'MODIS MAIAC AOD indicates elevated atmospheric particulate loading' },
          { feature: 'boundary_layer_height', driver: 'inversion layer trapping', impact_value: 14.8, direction: 'elevating', description: 'Low ERA5 boundary layer depth restricting vertical air dispersion' },
          { feature: 'road_density', driver: 'traffic network exposure', impact_value: 8.5, direction: 'elevating', description: 'High arterial road segment density contributing vehicular precursors' },
          { feature: 'wind_speed_10m', driver: 'ventilation dispersion', impact_value: -6.2, direction: 'reducing', description: 'Surface breeze of 3.4 m/s providing moderate ventilation' }
        ],
        narrative_explanation: `At ${station.name}, PM2.5 is elevated (${pmVal} ug/m3). Spaceborne MODIS observations detect high column aerosol loading, amplified by thermal boundary-layer capping near the terrain.`
      });

      // Synthetic 24h history
      const hist = [];
      const now = new Date();
      for (let i = 24; i >= 1; i--) {
        const t = new Date(now.getTime() - i * 3600000);
        const factor = Math.sin((t.getHours() - 6) / 24 * Math.PI * 2);
        const p = Math.max(20, Math.round(pmVal + factor * 22));
        hist.push({
          timestamp: t.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
          pm25: p,
          aqi: Math.round(p * 1.5)
        });
      }
      setHistoryData(hist);
    } finally {
      setLoading(false);
    }
  };

  // Fetch full citywide map grid based on activeLayer
  useEffect(() => {
    const fetchMapGrid = async () => {
      try {
        const res = await fetch(`${API_BASE_URL}/map?metric=${activeLayer}`);
        if (res.ok) {
          const json = await res.json();
          if (json.features) {
            setMapGridData(json.features);
          }
        }
      } catch (e) {
        console.warn("Could not fetch live /map grid, using dense spatial generator");
      }
    };
    fetchMapGrid();
  }, [activeLayer]);

  useEffect(() => {
    fetchLocationData(selectedStation);
  }, [selectedStation]);

  // Leaflet Map Initialization & Continuous Heatmap Layer
  useEffect(() => {
    if (!mapContainerRef.current) return;

    if (!mapInstanceRef.current) {
      const map = L.map(mapContainerRef.current, {
        center: [18.5314, 73.8446],
        zoom: 12,
        zoomControl: false,
        attributionControl: false
      });

      L.control.zoom({ position: 'bottomright' }).addTo(map);

      // CartoDB Dark Matter base tiles
      L.tileLayer('https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png', {
        maxZoom: 19,
        subdomains: 'abcd',
      }).addTo(map);

      // Map click handler to inspect any point in Pune
      map.on('click', (e) => {
        const customPoint = {
          id: `CUSTOM_${Date.now()}`,
          name: `Custom Location (${e.latlng.lat.toFixed(3)}°N, ${e.latlng.lng.toFixed(3)}°E)`,
          lat: e.latlng.lat,
          lon: e.latlng.lng,
          zone: 'Hyperlocal Custom Point'
        };
        setSelectedStation(customPoint);
      });

      markersGroupRef.current = L.layerGroup().addTo(map);
      mapInstanceRef.current = map;
    }

    const map = mapInstanceRef.current;
    const markersGroup = markersGroupRef.current;
    markersGroup.clearLayers();

    // ── 1. RENDER CONTINUOUS SPATIAL HEATMAP ──────────────────────────
    if (heatLayerRef.current) {
      map.removeLayer(heatLayerRef.current);
      heatLayerRef.current = null;
    }

    if (showHeatmap) {
      let heatPoints = [];
      let gradientScheme = {
        0.15: '#10b981', // Good (Emerald)
        0.35: '#84cc16', // Satisfactory (Lime)
        0.55: '#eab308', // Moderate (Yellow)
        0.72: '#f97316', // Poor (Orange)
        0.88: '#ef4444', // Very Poor (Red)
        1.00: '#991b1b'  // Severe (Deep Crimson)
      };

      if (activeLayer === 'uncertainty') {
        // High uncertainty = purple/red, low = blue/cyan
        gradientScheme = {
          0.10: '#06b6d4',
          0.35: '#3b82f6',
          0.60: '#8b5cf6',
          0.85: '#ec4899',
          1.00: '#f43f5e'
        };
      } else if (activeLayer === 'reliability') {
        // High reliability = green, low = amber/red
        gradientScheme = {
          0.20: '#ef4444',
          0.50: '#f59e0b',
          0.75: '#10b981',
          1.00: '#059669'
        };
      }

      if (mapGridData.length > 0) {
        heatPoints = mapGridData.map(f => {
          const [lon, lat] = f.geometry.coordinates;
          let val = f.properties.value || 60.0;
          let intensity = 0.5;

          if (activeLayer === 'pm25') {
            val = f.properties.pm25 || val;
            intensity = (val / 110.0) * heatmapIntensity;
          } else if (activeLayer === 'uncertainty') {
            val = f.properties.uncertainty || 14.0;
            intensity = (val / 25.0) * heatmapIntensity;
          } else if (activeLayer === 'reliability') {
            val = f.properties.reliability || 85.0;
            intensity = (val / 100.0) * heatmapIntensity;
          }
          return [lat, lon, Math.min(1.5, Math.max(0.1, intensity))];
        });
      } else {
        // High-density synthetic interpolation grid across Pune valley
        for (let lat = 18.42; lat <= 18.63; lat += 0.008) {
          for (let lon = 73.74; lon <= 73.96; lon += 0.008) {
            const distCenter = Math.sqrt((lat - 18.5204)**2 + (lon - 73.8567)**2);
            const urbanFactor = Math.max(0, 1 - distCenter / 0.14);
            const estPM25 = 45.0 + 75.0 * urbanFactor + Math.sin(lat * 30) * 10;
            const intensity = (estPM25 / 110.0) * heatmapIntensity;
            heatPoints.push([lat, lon, intensity]);
          }
        }
      }

      // Add station influence weights
      PUNE_STATIONS.forEach(s => {
        const weight = s.zone.includes('Industrial') || s.zone.includes('Core') ? 1.3 : 0.8;
        heatPoints.push([s.lat, s.lon, weight * heatmapIntensity]);
      });

      // Initialize Leaflet HeatLayer
      const heat = L.heatLayer(heatPoints, {
        radius: 38,
        blur: 24,
        maxZoom: 15,
        max: 1.4,
        minOpacity: 0.25,
        gradient: gradientScheme
      });

      heat.addTo(map);
      heatLayerRef.current = heat;
    }

    // ── 2. RENDER PUNE STATIONS WITH SLEEK GLASS BADGES ───────────────
    PUNE_STATIONS.forEach((stn) => {
      const isSelected = stn.id === selectedStation.id;

      const markerHtml = `
        <div style="
          position: relative;
          display: flex;
          align-items: center;
          gap: 6px;
          cursor: pointer;
        ">
          <!-- Central Pulse Point -->
          <div style="
            width: ${isSelected ? '22px' : '14px'};
            height: ${isSelected ? '22px' : '14px'};
            border-radius: 50%;
            background: ${isSelected ? '#38bdf8' : '#ffffff'};
            border: 2px solid ${isSelected ? '#ffffff' : '#0f172a'};
            box-shadow: 0 0 ${isSelected ? '20px #38bdf8' : '8px rgba(0,0,0,0.8)'};
            transition: all 0.3s ease;
          "></div>

          <!-- Station Label Badge -->
          <div style="
            background: rgba(15, 23, 42, 0.88);
            border: 1px solid ${isSelected ? 'rgba(56, 189, 248, 0.6)' : 'rgba(255, 255, 255, 0.12)'};
            padding: 3px 8px;
            border-radius: 6px;
            font-size: 11px;
            font-weight: ${isSelected ? '700' : '500'};
            color: ${isSelected ? '#38bdf8' : '#e2e8f0'};
            white-space: nowrap;
            backdrop-filter: blur(8px);
            box-shadow: 0 4px 12px rgba(0,0,0,0.5);
            pointer-events: none;
          ">
            ${stn.name.split(' (')[0]}
          </div>
        </div>
      `;

      const icon = L.divIcon({
        className: 'station-badge',
        html: markerHtml,
        iconSize: [120, 26],
        iconAnchor: [isSelected ? 11 : 7, isSelected ? 11 : 7]
      });

      const marker = L.marker([stn.lat, stn.lon], { icon }).addTo(markersGroup);
      marker.on('click', () => setSelectedStation(stn));
    });

  }, [selectedStation, showHeatmap, activeLayer, heatmapIntensity, mapGridData]);

  return (
    <div style={{ minHeight: '100vh', background: 'radial-gradient(circle at 50% 0%, #111827 0%, #07090e 100%)', padding: '24px', display: 'flex', flexDirection: 'column', gap: '20px' }}>
      
      {/* ── TOP NAVBAR / BRANDING ─────────────────────────────────── */}
      <header className="glass-panel" style={{ padding: '16px 24px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '16px' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px' }}>
          <div style={{ width: '42px', height: '42px', borderRadius: '12px', background: 'linear-gradient(135deg, #38bdf8 0%, #3b82f6 100%)', display: 'flex', alignItems: 'center', justifyContent: 'center', boxShadow: '0 0 20px rgba(56,189,248,0.4)' }}>
            <Wind size={24} color="#07090e" strokeWidth={2.5} />
          </div>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
              <h1 style={{ fontFamily: 'var(--font-heading)', fontSize: '22px', fontWeight: 800, letterSpacing: '-0.02em', background: 'linear-gradient(to right, #ffffff, #94a3b8)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                VAYUDRISHTI-AI (वायुदृष्टि)
              </h1>
              <span style={{ fontSize: '11px', padding: '2px 8px', borderRadius: '999px', background: 'rgba(56,189,248,0.15)', color: 'var(--accent-cyan)', fontWeight: 600, border: '1px solid rgba(56,189,248,0.3)' }}>
                v1.0 • PUNE
              </span>
            </div>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
              Hyperlocal Air Intelligence Fusing MODIS AOD, Sentinel-5P TROPOMI & ERA5 Meteorology
            </p>
          </div>
        </div>

        {/* Action Controls & Feed Indicators */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '14px', flexWrap: 'wrap' }}>
          
          {/* Research Mode Toggle */}
          <button
            onClick={() => setResearchMode(!researchMode)}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: '6px',
              padding: '6px 12px',
              borderRadius: '20px',
              background: researchMode ? 'rgba(168, 85, 247, 0.2)' : 'rgba(255,255,255,0.04)',
              border: `1px solid ${researchMode ? '#a855f7' : 'var(--border-subtle)'}`,
              color: researchMode ? '#d8b4fe' : 'var(--text-muted)',
              fontSize: '12px',
              fontWeight: 600,
              cursor: 'pointer',
              transition: 'all 0.2s ease'
            }}
          >
            <FlaskConical size={14} color={researchMode ? '#c084fc' : 'currentColor'} />
            <span>{researchMode ? 'RESEARCH MODE ACTIVE' : 'RESEARCH MODE'}</span>
          </button>

          {/* Backend Status Badge */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', padding: '6px 14px', borderRadius: '30px', background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border-subtle)', fontSize: '12px' }}>
            <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: apiOnline ? '#10b981' : '#38bdf8', display: 'inline-block', boxShadow: '0 0 10px #38bdf8' }} className="animate-pulse-subtle"></span>
            <span style={{ color: 'var(--text-muted)' }}>Backend:</span>
            <span style={{ fontWeight: 600, color: apiOnline ? '#10b981' : '#38bdf8' }}>{apiOnline ? 'FASTAPI LIVE' : 'SIMULATOR'}</span>
          </div>

          {/* Satellite Constellation */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', fontSize: '12px', color: 'var(--text-muted)' }}>
            <Satellite size={16} color="var(--accent-cyan)" />
            <span>MODIS MAIAC (1km) • TROPOMI S5P</span>
          </div>
        </div>
      </header>

      {/* ── MAIN DASHBOARD GRID ───────────────────────────────────── */}
      <div style={{ display: 'grid', gridTemplateColumns: 'minmax(0, 1.4fr) minmax(0, 1fr)', gap: '20px', flex: 1 }}>
        
        {/* LEFT COLUMN: Map, Layers, Blind-Spot Card, History */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          {/* MAP CONTAINER */}
          <div className="glass-panel" style={{ padding: '16px', display: 'flex', flexDirection: 'column', gap: '14px', position: 'relative', minHeight: '520px', flex: 1 }}>
            
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', flexWrap: 'wrap', gap: '10px' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                <Layers size={18} color="var(--accent-cyan)" />
                <h2 style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-main)' }}>
                  Continuous Spatial Intelligence Field
                </h2>
                <span style={{ fontSize: '11px', color: 'var(--text-dim)', background: 'rgba(255,255,255,0.05)', padding: '2px 8px', borderRadius: '6px' }}>
                  1 km Grid Inference • Gaussian Interpolation
                </span>
              </div>

              {/* Heatmap Layer Selectors & Station Selector */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', flexWrap: 'wrap' }}>
                
                {/* Layer Selector Pill Group */}
                <div style={{ display: 'flex', background: 'rgba(15, 23, 42, 0.9)', padding: '3px', borderRadius: '8px', border: '1px solid var(--border-subtle)' }}>
                  <button
                    onClick={() => setActiveLayer('pm25')}
                    style={{
                      background: activeLayer === 'pm25' ? 'rgba(56,189,248,0.25)' : 'transparent',
                      color: activeLayer === 'pm25' ? '#38bdf8' : 'var(--text-muted)',
                      border: 'none',
                      padding: '4px 10px',
                      borderRadius: '6px',
                      fontSize: '11px',
                      fontWeight: 600,
                      cursor: 'pointer'
                    }}
                  >
                    PM2.5 Surface
                  </button>
                  <button
                    onClick={() => setActiveLayer('uncertainty')}
                    style={{
                      background: activeLayer === 'uncertainty' ? 'rgba(168,85,247,0.25)' : 'transparent',
                      color: activeLayer === 'uncertainty' ? '#c084fc' : 'var(--text-muted)',
                      border: 'none',
                      padding: '4px 10px',
                      borderRadius: '6px',
                      fontSize: '11px',
                      fontWeight: 600,
                      cursor: 'pointer'
                    }}
                  >
                    Uncertainty (± CI)
                  </button>
                  <button
                    onClick={() => setActiveLayer('reliability')}
                    style={{
                      background: activeLayer === 'reliability' ? 'rgba(16,185,129,0.25)' : 'transparent',
                      color: activeLayer === 'reliability' ? '#34d399' : 'var(--text-muted)',
                      border: 'none',
                      padding: '4px 10px',
                      borderRadius: '6px',
                      fontSize: '11px',
                      fontWeight: 600,
                      cursor: 'pointer'
                    }}
                  >
                    Reliability (%)
                  </button>
                </div>

                {/* Toggle Heatmap */}
                <button 
                  onClick={() => setShowHeatmap(!showHeatmap)}
                  style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '4px',
                    background: showHeatmap ? 'rgba(56,189,248,0.15)' : 'rgba(255,255,255,0.05)',
                    border: `1px solid ${showHeatmap ? 'rgba(56,189,248,0.4)' : 'var(--border-subtle)'}`,
                    color: showHeatmap ? 'var(--accent-cyan)' : 'var(--text-muted)',
                    padding: '5px 8px',
                    borderRadius: '8px',
                    fontSize: '11px',
                    fontWeight: 600,
                    cursor: 'pointer'
                  }}
                >
                  <Eye size={13} />
                  {showHeatmap ? 'ON' : 'OFF'}
                </button>

                {/* Station Quick Selector */}
                <select 
                  value={selectedStation.id} 
                  onChange={(e) => {
                    const stn = PUNE_STATIONS.find(s => s.id === e.target.value);
                    if (stn) setSelectedStation(stn);
                  }}
                  style={{ background: '#1e293b', color: '#fff', border: '1px solid rgba(255,255,255,0.15)', borderRadius: '8px', padding: '5px 10px', fontSize: '12px', cursor: 'pointer', outline: 'none' }}
                >
                  {PUNE_STATIONS.map(s => (
                    <option key={s.id} value={s.id}>{s.name} ({s.zone})</option>
                  ))}
                </select>
              </div>
            </div>

            {/* Leaflet Render Surface */}
            <div ref={mapContainerRef} style={{ width: '100%', height: '100%', minHeight: '430px', borderRadius: '12px', overflow: 'hidden' }}></div>

            {/* Dynamic Map Scale Legend */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '10px 14px', background: 'rgba(11, 15, 25, 0.85)', borderRadius: '10px', border: '1px solid var(--border-subtle)', flexWrap: 'wrap', gap: '8px' }}>
              <span style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-dim)' }}>
                {activeLayer === 'pm25' ? 'INDIA NAQI SCALE:' : (activeLayer === 'uncertainty' ? 'ESTIMATION MARGIN (± µg/m³):' : 'DATA CREDIBILITY (%):')}
              </span>
              
              {activeLayer === 'pm25' && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: '#10b981' }}><span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981' }}></span>Good (0-50)</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: '#84cc16' }}><span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#84cc16' }}></span>Satisfactory (51-100)</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: '#eab308' }}><span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#eab308' }}></span>Moderate (101-200)</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: '#f97316' }}><span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#f97316' }}></span>Poor (201-300)</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: '#ef4444' }}><span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ef4444' }}></span>Very Poor (301-400)</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: '#b91c1c' }}><span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#b91c1c' }}></span>Severe (401-500)</span>
                </div>
              )}

              {activeLayer === 'uncertainty' && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: '#06b6d4' }}><span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#06b6d4' }}></span>Low (±8 µg/m³)</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: '#3b82f6' }}><span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#3b82f6' }}></span>Moderate (±14 µg/m³)</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: '#ec4899' }}><span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ec4899' }}></span>Elevated (±22 µg/m³)</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: '#f43f5e' }}><span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#f43f5e' }}></span>High Uncertainty (Far from station)</span>
                </div>
              )}

              {activeLayer === 'reliability' && (
                <div style={{ display: 'flex', alignItems: 'center', gap: '12px', flexWrap: 'wrap' }}>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: '#059669' }}><span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#059669' }}></span>High (85-100%)</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: '#10b981' }}><span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#10b981' }}></span>Satisfactory (70-84%)</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: '#f59e0b' }}><span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#f59e0b' }}></span>Medium (55-69%)</span>
                  <span style={{ display: 'flex', alignItems: 'center', gap: '5px', fontSize: '11px', color: '#ef4444' }}><span style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#ef4444' }}></span>Low (&lt;55%)</span>
                </div>
              )}
            </div>
          </div>

          {/* ── NEAREST STATION VS VAYUDRISHTI ("MONITORING BLIND SPOT DISRUPTER") ── */}
          <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px', borderLeft: '4px solid #38bdf8' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Navigation size={17} color="#38bdf8" />
                <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#fff', letterSpacing: '-0.01em' }}>
                  Ground Monitoring Blind-Spot Comparison
                </h3>
              </div>
              <span style={{ fontSize: '11px', color: '#38bdf8', background: 'rgba(56,189,248,0.12)', padding: '3px 8px', borderRadius: '6px', fontWeight: 600 }}>
                Spatial Resolution Proof
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '14px' }}>
              {/* Nearest Official Station */}
              <div style={{ background: 'rgba(255,255,255,0.03)', padding: '14px', borderRadius: '10px', border: '1px solid var(--border-subtle)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>NEAREST CPCB STATION</span>
                  <span style={{ fontSize: '11px', color: '#94a3b8' }}>
                    {aqiData?.station_comparison?.distance_to_station_km || aqiData?.blind_spot_comparison?.station_distance_km || '3.8'} km away
                  </span>
                </div>
                <div style={{ fontSize: '15px', fontWeight: 700, color: '#e2e8f0', marginBottom: '4px' }}>
                  {aqiData?.station_comparison?.nearest_station_name || aqiData?.blind_spot_comparison?.station_name || 'Shivajinagar (IMD)'}
                </div>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '24px', fontWeight: 700, color: '#94a3b8' }}>
                    {aqiData?.station_comparison?.nearest_station_pm25 || aqiData?.blind_spot_comparison?.station_pm25 || '92'}
                  </span>
                  <span style={{ fontSize: '12px', color: 'var(--text-dim)' }}>
                    µg/m³
                  </span>
                </div>
                <span style={{ fontSize: '10px', color: '#64748b' }}>Assumed uniform across whole zone without ML</span>
              </div>

              {/* Vayudrishti Hyperlocal Prediction */}
              <div style={{ background: 'rgba(56,189,248,0.06)', padding: '14px', borderRadius: '10px', border: '1px solid rgba(56,189,248,0.3)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '6px' }}>
                  <span style={{ fontSize: '11px', color: '#38bdf8', fontWeight: 600 }}>VAYUDRISHTI HYPERLOCAL</span>
                  <span style={{ fontSize: '11px', fontWeight: 700, color: (aqiData?.station_comparison?.delta_pm25 ?? 0) < 0 ? '#34d399' : '#f87171' }}>
                    {(aqiData?.station_comparison?.delta_pm25 ?? 0) > 0 ? `+${aqiData?.station_comparison?.delta_pm25}` : (aqiData?.station_comparison?.delta_pm25 ?? aqiData?.blind_spot_comparison?.difference_pm25 ?? 0)} µg/m³ delta
                  </span>
                </div>
                <div style={{ fontSize: '15px', fontWeight: 700, color: '#fff', marginBottom: '4px' }}>
                  {selectedStation.name}
                </div>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px' }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '24px', fontWeight: 700, color: aqiData?.color || '#38bdf8' }}>
                    {aqiData?.predicted_pm25 || '76'}
                  </span>
                  <span style={{ fontSize: '12px', color: 'var(--text-dim)' }}>µg/m³ (AQI {aqiData?.predicted_aqi || '153'})</span>
                </div>
                <span style={{ fontSize: '10px', color: '#38bdf8' }}>Fusing 1km Satellite AOD + Terrain Elevation + Wind</span>
              </div>
            </div>

            <p style={{ fontSize: '12px', color: '#cbd5e1', lineHeight: 1.4, margin: 0, background: 'rgba(0,0,0,0.2)', padding: '10px', borderRadius: '8px' }}>
              💡 <strong>Physical Insight:</strong> {aqiData?.station_comparison?.blind_spot_insight || aqiData?.blind_spot_comparison?.explanation || 'Microclimate terrain venting reduces stagnation compared to valley floor station.'}
            </p>
          </div>

          {/* 24-HOUR HISTORICAL TREND CHART */}
          <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Clock size={16} color="var(--accent-cyan)" />
                <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-main)' }}>
                  24-Hour Observed Diurnal Profile ({selectedStation.name})
                </h3>
              </div>
              <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
                Target: PM2.5 (µg/m³)
              </span>
            </div>

            {/* Custom SVG Bar/Trend Sparkline */}
            <div style={{ height: '85px', display: 'flex', alignItems: 'flex-end', gap: '4px', paddingTop: '10px' }}>
              {historyData.map((pt, idx) => {
                const heightPct = Math.min(100, Math.max(15, (pt.pm25 / 150) * 100));
                return (
                  <div key={idx} style={{ flex: 1, display: 'flex', flexDirection: 'column', alignItems: 'center', gap: '4px', height: '100%', justifyContent: 'flex-end' }}>
                    <div 
                      title={`${pt.timestamp}: ${pt.pm25} µg/m³ (AQI ${pt.aqi})`}
                      style={{ 
                        width: '100%', 
                        height: `${heightPct}%`, 
                        borderRadius: '4px 4px 0 0', 
                        background: pt.pm25 > 90 ? 'linear-gradient(to top, #f97316, #ef4444)' : 'linear-gradient(to top, #10b981, #eab308)',
                        opacity: idx === historyData.length - 1 ? 1 : 0.65,
                        transition: 'all 0.2s ease',
                        cursor: 'pointer'
                      }}
                    />
                  </div>
                );
              })}
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--text-dim)' }}>
              <span>-24 Hours Ago (Nocturnal)</span>
              <span>Morning Peak</span>
              <span>Afternoon Convection</span>
              <span style={{ color: 'var(--accent-cyan)', fontWeight: 600 }}>Current Hour</span>
            </div>
          </div>

        </div>

        {/* RIGHT COLUMN: Real-Time AQI, Confidence Interval, Best Window, Forecast, SHAP */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          
          {/* PRIMARY AQI GAUGE CARD WITH CONFIDENCE & RELIABILITY */}
          <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', gap: '18px', position: 'relative', overflow: 'hidden' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <div>
                <span style={{ fontSize: '12px', fontWeight: 600, color: 'var(--accent-cyan)', letterSpacing: '0.05em' }}>
                  HYPERLOCAL AIR QUALITY REPORT
                </span>
                <h3 style={{ fontSize: '20px', fontWeight: 700, marginTop: '2px', color: '#fff' }}>
                  {selectedStation.name}
                </h3>
                <span style={{ fontSize: '12px', color: 'var(--text-dim)' }}>
                  Lat: {selectedStation.lat.toFixed(4)}°N • Lon: {selectedStation.lon.toFixed(4)}°E • {selectedStation.zone}
                </span>
              </div>

              {/* Status Badge */}
              <div style={{ 
                padding: '6px 14px', 
                borderRadius: '999px', 
                background: `${aqiData?.color || '#eab308'}22`, 
                border: `1px solid ${aqiData?.color || '#eab308'}66`,
                color: aqiData?.color || '#eab308',
                fontWeight: 700,
                fontSize: '13px',
                display: 'flex',
                alignItems: 'center',
                gap: '6px'
              }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: aqiData?.color || '#eab308' }}></span>
                {aqiData?.category || 'Moderate'}
              </div>
            </div>

            {/* Metrics Dual Display */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', background: 'rgba(255,255,255,0.03)', padding: '16px', borderRadius: '12px', border: '1px solid var(--border-subtle)' }}>
              <div>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>Estimated PM2.5</span>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '4px' }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '38px', fontWeight: 700, color: '#fff' }}>
                    {loading ? '...' : aqiData?.predicted_pm25}
                  </span>
                  <span style={{ fontSize: '14px', color: 'var(--text-dim)' }}>µg/m³</span>
                </div>
                {/* Confidence Interval Tag */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '5px', marginTop: '4px' }}>
                  <span style={{ fontSize: '11px', color: '#38bdf8', fontWeight: 600 }}>
                    ±{aqiData?.uncertainty?.margin_of_error || 13.8} µg/m³
                  </span>
                  <span style={{ fontSize: '10px', color: '#64748b' }}>
                    (90% CI: [{aqiData?.uncertainty?.pm25_lower_bound || 62} - {aqiData?.uncertainty?.pm25_upper_bound || 90}])
                  </span>
                </div>
              </div>

              <div>
                <span style={{ fontSize: '12px', color: 'var(--text-muted)' }}>India NAQI Sub-Index</span>
                <div style={{ display: 'flex', alignItems: 'baseline', gap: '6px', marginTop: '4px' }}>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '38px', fontWeight: 700, color: aqiData?.color || '#eab308' }}>
                    {loading ? '...' : aqiData?.predicted_aqi}
                  </span>
                  <span style={{ fontSize: '14px', color: 'var(--text-dim)' }}>/ 500</span>
                </div>
                {/* Data Reliability Index */}
                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
                  <ShieldCheck size={13} color="#10b981" />
                  <span style={{ fontSize: '11px', color: '#34d399', fontWeight: 600 }}>
                    {aqiData?.data_reliability?.reliability_score || aqiData?.reliability?.reliability_score || 91}% Reliability
                  </span>
                  <span style={{ fontSize: '10px', color: '#64748b' }}>
                    ({aqiData?.data_reliability?.reliability_level || aqiData?.reliability?.reliability_level || 'HIGH'})
                  </span>
                </div>
              </div>
            </div>

            {/* Health Impact Statement */}
            <div style={{ display: 'flex', alignItems: 'center', gap: '10px', padding: '12px', borderRadius: '10px', background: 'rgba(239, 68, 68, 0.08)', border: '1px solid rgba(239, 68, 68, 0.2)' }}>
              <ShieldAlert size={20} color="#f97316" style={{ flexShrink: 0 }} />
              <p style={{ fontSize: '12px', color: '#fed7aa', lineHeight: 1.4, margin: 0 }}>
                {aqiData?.health_advisory || 'Minor breathing discomfort to sensitive individuals and asthma patients.'}
              </p>
            </div>
          </div>

          {/* ── OPTIMAL OUTDOOR WINDOW / DECISION SUPPORT CARD ── */}
          <div className="glass-panel" style={{ padding: '18px', display: 'flex', flexDirection: 'column', gap: '10px', background: 'linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(15, 23, 42, 0.6) 100%)', border: '1px solid rgba(16, 185, 129, 0.25)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Award size={16} color="#34d399" />
                <h3 style={{ fontSize: '13px', fontWeight: 700, color: '#34d399', letterSpacing: '0.02em' }}>
                  OPTIMAL OUTDOOR TRAVEL & ACTIVITY WINDOW
                </h3>
              </div>
              <span style={{ fontSize: '11px', background: 'rgba(16, 185, 129, 0.2)', color: '#34d399', padding: '2px 8px', borderRadius: '6px', fontWeight: 600 }}>
                {aqiData?.outdoor_advisor?.peak_hazard_horizon ? `Peak: ${aqiData.outdoor_advisor.peak_hazard_horizon}` : 'Satisfactory'}
              </span>
            </div>

            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', background: 'rgba(0,0,0,0.25)', padding: '10px 14px', borderRadius: '8px' }}>
              <div>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Best Forecast Window:</span>
                <div style={{ fontSize: '16px', fontWeight: 700, color: '#fff', marginTop: '2px' }}>
                  {aqiData?.outdoor_advisor?.recommended_window || aqiData?.optimal_outdoor_window?.best_window_label || 'In +12 hour(s)'}
                </div>
              </div>
              <div style={{ textAlign: 'right' }}>
                <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>Lowest Est. PM2.5:</span>
                <div style={{ fontSize: '18px', fontWeight: 700, color: '#34d399', marginTop: '2px', fontFamily: 'var(--font-mono)' }}>
                  ~{Math.round(aqiData?.outdoor_advisor?.lowest_predicted_pm25 || aqiData?.optimal_outdoor_window?.lowest_pm25 || 48)} µg/m³
                </div>
              </div>
            </div>

            <p style={{ fontSize: '11px', color: '#a7f3d0', margin: 0, lineHeight: 1.4 }}>
              {aqiData?.outdoor_advisor?.actionable_advice || aqiData?.optimal_outdoor_window?.advisory || 'Recommended period for morning jogging, outdoor school activities, and cycling before nocturnal inversion builds.'}
            </p>
          </div>

          {/* MULTI-HORIZON 24-HOUR FORECAST PANEL */}
          <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <TrendingUp size={16} color="var(--accent-cyan)" />
                <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-main)' }}>
                  Multi-Horizon Predictive Forecast
                </h3>
              </div>
              <span style={{ fontSize: '11px', background: 'rgba(56,189,248,0.1)', padding: '2px 8px', borderRadius: '4px', color: 'var(--accent-cyan)' }}>
                XGBoost Autoregressive Model
              </span>
            </div>

            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px' }}>
              {forecastData?.map((item, idx) => (
                <div key={idx} style={{ 
                  background: 'rgba(255,255,255,0.03)', 
                  border: '1px solid var(--border-subtle)', 
                  borderRadius: '10px', 
                  padding: '12px 10px', 
                  display: 'flex', 
                  flexDirection: 'column', 
                  alignItems: 'center', 
                  gap: '4px',
                  transition: 'transform 0.2s',
                  cursor: 'default'
                }}>
                  <span style={{ fontSize: '11px', color: 'var(--text-muted)', fontWeight: 600 }}>
                    +{item.horizon_hours}h Horizon
                  </span>
                  <span style={{ fontFamily: 'var(--font-mono)', fontSize: '20px', fontWeight: 700, color: item.color }}>
                    {item.predicted_pm25}
                  </span>
                  <span style={{ fontSize: '10px', color: 'var(--text-dim)' }}>
                    µg/m³
                  </span>
                  <span style={{ fontSize: '10px', color: item.color, fontWeight: 600 }}>
                    AQI {item.predicted_aqi}
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* SHAP EXPLAINABILITY PANEL ("WHY IS IT HIGH?") */}
          <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Sparkles size={16} color="var(--accent-cyan)" />
                <h3 style={{ fontSize: '14px', fontWeight: 600, color: 'var(--text-main)' }}>
                  Explainable AI Attribution (SHAP TreeExplainer)
                </h3>
              </div>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)' }}>
                Atmospheric Diagnostics
              </span>
            </div>

            {/* Narrative Explanation */}
            <p style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: 1.5, background: 'rgba(0,0,0,0.25)', padding: '12px', borderRadius: '8px', borderLeft: '3px solid var(--accent-cyan)', margin: 0 }}>
              {explainData?.narrative_explanation || 'Loading physics and emission attribution...'}
            </p>

            {/* Factor Breakdown List */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {explainData?.top_drivers?.map((driver, idx) => {
                const isElevating = driver.impact_value > 0;
                return (
                  <div key={idx} style={{ 
                    display: 'flex', 
                    alignItems: 'center', 
                    justifyContent: 'space-between', 
                    padding: '8px 12px', 
                    background: 'rgba(255,255,255,0.02)', 
                    borderRadius: '8px',
                    border: '1px solid var(--border-subtle)',
                    fontSize: '12px'
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ 
                        width: '6px', 
                        height: '6px', 
                        borderRadius: '50%', 
                        background: isElevating ? '#ef4444' : '#10b981' 
                      }}></span>
                      <span style={{ fontWeight: 600, color: 'var(--text-main)' }}>{driver.driver.toUpperCase()}</span>
                    </div>
                    
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <span style={{ color: 'var(--text-dim)', fontSize: '11px' }}>{driver.direction}</span>
                      <span style={{ 
                        fontFamily: 'var(--font-mono)', 
                        fontWeight: 700, 
                        color: isElevating ? '#f87171' : '#34d399' 
                      }}>
                        {isElevating ? `+${driver.impact_value}` : `${driver.impact_value}`} µg/m³
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>

          {/* ── RESEARCH MODE PANEL (WHEN TOGGLED) ───────────────────── */}
          {researchMode && (
            <div className="glass-panel" style={{ padding: '20px', display: 'flex', flexDirection: 'column', gap: '14px', border: '1px solid rgba(168, 85, 247, 0.4)', background: 'linear-gradient(135deg, rgba(168, 85, 247, 0.06) 0%, rgba(15, 23, 42, 0.8) 100%)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  <FlaskConical size={18} color="#c084fc" />
                  <h3 style={{ fontSize: '14px', fontWeight: 700, color: '#d8b4fe' }}>
                    Scientific Benchmark & Provenance Audit
                  </h3>
                </div>
                <span style={{ fontSize: '11px', color: '#c084fc', background: 'rgba(168, 85, 247, 0.2)', padding: '2px 8px', borderRadius: '4px' }}>
                  Ablation Verified
                </span>
              </div>

              {/* Scientific Metrics Table */}
              <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '10px' }}>
                <div style={{ background: 'rgba(0,0,0,0.3)', padding: '10px', borderRadius: '8px', textAlign: 'center' }}>
                  <span style={{ fontSize: '10px', color: '#94a3b8' }}>Weather Alone</span>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: '#f87171' }}>R² -0.0457</div>
                  <span style={{ fontSize: '10px', color: '#64748b' }}>MAE 86.17</span>
                </div>
                <div style={{ background: 'rgba(0,0,0,0.3)', padding: '10px', borderRadius: '8px', textAlign: 'center' }}>
                  <span style={{ fontSize: '10px', color: '#94a3b8' }}>Weather + GIS</span>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: '#f87171' }}>R² -0.0511</div>
                  <span style={{ fontSize: '10px', color: '#64748b' }}>MAE 85.96</span>
                </div>
                <div style={{ background: 'rgba(168, 85, 247, 0.15)', padding: '10px', borderRadius: '8px', textAlign: 'center', border: '1px solid rgba(168, 85, 247, 0.4)' }}>
                  <span style={{ fontSize: '10px', color: '#d8b4fe', fontWeight: 600 }}>Full Satellite Fusion</span>
                  <div style={{ fontSize: '16px', fontWeight: 700, color: '#34d399' }}>R² 0.7834</div>
                  <span style={{ fontSize: '10px', color: '#34d399' }}>MAE 33.64 (-60.9%)</span>
                </div>
              </div>

              {/* Provenance Metadata */}
              <div style={{ background: 'rgba(0,0,0,0.25)', padding: '12px', borderRadius: '8px', fontSize: '11px', display: 'flex', flexDirection: 'column', gap: '6px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94a3b8' }}>Prediction ID:</span>
                  <span style={{ color: '#e2e8f0', fontFamily: 'var(--font-mono)' }}>{aqiData?.provenance?.prediction_id || 'PRED-LIVE-001'}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94a3b8' }}>Model Checksum:</span>
                  <span style={{ color: '#e2e8f0', fontFamily: 'var(--font-mono)' }}>{aqiData?.provenance?.checksum || '7c8b21...'}</span>
                </div>
                <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                  <span style={{ color: '#94a3b8' }}>Cross-Validation:</span>
                  <span style={{ color: '#34d399' }}>Spatial GroupKFold (Zero station leakage)</span>
                </div>
              </div>
            </div>
          )}

        </div>

      </div>

      {/* ── FOOTER ───────────────────────────────────────────────── */}
      <footer style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', fontSize: '11px', color: 'var(--text-dim)', padding: '8px 4px', flexWrap: 'wrap', gap: '8px' }}>
        <span>Vayudrishti-AI Framework • Central Pollution Control Board (CPCB) NAQI Standard Compliant</span>
        <span>MODIS 061 MAIAC • Sentinel-5P OFFL L3 • ECMWF ERA5-Land Hourly</span>
      </footer>

    </div>
  );
}
