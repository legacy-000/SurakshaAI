import React, { useState } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { Search, Bot, ChevronRight, Sliders, MessageSquare, MapPin, X, ArrowUpDown } from 'lucide-react';

const mockResults = [
  { crime_no: '104430006202600001', complainant: 'Ravi Kumar', accused_count: 2, category: 'FIR', status: 'Under Investigation', head: 'Theft', location: 'Bengaluru South', date: '2026-03-15', snippet: 'Complainant reported theft of motorcycle from Whitefield area...', lat: 12.9716, lng: 77.5946 },
  { crime_no: '104430006202600015', complainant: 'Priya Sharma', accused_count: 1, category: 'FIR', status: 'Chargesheeted', head: 'Robbery', location: 'Mysuru', date: '2026-04-02', snippet: 'Armed robbery at a jewelry store on Main Road...', lat: 12.2958, lng: 76.6394 },
  { crime_no: '104430006202600042', complainant: 'Anil Kumar', accused_count: 3, category: 'FIR', status: 'Under Investigation', head: 'Assault', location: 'Hubballi', date: '2026-05-10', snippet: 'Grievous assault reported near bus stand...', lat: 15.3647, lng: 75.1240 },
  { crime_no: '104430006202500312', complainant: 'Sunil D', accused_count: 1, category: 'UDR', status: 'Closed', head: 'Cheating', location: 'Belagavi', date: '2025-11-20', snippet: 'Financial fraud involving property sale...', lat: 15.8497, lng: 74.4977 },
  { crime_no: '104430006202600088', complainant: 'Meena Rao', accused_count: 4, category: 'FIR', status: 'Under Investigation', head: 'Cyber Crime', location: 'Bengaluru Urban', date: '2026-06-01', snippet: 'Phishing attack on banking customers...', lat: 12.9344, lng: 77.6102 },
];

const crimeTypes = ['Theft', 'Robbery', 'Assault', 'Burglary', 'Cheating', 'Kidnapping', 'Murder', 'Cyber Crime'];
const statuses = ['Under Investigation', 'Chargesheeted', 'Closed', 'Pending'];
const stations = ['Bengaluru South', 'Bengaluru North', 'Mysuru', 'Hubballi', 'Mangaluru', 'Belagavi'];

type SortKey = 'date' | 'crime_no' | 'relevance';

export const SearchPage: React.FC = () => {
  const { t } = useLanguage();
  const [mode, setMode] = useState<'quick' | 'advanced' | 'nl'>('quick');
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<typeof mockResults>([]);
  const [searched, setSearched] = useState(false);
  const [selectedCase, setSelectedCase] = useState<typeof mockResults[0] | null>(null);
  const [sortKey, setSortKey] = useState<SortKey>('date');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [searchBotMsg, setSearchBotMsg] = useState(t('I am SearchBot. Describe what you need and I will find it.', 'ನಾನು ಹುಡುಕು-ಬಾಟ್. ನಿಮಗೆ ಬೇಕಾದುದನ್ನು ವಿವರಿಸಿ, ನಾನು ಅದನ್ನು ಹುಡುಕುತ್ತೇನೆ.'));

  const [filters, setFilters] = useState({
    date_from: '', date_to: '', crime_type: '', status: '', station: '', gravity: '',
    geo_lat: '', geo_lng: '', geo_radius_km: '',
  });

  const deg2rad = (d: number) => d * (Math.PI / 180);
  const haversineDist = (lat1: number, lng1: number, lat2: number, lng2: number) => {
    const R = 6371;
    const dLat = deg2rad(lat2 - lat1);
    const dLng = deg2rad(lng2 - lng1);
    const a = Math.sin(dLat / 2) ** 2 + Math.cos(deg2rad(lat1)) * Math.cos(deg2rad(lat2)) * Math.sin(dLng / 2) ** 2;
    return R * 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
  };

  const handleSearch = () => {
    setSearched(true);
    let filtered = [...mockResults];

    if (mode === 'quick' && query) {
      const q = query.toLowerCase();
      filtered = filtered.filter(r =>
        r.crime_no.toLowerCase().includes(q) ||
        r.complainant.toLowerCase().includes(q) ||
        r.location.toLowerCase().includes(q) ||
        r.head.toLowerCase().includes(q)
      );
    }

    if (mode === 'advanced') {
      if (filters.crime_type) filtered = filtered.filter(r => r.head === filters.crime_type);
      if (filters.status) filtered = filtered.filter(r => r.status === filters.status);
      if (filters.station) filtered = filtered.filter(r => r.location === filters.station);
      if (filters.date_from) filtered = filtered.filter(r => r.date >= filters.date_from);
      if (filters.date_to) filtered = filtered.filter(r => r.date <= filters.date_to);

      if (filters.geo_lat && filters.geo_lng && filters.geo_radius_km) {
        const lat = parseFloat(filters.geo_lat);
        const lng = parseFloat(filters.geo_lng);
        const radius = parseFloat(filters.geo_radius_km);
        if (!isNaN(lat) && !isNaN(lng) && !isNaN(radius)) {
          filtered = filtered.filter(r => haversineDist(lat, lng, r.lat, r.lng) <= radius);
        }
      }
    }

    if (mode === 'nl' && query) {
      const q = query.toLowerCase();
      if (q.includes('robbery')) filtered = mockResults.filter(r => r.head === 'Robbery');
      else if (q.includes('theft') || q.includes('kಳ್ಳತನ')) filtered = mockResults.filter(r => r.head === 'Theft');
      else if (q.includes('bengaluru') || q.includes('ಬೆಂಗಳೂರು')) filtered = mockResults.filter(r => r.location.includes('Bengaluru'));
      else if (q.includes('mysuru') || q.includes('ಮೈಸೂರು')) filtered = mockResults.filter(r => r.location.includes('Mysuru'));
      else if (q.includes('last month') || q.includes('ಕಳೆದ ತಿಂಗಳು')) filtered = mockResults.filter(r => r.date >= '2026-05-15');
      setSearchBotMsg(t('Analyzed query and auto-applied filters. Confidence: High', 'ಪ್ರಶ್ನೆಯನ್ನು ವಿಶ್ಲೇಷಿಸಲಾಗಿದೆ ಮತ್ತು ಸ್ವಯಂಚಾಲಿತ ಫಿಲ್ಟರ್‌ಗಳನ್ನು ಅನ್ವಯಿಸಲಾಗಿದೆ. ವಿಶ್ವಾಸ: ಹೆಚ್ಚು'));
    }

    // Sort
    filtered.sort((a, b) => {
      let cmp = 0;
      if (sortKey === 'date') cmp = a.date.localeCompare(b.date);
      else if (sortKey === 'crime_no') cmp = a.crime_no.localeCompare(b.crime_no);
      return sortDir === 'asc' ? cmp : -cmp;
    });

    setResults(filtered);
  };

  const toggleSort = (key: SortKey) => {
    if (sortKey === key) setSortDir(d => (d === 'asc' ? 'desc' : 'asc'));
    else { setSortKey(key); setSortDir('desc'); }
    setTimeout(handleSearch, 0);
  };

  return (
    <div style={{ display: 'flex', gap: 24 }}>
      <div style={{ flex: 1 }}>
        <div className="page-header">
          <h1>{t('Case Search & Retrieval', 'ಪ್ರಕರಣ ಹುಡುಕಾಟ ಮತ್ತು ಮರುಪಡೆಯುವಿಕೆ')}</h1>
          <p>{t('Search by Crime No, complainant, accused, location, or free-text', 'ಅಪರಾಧ ಸಂಖ್ಯೆ, ದೂರುದಾರ, ಆರೋಪಿ, ಸ್ಥಳ ಅಥವಾ ಮುಕ್ತ ಪಠ್ಯದ ಮೂಲಕ ಹುಡುಕಿ')}</p>
        </div>

        <div className="tabs" style={{ marginBottom: 16 }}>
          <button className={`tab ${mode === 'quick' ? 'active' : ''}`} onClick={() => setMode('quick')}>
            <Search size={14} /> {t('Quick', 'ತ್ವರಿತ')}
          </button>
          <button className={`tab ${mode === 'advanced' ? 'active' : ''}`} onClick={() => setMode('advanced')}>
            <Sliders size={14} /> {t('Advanced', 'ಸುಧಾರಿತ')}
          </button>
          <button className={`tab ${mode === 'nl' ? 'active' : ''}`} onClick={() => setMode('nl')}>
            <MessageSquare size={14} /> {t('Natural Language', 'ನೈಸರ್ಗಿಕ ಭಾಷೆ')}
          </button>
        </div>

        <div className="card" style={{ marginBottom: 24 }}>
          {mode === 'quick' && (
            <div style={{ display: 'flex', gap: 12 }}>
              <div className="input-group" style={{ flex: 1 }}>
                <Search className="input-icon" size={18} />
                <input className="input" placeholder={t('Search by Crime No, complainant, accused, location...', 'ಅಪರಾಧ ಸಂಖ್ಯೆ, ದೂರುದಾರ, ಆರೋಪಿ, ಸ್ಥಳ...')}
                  value={query} onChange={e => setQuery(e.target.value)}
                  onKeyDown={e => e.key === 'Enter' && handleSearch()} />
              </div>
              <button className="btn btn-primary" onClick={handleSearch}>{t('Search', 'ಹುಡುಕು')}</button>
            </div>
          )}

          {mode === 'advanced' && (
            <div>
              <div className="grid-3" style={{ marginBottom: 16 }}>
                <div className="form-group">
                  <label>{t('Date From', 'ದಿನಾಂಕ ಇಂದ')}</label>
                  <input className="input" type="date" value={filters.date_from} onChange={e => setFilters(f => ({ ...f, date_from: e.target.value }))} />
                </div>
                <div className="form-group">
                  <label>{t('Date To', 'ದಿನಾಂಕ ವರೆಗೆ')}</label>
                  <input className="input" type="date" value={filters.date_to} onChange={e => setFilters(f => ({ ...f, date_to: e.target.value }))} />
                </div>
                <div className="form-group">
                  <label>{t('Crime Type', 'ಅಪರಾಧ ಪ್ರಕಾರ')}</label>
                  <select className="input" value={filters.crime_type} onChange={e => setFilters(f => ({ ...f, crime_type: e.target.value }))}>
                    <option value="">{t('All', 'ಎಲ್ಲಾ')}</option>
                    {crimeTypes.map(ct => <option key={ct} value={ct}>{ct}</option>)}
                  </select>
                </div>
              </div>
              <div className="grid-3">
                <div className="form-group">
                  <label>{t('Case Status', 'ಪ್ರಕರಣ ಸ್ಥಿತಿ')}</label>
                  <select className="input" value={filters.status} onChange={e => setFilters(f => ({ ...f, status: e.target.value }))}>
                    <option value="">{t('All', 'ಎಲ್ಲಾ')}</option>
                    {statuses.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label>{t('Police Station', 'ಪೊಲೀಸ್ ಠಾಣೆ')}</label>
                  <select className="input" value={filters.station} onChange={e => setFilters(f => ({ ...f, station: e.target.value }))}>
                    <option value="">{t('All', 'ಎಲ್ಲಾ')}</option>
                    {stations.map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
                <div className="form-group">
                  <label>{t('Gravity', 'ಗುರುತ್ವ')}</label>
                  <select className="input" value={filters.gravity} onChange={e => setFilters(f => ({ ...f, gravity: e.target.value }))}>
                    <option value="">{t('All', 'ಎಲ್ಲಾ')}</option>
                    <option value="Heinous">{t('Heinous', 'ಗಂಭೀರ')}</option>
                    <option value="Non-Heinous">{t('Non-Heinous', 'ಅಗಂಭೀರ')}</option>
                  </select>
                </div>
              </div>
              <details style={{ marginTop: 16 }}>
                <summary className="text-sm" style={{ cursor: 'pointer', color: 'var(--text-muted)', fontWeight: 500 }}>
                  <MapPin size={14} style={{ display: 'inline' }} /> {t('Geo-filter (radius)', 'ಭೌಗೋಳಿಕ ಫಿಲ್ಟರ್ (ತ್ರಿಜ್ಯ)')}
                </summary>
                <div className="grid-3" style={{ marginTop: 12 }}>
                  <div className="form-group">
                    <label>{t('Center Latitude', 'ಕೇಂದ್ರ ಅಕ್ಷಾಂಶ')}</label>
                    <input className="input" type="number" step="0.01" placeholder="12.97" value={filters.geo_lat} onChange={e => setFilters(f => ({ ...f, geo_lat: e.target.value }))} />
                  </div>
                  <div className="form-group">
                    <label>{t('Center Longitude', 'ಕೇಂದ್ರ ರೇಖಾಂಶ')}</label>
                    <input className="input" type="number" step="0.01" placeholder="77.59" value={filters.geo_lng} onChange={e => setFilters(f => ({ ...f, geo_lng: e.target.value }))} />
                  </div>
                  <div className="form-group">
                    <label>{t('Radius (km)', 'ತ್ರಿಜ್ಯ (ಕಿಮೀ)')}</label>
                    <input className="input" type="number" min="0" step="0.5" placeholder="5" value={filters.geo_radius_km} onChange={e => setFilters(f => ({ ...f, geo_radius_km: e.target.value }))} />
                  </div>
                </div>
              </details>
              <button className="btn btn-primary" onClick={handleSearch} style={{ marginTop: 16 }}>{t('Search', 'ಹುಡುಕು')}</button>
            </div>
          )}

          {mode === 'nl' && (
            <div>
              <div style={{ display: 'flex', gap: 12 }}>
                <div className="input-group" style={{ flex: 1 }}>
                  <MessageSquare className="input-icon" size={18} />
                  <input className="input" placeholder={t('Describe what you are looking for...', 'ನೀವು ಏನನ್ನು ಹುಡುಕುತ್ತಿದ್ದೀರಿ ಎಂಬುದನ್ನು ವಿವರಿಸಿ...')}
                    value={query} onChange={e => setQuery(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleSearch()} />
                </div>
                <button className="btn btn-primary" onClick={handleSearch}>{t('Analyze', 'ವಿಶ್ಲೇಷಿಸಿ')}</button>
              </div>
              <p className="text-xs text-muted" style={{ marginTop: 8 }}>
                {t('e.g., "Robbery cases in Bengaluru last month" or "ಬೆಂಗಳೂರಿನಲ್ಲಿ ಕಳ್ಳತನದ ಪ್ರಕರಣಗಳು"', 'ಉದಾ: "Robbery cases in Bengaluru last month" ಅಥವಾ "ಬೆಂಗಳೂರಿನಲ್ಲಿ ಕಳ್ಳತನದ ಪ್ರಕರಣಗಳು"')}
              </p>
            </div>
          )}
        </div>

        {searched && (
          <div>
            <div className="flex justify-between items-center" style={{ marginBottom: 16 }}>
              <p className="text-sm text-muted">
                {results.length} {t('results found', 'ಫಲಿತಾಂಶಗಳು ಕಂಡುಬಂದಿವೆ')}
              </p>
              <div className="flex gap-2 items-center">
                <span className="text-xs text-muted">{t('Sort by', 'ವಿಂಗಡಿಸಿ')}:</span>
                <button className={`btn btn-ghost btn-sm ${sortKey === 'date' ? 'active' : ''}`} onClick={() => toggleSort('date')}>
                  {t('Date', 'ದಿನಾಂಕ')} <ArrowUpDown size={12} />
                </button>
                <button className={`btn btn-ghost btn-sm ${sortKey === 'crime_no' ? 'active' : ''}`} onClick={() => toggleSort('crime_no')}>
                  {t('Case ID', 'ಪ್ರಕರಣ ಐಡಿ')} <ArrowUpDown size={12} />
                </button>
              </div>
            </div>
            {results.length === 0 ? (
              <div className="card" style={{ textAlign: 'center', padding: 48 }}>
                <p className="text-muted">{t('No results found. Try adjusting your search criteria.', 'ಯಾವುದೇ ಫಲಿತಾಂಶಗಳು ಕಂಡುಬಂದಿಲ್ಲ. ನಿಮ್ಮ ಹುಡುಕಾಟ ಮಾನದಂಡಗಳನ್ನು ಸರಿಹೊಂದಿಸಿ.')}</p>
                <button className="btn btn-ghost btn-sm" style={{ marginTop: 12 }} onClick={() => setSearchBotMsg(t('Try: (1) Use broader terms, (2) Check spelling, (3) Remove date filters, (4) Search by Crime No directly.', 'ಪ್ರಯತ್ನಿಸಿ: (1) ವಿಶಾಲ ಪದಗಳನ್ನು ಬಳಸಿ, (2) ಕಾಗುಣಿತ ಪರಿಶೀಲಿಸಿ, (3) ದಿನಾಂಕ ಫಿಲ್ಟರ್‌ಗಳನ್ನು ತೆಗೆದುಹಾಕಿ, (4) ನೇರವಾಗಿ ಅಪರಾಧ ಸಂಖ್ಯೆಯಿಂದ ಹುಡುಕಿ.'))}>
                  {t('No results? Try...', 'ಫಲಿತಾಂಶಗಳಿಲ್ಲವೇ? ಪ್ರಯತ್ನಿಸಿ...')}
                </button>
              </div>
            ) : (
              results.map((r, i) => (
                <div key={i} className="card" style={{ marginBottom: 12, cursor: 'pointer' }}
                  onClick={() => setSelectedCase(r)}>
                  <div className="flex justify-between items-center" style={{ marginBottom: 8 }}>
                    <div>
                      <span style={{ fontFamily: 'monospace', fontWeight: 600, fontSize: 14 }}>{r.crime_no}</span>
                      <span className="badge badge-info" style={{ marginLeft: 8 }}>{r.head}</span>
                      <span className={`badge ${r.status === 'Under Investigation' ? 'badge-elevated' : r.status === 'Chargesheeted' ? 'badge-moderate' : 'badge-low'}`} style={{ marginLeft: 4 }}>{r.status}</span>
                    </div>
                    <ChevronRight size={16} style={{ color: 'var(--text-muted)' }} />
                  </div>
                  <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 4 }}>
                    <strong>{t('Complainant', 'ದೂರುದಾರ')}:</strong> {r.complainant} | <strong>{t('Accused', 'ಆರೋಪಿಗಳು')}:</strong> {r.accused_count} | <strong>{t('Location', 'ಸ್ಥಳ')}:</strong> {r.location}
                  </div>
                  <p className="text-xs text-muted">{r.snippet}</p>
                  <div className="text-xs text-muted" style={{ marginTop: 4 }}>{r.date}</div>
                </div>
              ))
            )}
          </div>
        )}

        {/* Case Detail Modal */}
        {selectedCase && (
          <div style={{
            position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)',
            display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
          }} onClick={() => setSelectedCase(null)}>
            <div className="card" style={{ width: 560, maxHeight: '80vh', overflow: 'auto' }} onClick={e => e.stopPropagation()}>
              <div className="card-header flex justify-between items-center">
                <h3>{t('Case Details', 'ಪ್ರಕರಣ ವಿವರಗಳು')}</h3>
                <button className="btn btn-ghost btn-icon" onClick={() => setSelectedCase(null)}><X size={20} /></button>
              </div>
              <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
                <div className="grid-2" style={{ marginBottom: 16 }}>
                  <div><strong>{t('Crime No', 'ಅಪರಾಧ ಸಂಖ್ಯೆ')}:</strong> <span style={{ fontFamily: 'monospace' }}>{selectedCase.crime_no}</span></div>
                  <div><strong>{t('Category', 'ವರ್ಗ')}:</strong> {selectedCase.category}</div>
                  <div><strong>{t('Type', 'ಪ್ರಕಾರ')}:</strong> {selectedCase.head}</div>
                  <div><strong>{t('Status', 'ಸ್ಥಿತಿ')}:</strong> {selectedCase.status}</div>
                  <div><strong>{t('Date', 'ದಿನಾಂಕ')}:</strong> {selectedCase.date}</div>
                  <div><strong>{t('Location', 'ಸ್ಥಳ')}:</strong> {selectedCase.location}</div>
                </div>
                <div className="card" style={{ padding: 16, marginBottom: 16 }}>
                  <strong>{t('Complainant', 'ದೂರುದಾರ')}:</strong> {selectedCase.complainant}<br />
                  <strong>{t('Accused Count', 'ಆರೋಪಿಗಳ ಸಂಖ್ಯೆ')}:</strong> {selectedCase.accused_count}
                </div>
                <p style={{ fontSize: 13 }}>{selectedCase.snippet}</p>
                <div className="flex gap-4" style={{ marginTop: 24 }}>
                  <button className="btn btn-primary btn-sm" onClick={() => window.location.hash = '/workspace'}>{t('View in Workspace', 'ಕಾರ್ಯಕ್ಷೇತ್ರದಲ್ಲಿ ವೀಕ್ಷಿಸಿ')}</button>
                  <button className="btn btn-secondary btn-sm" onClick={() => setSearchBotMsg(t('Checking similar cases based on crime type, location, and modus operandi...', 'ಅಪರಾಧ ಪ್ರಕಾರ, ಸ್ಥಳ ಮತ್ತು ಕಾರ್ಯವಿಧಾನದ ಆಧಾರದ ಮೇಲೆ ಹೋಲುವ ಪ್ರಕರಣಗಳನ್ನು ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ...'))}>
                    {t('Similar cases', 'ಹೋಲುವ ಪ್ರಕರಣಗಳು')}
                  </button>
                </div>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* SearchBot AI Panel */}
      <div style={{ width: 280, flexShrink: 0 }}>
        <div className="card" style={{ position: 'sticky', top: 32 }}>
          <div className="card-header flex items-center gap-2"><Bot size={20} /> {t('SearchBot', 'ಹುಡುಕು-ಬಾಟ್')}</div>
          <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
            <div style={{ marginBottom: 16, padding: 12, background: 'var(--bg-hover)', borderRadius: 8, fontSize: 13, minHeight: 40 }}>
              {searchBotMsg}
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              <button className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }}
                onClick={() => setSearchBotMsg(t('Try: (1) Use broader terms, (2) Check spelling, (3) Remove date filters, (4) Search by Crime No directly.', 'ಪ್ರಯತ್ನಿಸಿ: (1) ವಿಶಾಲ ಪದಗಳನ್ನು ಬಳಸಿ, (2) ಕಾಗುಣಿತ ಪರಿಶೀಲಿಸಿ, (3) ದಿನಾಂಕ ಫಿಲ್ಟರ್‌ಗಳನ್ನು ತೆಗೆದುಹಾಕಿ, (4) ನೇರವಾಗಿ ಅಪರಾಧ ಸಂಖ್ಯೆಯಿಂದ ಹುಡುಕಿ.'))}>
                {t('No results? Try...', 'ಫಲಿತಾಂಶಗಳಿಲ್ಲವೇ? ಪ್ರಯತ್ನಿಸಿ...')}
              </button>
              <button className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }}
                onClick={() => setSearchBotMsg(t('Checking for similar cases by crime type and location proximity...', 'ಅಪರಾಧ ಪ್ರಕಾರ ಮತ್ತು ಸ್ಥಳ ಸಾಮೀಪ್ಯದಿಂದ ಹೋಲುವ ಪ್ರಕರಣಗಳನ್ನು ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ...'))}>
                {t('Similar cases?', 'ಹೋಲುವ ಪ್ರಕರಣಗಳು?')}
              </button>
              <button className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }}
                onClick={() => setSearchBotMsg(t('Building network graph for people linked to this case...', 'ಈ ಪ್ರಕರಣಕ್ಕೆ ಲಿಂಕ್ ಮಾಡಲಾದ ಜನರ ನೆಟ್‌ವರ್ಕ್ ಗ್ರಾಫ್ ನಿರ್ಮಿಸಲಾಗುತ್ತಿದೆ...'))}>
                {t('People network?', 'ಜನರ ನೆಟ್‌ವರ್ಕ್?')}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
