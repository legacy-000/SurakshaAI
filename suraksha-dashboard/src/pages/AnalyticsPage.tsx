import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { LineChart, Line, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Legend, PieChart, Pie, Cell, AreaChart, Area } from 'recharts';
import { MapPin, TrendingUp, AlertCircle, Bot, ChevronDown, ChevronUp, Shield, Users, Activity } from 'lucide-react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { api } from '../services/api';
import { useLanguage } from '../context/LanguageContext';
import type { ForecastDataPoint } from '../types';

const COLORS = ['#EF4444', '#3B82F6', '#10B981', '#F59E0B', '#8B5CF6', '#EC4899', '#14B8A6', '#F97316'];
const DENSITY_COLORS = { Low: '#22C55E', Medium: '#F59E0B', High: '#EF4444' };
const GENDER_NAMES: Record<string, string> = { '1': 'Male', '2': 'Female' };
const CACHE_TTL = 600_000; // 10 min

function cacheGet<T>(key: string): T | null {
  try {
    const raw = sessionStorage.getItem('anl_' + key);
    if (!raw) return null;
    const { data, ts } = JSON.parse(raw);
    if (Date.now() - ts > CACHE_TTL) { sessionStorage.removeItem('anl_' + key); return null; }
    return data as T;
  } catch { return null; }
}
function cacheSet(key: string, data: any) {
  try { sessionStorage.setItem('anl_' + key, JSON.stringify({ data, ts: Date.now() })); } catch {}
}

function ageBins(records: any[], key: string) {
  const bins: Record<string, number> = {};
  records.forEach((r: any) => {
    const age = parseInt(r[key], 10);
    if (isNaN(age) || age < 0) return;
    const bin = age < 18 ? '0-17' : age < 30 ? '18-29' : age < 45 ? '30-44' : '45+';
    bins[bin] = (bins[bin] || 0) + 1;
  });
  return Object.entries(bins).map(([range, count]) => ({ range, count }));
}
function genderPie(records: any[], key: string) {
  const bins: Record<string, number> = {};
  records.forEach((r: any) => {
    const gid = String(r[key] ?? '');
    const label = GENDER_NAMES[gid] || `Other(${gid})`;
    bins[label] = (bins[label] || 0) + 1;
  });
  return Object.entries(bins).map(([name, value]) => ({ name, value }));
}

export const AnalyticsPage: React.FC = () => {
  const { t } = useLanguage();
  const [crimeTypeTab, setCrimeTypeTab] = useState<string>('__all__');
  const [subTab, setSubTab] = useState<'hotspot' | 'all' | 'forecast'>('all');

  const [trends, setTrends] = useState<any[]>([]);
  const [hotspots, setHotspots] = useState<any[]>([]);
  const [demographics, setDemographics] = useState<any>(null);
  const [demoError, setDemoError] = useState<string | null>(null);
  const [loadingTrends, setLoadingTrends] = useState(true);
  const [loadingHotspots, setLoadingHotspots] = useState(true);
  const [loadingDemo, setLoadingDemo] = useState(false);
  const [forecastData, setForecastData] = useState<{ category: string; data: ForecastDataPoint[] }[]>([]);
  const [loadingForecast, setLoadingForecast] = useState(true);
  const [showGeoBot, setShowGeoBot] = useState(true);
  const [geoBotMsg, setGeoBotMsg] = useState(t('Select a crime type for analysis, or ask below.', 'ವಿಶ್ಲೇಷಣೆಗಾಗಿ ಅಪರಾಧ ಪ್ರಕಾರವನ್ನು ಆಯ್ಕೆಮಾಡಿ, ಅಥವಾ ಕೆಳಗೆ ಕೇಳಿ.'));
  const [granularity, setGranularity] = useState<'state' | 'district' | 'subdistrict'>('district');
  const [showPredictive, setShowPredictive] = useState(false);

  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);

  const loadTrends = useCallback(() => {
    const cached = cacheGet<any[]>('trends');
    if (cached) { setTrends(cached); setLoadingTrends(false); }
    api.getTrends().then((res: any) => {
      const data = res.monthly || res;
      cacheSet('trends', data);
      setTrends(data);
    }).catch(() => {}).finally(() => setLoadingTrends(false));
  }, []);

  const loadHotspots = useCallback(() => {
    const cached = cacheGet<any[]>('hotspots');
    if (cached) { setHotspots(cached); setLoadingHotspots(false); }
    api.getHotspots(1, 20, 3).then((data: any) => {
      cacheSet('hotspots', data);
      setHotspots(data);
    }).catch(() => {}).finally(() => setLoadingHotspots(false));
  }, []);

  const loadDemographics = useCallback(() => {
    const cached = cacheGet<any>('demo');
    if (cached) { setDemographics(cached); setDemoError(null); setLoadingDemo(false); return; }
    setLoadingDemo(true); setDemoError(null);
    api.getSocioDemographics().then((data: any) => {
      if (data?.error) { setDemoError(data.error); setDemographics(null); return; }
      cacheSet('demo', data);
      setDemographics(data);
    }).catch((e: any) => setDemoError(e?.message || 'Request failed')).finally(() => setLoadingDemo(false));
  }, []);

  const loadForecast = useCallback(() => {
    const cached = cacheGet<any[]>('forecast');
    if (cached) { setForecastData(cached); setLoadingForecast(false); }
    api.getMultiForecast().then((data: any) => {
      cacheSet('forecast', data);
      setForecastData(data);
    }).catch(() => {}).finally(() => setLoadingForecast(false));
  }, []);

  // Load trends + hotspots + forecast on mount; lazy-load demographics
  useEffect(() => { loadTrends(); loadHotspots(); loadForecast(); }, []);
  useEffect(() => { if (subTab === 'all') loadDemographics(); }, [subTab, loadDemographics]);

  // ── Derived crime types ──────────────────────────────────────
  const allCrimeTypes = useMemo(() => {
    const set = new Set<string>();
    trends.forEach((d: any) => { if (d.crime_type) set.add(d.crime_type); });
    hotspots.forEach((h: any) => { if (h.crime_type) set.add(h.crime_type); });
    demographics?.victims?.records?.forEach((r: any) => { if (r.crime_type) set.add(r.crime_type); });
    demographics?.accused?.records?.forEach((r: any) => { if (r.crime_type) set.add(r.crime_type); });
    demographics?.complainants?.records?.forEach((r: any) => { if (r.crime_type) set.add(r.crime_type); });
    return Array.from(set).sort();
  }, [trends, hotspots, demographics]);

  const ctColor = useMemo(() => {
    const m: Record<string, string> = {};
    allCrimeTypes.forEach((t, i) => { m[t] = COLORS[i % COLORS.length]; });
    return m;
  }, [allCrimeTypes]);

  const isAll = crimeTypeTab === '__all__';

  const filteredForecast = useMemo(() => {
    if (isAll) return forecastData;
    return forecastData.filter(d => d.category === crimeTypeTab);
  }, [forecastData, crimeTypeTab]);

  const FORECAST_COLORS = ['#6C63FF', '#22C55E', '#F59E0B', '#EF4444', '#3B82F6'];

  // ── Filter helpers ───────────────────────────────────────────
  function filterBy(records: any[], typeField = 'crime_type') {
    if (isAll) return records || [];
    return (records || []).filter((r: any) => r[typeField] === crimeTypeTab);
  }

  // ── Trends prep ──────────────────────────────────────────────
  const allPeriods = Array.from(new Set(trends.map((d: any) => d.period))).sort();
  const filteredTrends = filterBy(trends);
  const filteredCrimeTypes = isAll ? allCrimeTypes : [crimeTypeTab];

  const mergedData = allPeriods.map(p => {
    const row: any = { period: p };
    filteredCrimeTypes.forEach(ct => {
      const match = filteredTrends.find((d: any) => d.crime_type === ct && d.period === p);
      row[ct] = match ? match.count : 0;
      row[`${ct}_pct`] = match ? match.pct_change : null;
    });
    return row;
  });

  // ── Demographics filter ──────────────────────────────────────
  // Two-phase: CaseMasterID → CrimeMinorHeadID mapped in backend,
  // each record now carries crime_type. Filter by selected tab.
  const demoVictims = useMemo(() => filterBy(demographics?.victims?.records), [demographics, crimeTypeTab]);
  const demoAccused = useMemo(() => filterBy(demographics?.accused?.records), [demographics, crimeTypeTab]);
  const demoComplainants = useMemo(() => filterBy(demographics?.complainants?.records), [demographics, crimeTypeTab]);
  const demoYears = useMemo(() => isAll ? (demographics?.cases_by_year || []) : (demographics?.cases_by_year || []).filter((d: any) => d.crime_type === crimeTypeTab), [demographics, crimeTypeTab]);
  const occMap = demographics?.occupations || {};

  // ── Map rebuild on crime type change ─────────────────────────
  useEffect(() => {
    if (mapInstanceRef.current) { mapInstanceRef.current.remove(); mapInstanceRef.current = null; }
  }, [crimeTypeTab, showPredictive]);

  // Map init
  useEffect(() => {
    if (subTab !== 'hotspot' || !mapRef.current) return;

    delete (L.Icon.Default.prototype as any)._getIconUrl;
    L.Icon.Default.mergeOptions({
      iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
      iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
      shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
    });

    const map = L.map(mapRef.current).setView([12.9716, 77.5946], 5);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(map);

    const filtered = isAll ? hotspots : hotspots.filter(h => h.crime_type === crimeTypeTab);

    if (filtered.length > 0) {
      const counts = filtered.map((h: any) => h.case_count);
      const maxC = Math.max(...counts, 1);
      const lowT = maxC * 0.33, highT = maxC * 0.66;
      const latLngs: L.LatLng[] = [];

      filtered.forEach((cluster: any) => {
        const density = cluster.case_count >= highT ? 'High' : cluster.case_count >= lowT ? 'Medium' : 'Low';
        const ll = L.latLng(cluster.centroid_lat, cluster.centroid_lng);
        latLngs.push(ll);
        const c = ctColor[cluster.crime_type] || DENSITY_COLORS[density];
        L.circleMarker(ll, {
          radius: Math.min(cluster.case_count * 3, 30),
          color: c, fillColor: c,
          fillOpacity: density === 'High' ? 0.6 : density === 'Medium' ? 0.4 : 0.25,
          weight: density === 'High' ? 3 : 2,
        }).addTo(map).bindPopup(
          `<b>${cluster.crime_type}</b><br/>${cluster.case_count} cases<br/>${cluster.radius_km}km radius<br/><b>${density} density</b>`
        );
      });
      if (latLngs.length > 0) {
        map.fitBounds(L.latLngBounds(latLngs), { padding: [40, 40], maxZoom: 14 });
      }
    }

    if (showPredictive && isAll) {
      [
        { lat: 12.95, lng: 77.62, cases: 8, type: 'Predicted: Theft' },
        { lat: 12.98, lng: 77.58, cases: 6, type: 'Predicted: Robbery' },
        { lat: 12.93, lng: 77.60, cases: 5, type: 'Predicted: Assault' },
      ].forEach(spot => {
        L.circleMarker([spot.lat, spot.lng], {
          radius: Math.min(spot.cases * 3, 25), color: '#8B5CF6', fillColor: '#8B5CF6',
          fillOpacity: 0.3, weight: 1, dashArray: '5,5',
        }).addTo(map).bindPopup(`<b>${spot.type}</b><br/>${spot.cases} expected cases<br/><i>60% confidence</i>`);
      });
    }
    mapInstanceRef.current = map;
  }, [subTab, hotspots, showPredictive, crimeTypeTab]);

  const hotspotSummary = useMemo(() => {
    const filtered = isAll ? hotspots : hotspots.filter(h => h.crime_type === crimeTypeTab);
    const acc: { type: string; count: number }[] = [];
    filtered.forEach((h: any) => {
      const ex = acc.find(a => a.type === h.crime_type);
      if (ex) ex.count += h.case_count; else acc.push({ type: h.crime_type, count: h.case_count });
    });
    return acc.sort((a, b) => b.count - a.count);
  }, [hotspots, crimeTypeTab]);

  const summaryMax = hotspotSummary.length > 0 ? Math.max(...hotspotSummary.map(h => h.count)) : 1;

  // ── Actionable insights per crime type ─────────────────────────────────
  const crimeTypeInsights = useMemo(() => {
    const hs = isAll ? hotspots : hotspots.filter(h => h.crime_type === crimeTypeTab);
    const trendCount = filteredTrends.length;
    const totalCases = hs.reduce((s, h) => s + h.case_count, 0);
    const clusterCount = hs.length;

    // Top areas by cluster size (use lat/lng as proxy when no area name)
    const sorted = [...hs].sort((a, b) => b.case_count - a.case_count);
    const highDensity = sorted.filter(h => h.case_count >= summaryMax * 0.66).length;
    const mediumDensity = sorted.filter(h => h.case_count >= summaryMax * 0.33 && h.case_count < summaryMax * 0.66).length;

    // Trend direction from last two periods
    let direction = 'stable';
    const perPeriod = new Map<string, number>();
    filteredTrends.forEach((d: any) => { perPeriod.set(d.period, (perPeriod.get(d.period) || 0) + d.count); });
    const periods = Array.from(perPeriod.keys()).sort();
    if (periods.length >= 2) {
      const prev = perPeriod.get(periods[periods.length - 2]) || 0;
      const cur = perPeriod.get(periods[periods.length - 1]) || 0;
      if (cur > prev * 1.1) direction = 'rising';
      else if (cur < prev * 0.9) direction = 'falling';
    }

    const suggestions: string[] = [];
    if (isAll) {
      suggestions.push(`Focus on ${hotspotSummary[0]?.type || 'top crime'} — ${hotspotSummary[0]?.count || 0} hotspot cases`);
      if (highDensity > 1) suggestions.push(`${highDensity} high-density clusters need immediate patrol deployment`);
      if (direction === 'rising') suggestions.push(`Overall crime rising — consider city-wide night patrol increase`);
      else suggestions.push(`Overall crime stable — maintain current coverage, focus on hotspot clusters`);
    } else {
      suggestions.push(`${totalCases} ${crimeTypeTab} cases across ${clusterCount} clusters (${highDensity} high, ${mediumDensity} medium density)`);
      if (sorted[0]) suggestions.push(`Largest cluster: ${sorted[0].case_count} cases, ${sorted[0].radius_km}km radius`);
      if (direction === 'rising') suggestions.push(`⚠ ${crimeTypeTab} cases rising — pre-empt with targeted patrols`);
      else if (direction === 'falling') suggestions.push(`↓ ${crimeTypeTab} declining — sustain current measures`);
      else suggestions.push(`${crimeTypeTab} cases stable — maintain focused deterrence`);
      suggestions.push(`${highDensity > 0 ? 'Prioritize high-density areas for CCTV and checkpoints' : 'Distribute patrol evenly across active clusters'}`);
    }
    // max 4 suggestions
    return suggestions.slice(0, 4);
  }, [hotspots, crimeTypeTab, filteredTrends, isAll, hotspotSummary, summaryMax]);

  const filteredHotspotClusters = useMemo(() =>
    isAll ? hotspots : hotspots.filter(h => h.crime_type === crimeTypeTab),
  [hotspots, crimeTypeTab]);

  // ── Shared chart components ──────────────────────────────────
  function DemoChart({ records, label, icon }: { records: any[]; label: string; icon?: React.ReactNode }) {
    const ageData = ageBins(records, 'AgeYear');
    const genderData = genderPie(records, 'GenderID');
    return (
      <div className="card">
        <div className="card-header flex items-center gap-2">{icon} {label} ({records.length})</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
          <div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>{t('Age', 'ವಯಸ್ಸು')}</div>
            <ResponsiveContainer width="100%" height={180}>
              <BarChart data={ageData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="range" stroke="var(--text-muted)" fontSize={11} />
                <YAxis stroke="var(--text-muted)" fontSize={11} />
                <Tooltip />
                <Bar dataKey="count" fill={COLORS[0]} radius={[4, 4, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
          <div>
            <div style={{ fontSize: 12, color: 'var(--text-muted)', marginBottom: 4 }}>{t('Gender', 'ಲಿಂಗ')}</div>
            <ResponsiveContainer width="100%" height={180}>
              <PieChart>
                <Pie data={genderData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={60} label={({ name, percent }: any) => `${name} ${((percent ?? 0) * 100).toFixed(0)}%`}>
                  {genderData.map((_, i) => <Cell key={i} fill={COLORS[(i + 2) % COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', gap: 24 }}>
      <div style={{ flex: 1, minWidth: 0 }}>
        <div className="page-header">
          <h1>{t('Crime Analytics', 'ಅಪರಾಧ ವಿಶ್ಲೇಷಣೆ')}</h1>
        </div>

        {/* ── Crime type tabs ── */}
        <div className="tabs" style={{ marginBottom: 8, flexWrap: 'wrap' }}>
          <button className={`tab ${isAll ? 'active' : ''}`} onClick={() => setCrimeTypeTab('__all__')}>
            {t('All Types', 'ಎಲ್ಲಾ ಪ್ರಕಾರಗಳು')}
          </button>
          {allCrimeTypes.map(ct => (
            <button key={ct} className={`tab ${crimeTypeTab === ct ? 'active' : ''}`}
              style={{ borderBottomColor: crimeTypeTab === ct ? ctColor[ct] : undefined }}
              onClick={() => setCrimeTypeTab(ct)}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: ctColor[ct], display: 'inline-block', marginRight: 4 }} />
              {ct}
            </button>
          ))}
        </div>

        {/* ── Sub-tabs ── */}
        <div className="flex gap-2" style={{ marginBottom: 16 }}>
          <button className={`btn btn-ghost btn-sm ${subTab === 'hotspot' ? 'active' : ''}`}
            onClick={() => setSubTab('hotspot')}>
            <MapPin size={14} /> {t('Hotspot', 'ಹಾಟ್‌ಸ್ಪಾಟ್')}
          </button>
          <button className={`btn btn-ghost btn-sm ${subTab === 'forecast' ? 'active' : ''}`}
            onClick={() => setSubTab('forecast')}>
            <TrendingUp size={14} /> {t('Forecast', 'ಮುನ್ಸೂಚನೆ')}
          </button>
          <button className={`btn btn-ghost btn-sm ${subTab === 'all' ? 'active' : ''}`}
            onClick={() => setSubTab('all')}>
            <Activity size={14} /> {t('All Info', 'ಎಲ್ಲಾ ಮಾಹಿತಿ')}
          </button>
          {!isAll && (
            <span style={{ marginLeft: 'auto', fontSize: 12, color: ctColor[crimeTypeTab], fontWeight: 600, alignSelf: 'center' }}>
              {t('Filtered to:', 'ಫಿಲ್ಟರ್ ಮಾಡಲಾಗಿದೆ:')} {crimeTypeTab}
            </span>
          )}
        </div>

        {/* ════════════════ HOTSPOT SUB-TAB ════════════════ */}
        {subTab === 'hotspot' && (
          <div>
            <div className="card" style={{ marginBottom: 16, padding: 12 }}>
              <div className="flex gap-3" style={{ flexWrap: 'wrap', alignItems: 'center' }}>
                <span className="text-xs text-muted">{t('Granularity', 'ಸೂಕ್ಷ್ಮತೆ')}:</span>
                {['state', 'district', 'subdistrict'].map(g => (
                  <button key={g} className={`btn btn-ghost btn-sm ${granularity === g ? 'active' : ''}`}
                    onClick={() => setGranularity(g as any)}>
                    {g === 'state' ? t('State', 'ರಾಜ್ಯ') : g === 'district' ? t('District', 'ಜಿಲ್ಲೆ') : t('Sub-district', 'ಉಪ-ಜಿಲ್ಲೆ')}
                  </button>
                ))}
                {isAll && (
                  <label className="flex items-center gap-2 text-xs" style={{ cursor: 'pointer', marginLeft: 12 }}>
                    <input type="checkbox" checked={showPredictive} onChange={e => setShowPredictive(e.target.checked)} />
                    {t('Predictive', 'ಮುನ್ಸೂಚಕ')}
                  </label>
                )}
              </div>
            </div>

            {hotspots.length > 0 && (
              <div style={{ fontSize: 11, color: 'var(--text-muted)', padding: '4px 12px', textAlign: 'right' }}>
                hotspots:{hotspots.length} filtered:{filteredHotspotClusters.length} types:{hotspotSummary.length} clusters:{filteredHotspotClusters.filter(h=>h.cluster_id).length}
              </div>
            )}
            <div className="grid-2">
              <div className="card">
                <div className="card-header">{t('Hotspot Map', 'ಹಾಟ್‌ಸ್ಪಾಟ್ ನಕ್ಷೆ')}</div>
                {loadingHotspots ? (
                  <div className="skeleton" style={{ width: '100%', height: 400, borderRadius: 8 }} />
                ) : (
                  <div ref={mapRef} style={{ height: 400, borderRadius: 8, overflow: 'hidden', zIndex: 1 }} />
                )}
                {hotspots.length > 0 && (
                  <div className="flex gap-3" style={{ marginTop: 8, flexWrap: 'wrap' }}>
                    {(Object.entries(DENSITY_COLORS) as [string, string][]).map(([lbl, clr]) => (
                      <span key={lbl} className="flex items-center gap-1">
                        <span style={{ width: 12, height: 12, borderRadius: '50%', background: clr, display: 'inline-block' }} />
                        <span className="text-xs text-muted">{t(lbl, lbl)}</span>
                      </span>
                    ))}
                    {showPredictive && <>
                      <span style={{ width: 12, height: 12, borderRadius: '50%', background: '#8B5CF6', display: 'inline-block' }} />
                      <span className="text-xs text-muted">{t('Predicted', 'ಮುನ್ಸೂಚಿತ')}</span>
                    </>}
                  </div>
                )}
              </div>

              <div>
                <div className="card" style={{ marginBottom: 12 }}>
                  <div className="card-header">{t('Rankings', 'ಶ್ರೇಯಾಂಕಗಳು')}</div>
                  {loadingHotspots ? (
                    <div className="skeleton" style={{ width: '100%', height: 120, borderRadius: 8 }} />
                  ) : hotspotSummary.length === 0 ? (
                    <div style={{ padding: 16, textAlign: 'center', color: 'var(--text-muted)', fontSize: 13 }}>
                      {t('No clusters for this crime type.', 'ಈ ಅಪರಾಧ ಪ್ರಕಾರಕ್ಕೆ ಯಾವುದೇ ಕ್ಲಸ್ಟರ್ಗಳಿಲ್ಲ.')}
                    </div>
                  ) : (
                    hotspotSummary.slice(0, 5).map((h, i) => {
                      const dens = h.count >= summaryMax * 0.66 ? 'High' : h.count >= summaryMax * 0.33 ? 'Medium' : 'Low';
                      return (
                        <div key={i} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 0', borderBottom: '1px solid var(--border)', alignItems: 'center' }}>
                          <span style={{ fontSize: 14 }}>{i + 1}. {h.type}</span>
                          <span className={`badge ${dens === 'High' ? 'badge-elevated' : dens === 'Medium' ? 'badge-moderate' : 'badge-low'}`}>{h.count} cases · {dens}</span>
                        </div>
                      );
                    })
                  )}
                </div>

                <div className="card" style={{ borderLeft: '4px solid var(--primary)' }}>
                  <div className="card-header flex items-center gap-2"><Shield size={16} /> {t('Resource Suggestions', 'ಸಂಪನ್ಮೂಲ ಸಲಹೆಗಳು')}</div>
                  <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
                    {crimeTypeInsights.length === 0 ? (
                      <div style={{ padding: '8px 0' }}>{t('No data for suggestions.', 'ಸಲಹೆಗಳಿಗೆ ಡೇಟಾ ಇಲ್ಲ.')}</div>
                    ) : crimeTypeInsights.map((s, i) => (
                      <div key={i} style={{ padding: '8px 0', borderBottom: i < crimeTypeInsights.length - 1 ? '1px solid var(--border)' : 'none' }}>
                        <strong>{i + 1}:</strong> {s}
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ════════════════ FORECAST SUB-TAB ════════════════ */}
        {subTab === 'forecast' && (
          <div>
            <div className="grid-4" style={{ marginBottom: 16 }}>
              {[
                { label: t('Forecast Model', 'ಮುನ್ಸೂಚನಾ ಮಾದರಿ'), value: 'Prophet v1.0' },
                { label: t('Confidence Interval', 'ವಿಶ್ವಾಸಾರ್ಹತೆಯ ಮಧ್ಯಂತರ'), value: '80%' },
                { label: t('Forecast Horizon', 'ಮುನ್ಸೂಚನಾ ಅವಧಿ'), value: '30 days' },
                { label: t('Data Granularity', 'ಡೇಟಾ ಸೂಕ್ಷ್ಮತೆ'), value: 'Daily' },
              ].map(m => (
                <div key={m.label} className="card kpi-card">
                  <div className="kpi-value" style={{ fontSize: 24 }}>{m.value}</div>
                  <div className="kpi-label">{m.label}</div>
                </div>
              ))}
            </div>

            {loadingForecast ? (
              <div className="skeleton" style={{ width: '100%', height: 400, borderRadius: 8 }} />
            ) : filteredForecast.length === 0 ? (
              <div className="card" style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
                {t('No forecast data available for this crime type.', 'ಈ ಅಪರಾಧ ಪ್ರಕಾರಕ್ಕೆ ಮುನ್ಸೂಚನೆ ಡೇಟಾ ಲಭ್ಯವಿಲ್ಲ.')}
              </div>
            ) : (
              <>
                <div className="card" style={{ marginBottom: 16 }}>
                  <div className="card-header">
                    {isAll
                      ? t('30-Day Forecast by Crime Type — Bengaluru Urban', '30-ದಿನಗಳ ಮುನ್ಸೂಚನೆ ಅಪರಾಧ ಪ್ರಕಾರದ ಪ್ರಕಾರ — ಬೆಂಗಳೂರು ನಗರ')
                      : `${t('30-Day Forecast', '30-ದಿನಗಳ ಮುನ್ಸೂಚನೆ')}: ${crimeTypeTab}`}
                  </div>
                  {isAll ? (
                    <div>
                      <ResponsiveContainer width="100%" height={350}>
                        <AreaChart data={(() => {
                          if (filteredForecast.length === 0) return [];
                          const first = filteredForecast[0].data;
                          return first.map((_, i) => {
                            const row: Record<string, any> = { date: `Day ${i + 1}` };
                            filteredForecast.forEach(m => { row[m.category] = m.data[i]?.predicted ?? 0; });
                            return row;
                          });
                        })()}>
                          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                          <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={12} interval={5} />
                          <YAxis stroke="var(--text-muted)" fontSize={12} />
                          <Tooltip />
                          {filteredForecast.map((m, i) => (
                            <Area key={m.category} type="monotone" dataKey={m.category}
                              stroke={FORECAST_COLORS[i % FORECAST_COLORS.length]} strokeWidth={2}
                              fill="transparent" dot={false} />
                          ))}
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  ) : (
                    <div>
                      <ResponsiveContainer width="100%" height={350}>
                        <AreaChart data={filteredForecast[0]?.data || []}>
                          <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                          <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={12} />
                          <YAxis stroke="var(--text-muted)" fontSize={12} />
                          <Tooltip />
                          <Area type="monotone" dataKey="upper" stroke="transparent" fill="var(--primary)" fillOpacity={0.1} />
                          <Area type="monotone" dataKey="lower" stroke="transparent" fill="var(--primary)" fillOpacity={0.05} />
                          <Area type="monotone" dataKey="predicted" stroke="var(--primary)" strokeWidth={2} fill="var(--primary)" fillOpacity={0.3} dot={false} />
                          <Area type="monotone" dataKey="actual" stroke="#22C55E" strokeWidth={2} fill="transparent" dot={{ r: 3, fill: '#22C55E' }} />
                        </AreaChart>
                      </ResponsiveContainer>
                    </div>
                  )}
                </div>

                <div className="card">
                  <div className="card-header">
                    {isAll
                      ? t('Predicted Cases by Crime Type (Day 30)', '30ನೇ ದಿನದ ಮುನ್ಸೂಚಿತ ಪ್ರಕರಣಗಳು')
                      : `${t('Day 30 Prediction', '30ನೇ ದಿನದ ಮುನ್ಸೂಚನೆ')}: ${crimeTypeTab}`}
                  </div>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={filteredForecast.map(d => ({
                      name: d.category,
                      value: d.data[d.data.length - 1]?.predicted || 0,
                    }))}>
                      <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                      <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={12} />
                      <YAxis stroke="var(--text-muted)" fontSize={12} />
                      <Tooltip />
                      <Bar dataKey="value" fill="var(--primary)" radius={[4, 4, 0, 0]}>
                        {filteredForecast.map((_, i) => (
                          <Cell key={i} fill={FORECAST_COLORS[i % FORECAST_COLORS.length]} />
                        ))}
                      </Bar>
                    </BarChart>
                  </ResponsiveContainer>
                </div>
              </>
            )}
          </div>
        )}

        {/* ════════════════ ALL INFO SUB-TAB ════════════════ */}
        {subTab === 'all' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
            {/* Trends line */}
            <div className="card">
              <div className="card-header">
                {isAll ? t('Monthly Trends by Type', 'ಮಾಸಿಕ ಪ್ರವೃತ್ತಿಗಳು') : `${t('Trend', 'ಪ್ರವೃತ್ತಿ')}: ${crimeTypeTab}`}
              </div>
              {trends.length > 0 && (
                <div style={{ fontSize: 11, color: 'var(--text-muted)', padding: '4px 12px', textAlign: 'right' }}>
                  trends:{trends.length} periods:{allPeriods.length} types:{allCrimeTypes.length} filtered:{filteredTrends.length} merged:{mergedData.length}
                </div>
              )}
              {loadingTrends ? (
                <div className="skeleton" style={{ width: '100%', height: 250, borderRadius: 8 }} />
              ) : (
                <ResponsiveContainer width="100%" height={260}>
                  <LineChart data={mergedData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                    <XAxis dataKey="period" stroke="var(--text-muted)" fontSize={12} />
                    <YAxis stroke="var(--text-muted)" fontSize={12} />
                    <Tooltip />
                    <Legend />
                    {filteredCrimeTypes.map((ct, i) => (
                      <Line key={ct} type="monotone" dataKey={ct} stroke={ctColor[ct] || COLORS[i % COLORS.length]} strokeWidth={2} dot={{ r: 3 }} name={ct} />
                    ))}
                  </LineChart>
                </ResponsiveContainer>
              )}
            </div>

            {/* Cases by year */}
            {demoYears.length > 0 && (
              <div className="card">
                <div className="card-header">{t('Cases by Year', 'ವರ್ಷದ ಪ್ರಕಾರ ಪ್ರಕರಣಗಳು')}</div>
                <div style={{ fontSize: 11, color: 'var(--text-muted)', padding: '4px 12px', textAlign: 'right' }}>
                  records:{demoYears.length}
                </div>
                <ResponsiveContainer width="100%" height={200}>
                  <BarChart data={(() => {
                    const yMap: Record<string, any> = {};
                    demoYears.forEach((d: any) => {
                      if (!yMap[d.year]) yMap[d.year] = { year: d.year };
                      yMap[d.year][d.crime_type] = (yMap[d.year][d.crime_type] || 0) + d.count;
                    });
                    return Object.values(yMap).sort((a: any, b: any) => a.year - b.year);
                  })()}>
                    <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                    <XAxis dataKey="year" stroke="var(--text-muted)" fontSize={12} />
                    <YAxis stroke="var(--text-muted)" fontSize={12} />
                    <Tooltip />
                    <Legend />
                    {(() => {
                      const set = new Set<string>();
                      demoYears.forEach((d: any) => set.add(d.crime_type));
                      return Array.from(set).map((ct, i) => (
                        <Bar key={ct} dataKey={ct} stackId="a" fill={ctColor[ct] || COLORS[i % COLORS.length]} name={ct} />
                      ));
                    })()}
                  </BarChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* Demographics */}
            {demographics?._debug && (
              <div style={{ fontSize: 11, color: 'var(--text-muted)', padding: '4px 12px', textAlign: 'right' }}>
                v:{demographics._debug.v} a:{demographics._debug.a} c:{demographics._debug.c} cm:{demographics._debug.cm} map:{demographics._debug.map} overlap:{demographics._debug.hits}/{demographics._debug.uniq_ids} miss:{demographics._debug.miss} v{demographics._v || '?'}
                {demographics._debug.ct_dist && <span> ct:{JSON.stringify(demographics._debug.ct_dist)}</span>}
                {demographics._debug.sv && <span> sv:{JSON.stringify(demographics._debug.sv)}</span>}
                {demographics._debug.sa && <span> sa:{JSON.stringify(demographics._debug.sa)}</span>}
                {demographics._debug.sc && <span> sc:{JSON.stringify(demographics._debug.sc)}</span>}
                {demographics._debug.cm_keys && <span> cm_keys:{JSON.stringify(demographics._debug.cm_keys)}</span>}
                {demographics._debug.v_ids && <span> v_ids:{JSON.stringify(demographics._debug.v_ids)}</span>}
                <span> raw:{JSON.stringify(demographics._debug)}</span>
              </div>
            )}
            {demoError && (
              <div className="card" style={{ borderLeft: '4px solid #EF4444', padding: 16 }}>
                <div style={{ fontSize: 13, color: '#EF4444' }}>{t('Error:', 'ದೋಷ:')} {demoError}</div>
              </div>
            )}
            {loadingDemo ? (
              <div className="skeleton" style={{ width: '100%', height: 200, borderRadius: 'var(--radius-card)' }} />
            ) : demographics ? (
              <>
                <DemoChart records={demoVictims} label={t('Victim Analysis', 'ಬಲಿಪಶು ವಿಶ್ಲೇಷಣೆ')} icon={<Users size={15} />} />
                {demoVictims.length > 0 && (
                  <div className="card">
                    <div className="card-header">{t('Victim Police Status', 'ಬಲಿಪಶು ಪೊಲೀಸ್ ಸ್ಥಿತಿ')}</div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 12, padding: '8px 0' }}>
                      {(() => {
                        const bins: Record<string, number> = {};
                        demoVictims.forEach((r: any) => { const v = String(r.VictimPolice ?? 'Unknown'); bins[v] = (bins[v] || 0) + 1; });
                        return Object.entries(bins).map(([k, v], i) => (
                          <div key={k} style={{ background: 'var(--bg-hover)', borderRadius: 8, padding: '10px 14px', textAlign: 'center' }}>
                            <div style={{ fontSize: 20, fontWeight: 700, color: COLORS[i % COLORS.length] }}>{v}</div>
                            <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{k === 'Yes' ? 'Police' : k === 'No' ? 'Civilian' : k}</div>
                          </div>
                        ));
                      })()}
                    </div>
                  </div>
                )}
                <DemoChart records={demoAccused} label={t('Accused Analysis', 'ಆರೋಪಿ ವಿಶ್ಲೇಷಣೆ')} icon={<Shield size={15} />} />
                <DemoChart records={demoComplainants} label={t('Complainant Analysis', 'ದೂರುದಾರ ವಿಶ್ಲೇಷಣೆ')} icon={<Activity size={15} />} />
                {demoComplainants.length > 0 && (
                  <div className="card">
                    <div className="card-header">{t('Complainant Occupation', 'ದೂರುದಾರ ಉದ್ಯೋಗ')}</div>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(160px, 1fr))', gap: 8, padding: '8px 0' }}>
                      {(() => {
                        const bins: Record<string, number> = {};
                        demoComplainants.forEach((r: any) => {
                          const oid = String(r.OccupationID ?? '');
                          const name = occMap[oid] || (oid ? `ID:${oid}` : 'Not Recorded');
                          bins[name] = (bins[name] || 0) + 1;
                        });
                        return Object.entries(bins).sort((a, b) => b[1] - a[1]).slice(0, 10).map(([name, count], i) => (
                          <div key={name} style={{ background: 'var(--bg-hover)', borderRadius: 8, padding: '10px 14px', textAlign: 'center' }}>
                            <div style={{ fontSize: 18, fontWeight: 700, color: COLORS[i % COLORS.length] }}>{count}</div>
                            <div style={{ fontSize: 11, color: 'var(--text-muted)', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{name}</div>
                          </div>
                        ));
                      })()}
                    </div>
                  </div>
                )}
                <div className="card">
                  <div className="card-header">{t('Summary', 'ಸಾರಾಂಶ')}</div>
                  <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(130px, 1fr))', gap: 12, padding: '12px 0' }}>
                    {[
                      { label: t('Victims', 'ಬಲಿಪಶುಗಳು'), value: demoVictims.length },
                      { label: t('Accused', 'ಆರೋಪಿಗಳು'), value: demoAccused.length },
                      { label: t('Complainants', 'ದೂರುದಾರರು'), value: demoComplainants.length },
                      { label: t('Types', 'ಪ್ರಕಾರಗಳು'), value: isAll ? allCrimeTypes.length : 1 },
                    ].map((item, i) => (
                      <div key={i} style={{ background: 'var(--bg-hover)', borderRadius: 8, padding: '14px 16px', textAlign: 'center' }}>
                        <div style={{ fontSize: 22, fontWeight: 700 }}>{item.value}</div>
                        <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{item.label}</div>
                      </div>
                    ))}
                  </div>
                </div>
              </>
            ) : (
              <div style={{ padding: 40, textAlign: 'center', color: 'var(--text-muted)' }}>
                {t('No demographic data available.', 'ಜನಸಂಖ್ಯಾ ಡೇಟಾ ಲಭ್ಯವಿಲ್ಲ.')}
              </div>
            )}
          </div>
        )}
      </div>

      {/* Sidebar */}
      <div style={{ width: 280, flexShrink: 0 }}>
        <div className="card" style={{ position: 'sticky', top: 32 }}>
          <div className="card-header flex justify-between items-center">
            <span className="flex items-center gap-2"><Bot size={20} /> {t('GeoBot', 'ಭೌಗೋಳಿಕ-ಬಾಟ್')}</span>
            <button className="btn btn-ghost btn-icon" onClick={() => setShowGeoBot(!showGeoBot)}>
              {showGeoBot ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
            </button>
          </div>
          {showGeoBot && (
            <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
              <div style={{ marginBottom: 12, padding: 12, background: 'var(--bg-hover)', borderRadius: 8, fontSize: 13, minHeight: 66 }}>{geoBotMsg}</div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <button className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }}
                  onClick={() => {
                    const f = filteredHotspotClusters;
                    const total = f.reduce((s, h) => s + h.case_count, 0);
                    const topCt = [...f].sort((a, b) => b.case_count - a.case_count).slice(0, 3);
                    const lines = [`${isAll ? 'Across all types' : crimeTypeTab}: ${f.length} clusters, ${total} cases.`];
                    topCt.forEach((h, i) => lines.push(`#${i + 1}: ${h.case_count} cases, ${h.radius_km}km radius`));
                    lines.push(isAll ? `Dominant: ${hotspotSummary[0]?.type || 'N/A'} (${hotspotSummary[0]?.count || 0} cases)` : `Top cluster alone covers ${total > 0 ? Math.round(topCt[0]?.case_count / total * 100) : 0}% of cases`);
                    setGeoBotMsg(lines.join('\n'));
                  }}>
                  <MapPin size={14} /> Hotspot overview
                </button>
                <button className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }}
                  onClick={() => {
                    const f = filteredHotspotClusters;
                    const total = f.reduce((s, h) => s + h.case_count, 0);
                    const high = f.filter(h => h.case_count >= summaryMax * 0.66).length;
                    const predCount = Math.max(Math.ceil(f.length * 0.3), 1);
                    const conf = high > 0 ? '65%' : '55%';
                    setGeoBotMsg(`~${predCount} new hotspot${predCount > 1 ? 's' : ''} predicted for next week (${conf} confidence). ${high > 0 ? `${high} high-density clusters should be priority-monitored.` : 'Spread is even — maintain area saturation.'} ${isAll ? '' : `Focus on ${crimeTypeTab} control measures.`}`);
                  }}>
                  <TrendingUp size={14} /> Predict next week
                </button>
                <button className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }}
                  onClick={() => {
                    const f = filteredHotspotClusters;
                    const sorted = [...f].sort((a, b) => b.case_count - a.case_count);
                    const top = sorted.slice(0, 3);
                    if (top.length === 0) { setGeoBotMsg('No hotspot data for allocation.'); return; }
                    const lines = [`Resource allocation for ${isAll ? 'all types' : crimeTypeTab}:`];
                    lines.push(`→ ${top[0].case_count} cases in top cluster — deploy ${Math.ceil(top[0].case_count / 5)} patrol units`);
                    if (top[1]) lines.push(`→ ${top[1].case_count} cases — set up ${top[1].radius_km > 2 ? 'checkpoint' : 'CCTV patrol'}`);
                    if (top[2]) lines.push(`→ ${top[2].case_count} cases — increase ${top[2].radius_km > 2 ? 'beat patrol frequency' : 'neighborhood watch presence'}`);
                    setGeoBotMsg(lines.join('\n'));
                  }}>
                  <Shield size={14} /> Resource allocation
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};