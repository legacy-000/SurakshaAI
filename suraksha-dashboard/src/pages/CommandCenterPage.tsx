import React, { useState, useEffect, useRef } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { Bot, TrendingUp, TrendingDown, ChevronDown, ChevronUp, MapPin, AlertTriangle } from 'lucide-react';
import { api } from '../services/api';

const kpiDefaults = [
  { label: 'Active Cases', value: '156', change: '-8.2%', up: false },
  { label: 'This Month FIRs', value: '847', change: '+12.4%', up: true },
  { label: 'Arrests This Month', value: '312', change: '+5.7%', up: true },
  { label: 'Chargesheet Rate', value: '71.2%', change: '+3.1%', up: true },
  { label: 'Crime Hotspots', value: '8', change: '+2', up: true },
];

const intelligenceFeed = [
  { time: '2 min ago', event: 'FIR 104430006202600001 filed — Robbery, Bengaluru South', type: 'case' },
  { time: '15 min ago', event: 'Accused A1 arrested in FIR 104430006202600001', type: 'arrest' },
  { time: '1 hour ago', event: 'Alert: Repeat offender in custody for 3rd time this month', type: 'alert', severity: 'critical' },
  { time: '2 hours ago', event: 'Chargesheet filed for FIR 104430006202600002', type: 'chargesheet' },
  { time: '3 hours ago', event: 'Hotspot alert: Theft cluster detected in Whitefield', type: 'alert', severity: 'warning' },
  { time: '5 hours ago', event: 'Network analysis complete: 4 communities in Bengaluru network', type: 'network' },
];

const districtData = [
  { name: 'Bengaluru Urban', cases: 2847, change: '+12%' },
  { name: 'Bengaluru Rural', cases: 1245, change: '+8%' },
  { name: 'Mysuru', cases: 982, change: '-3%' },
  { name: 'Belagavi', cases: 876, change: '+5%' },
  { name: 'Hubballi-Dharwad', cases: 654, change: '+15%' },
  { name: 'Mangaluru', cases: 543, change: '-2%' },
  { name: 'Kalaburagi', cases: 432, change: '+7%' },
  { name: 'Shivamogga', cases: 321, change: '+1%' },
];

// ponytail: simplified district coords for heatmap, GeoJSON boundary source when available
const districtCoords: Record<string, { lat: number; lng: number }> = {
  'Bengaluru Urban': { lat: 12.9716, lng: 77.5946 },
  'Bengaluru Rural': { lat: 13.1, lng: 77.6 },
  'Mysuru': { lat: 12.2958, lng: 76.6394 },
  'Belagavi': { lat: 15.8497, lng: 74.4977 },
  'Hubballi-Dharwad': { lat: 15.3647, lng: 75.1240 },
  'Mangaluru': { lat: 12.9141, lng: 74.8560 },
  'Kalaburagi': { lat: 17.3297, lng: 76.8343 },
  'Shivamogga': { lat: 13.9299, lng: 75.5681 },
};

export const CommandCenterPage: React.FC = () => {
  const { t } = useLanguage();
  const [commanderMsg, setCommanderMsg] = useState(t('I am CommanderAI. Overview intelligence at your command.', 'ನಾನು ಸೈನ್ಯಾಧಿಕಾರಿ-ಎಐ. ನಿಮ್ಮ ಆಜ್ಞೆಯಲ್ಲಿ ಗುಪ್ತಚರ ಅವಲೋಕನ.'));
  const [showAi, setShowAi] = useState(true);
  const [kpIs, setKpis] = useState(kpiDefaults);
  const canvasRef = useRef<HTMLCanvasElement>(null);

  useEffect(() => {
    api.getDashboardKpis().then(data => {
      if (data) setKpis(data.map((d: any) => ({
        label: d.label, value: d.value, change: d.change, up: d.change?.startsWith('+')
      })));
    }).catch(() => {});
  }, []);

  // Draw simplified Karnataka heatmap on canvas
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;
    const w = canvas.width, h = canvas.height;

    ctx.clearRect(0, 0, w, h);

    // Background
    ctx.fillStyle = 'rgba(30,41,59,0.05)';
    ctx.fillRect(0, 0, w, h);

    // Draw district circles as heatmap
    const maxCases = Math.max(...districtData.map(d => d.cases));
    districtData.forEach(d => {
      const c = districtCoords[d.name];
      if (!c) return;
      const x = ((c.lng - 74) / (78 - 74)) * w;
      const y = ((16.5 - c.lat) / (16.5 - 11.5)) * h;
      const r = (d.cases / maxCases) * 60 + 10;
      const intensity = d.cases / maxCases;

      const gradient = ctx.createRadialGradient(x, y, 0, x, y, r);
      gradient.addColorStop(0, `rgba(239, ${Math.round(68 + (1 - intensity) * 150)}, ${Math.round(68 + (1 - intensity) * 150)}, 0.7)`);
      gradient.addColorStop(1, 'rgba(239,68,68,0)');
      ctx.fillStyle = gradient;
      ctx.beginPath();
      ctx.arc(x, y, r, 0, Math.PI * 2);
      ctx.fill();

      // Label
      ctx.fillStyle = 'var(--text-primary)';
      ctx.font = '10px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.fillText(d.name.split(' ')[0], x, y + 4);
    });

    // Border outline
    ctx.strokeStyle = 'var(--border)';
    ctx.lineWidth = 2;
    ctx.strokeRect(2, 2, w - 4, h - 4);
  }, []);

  return (
    <div style={{ display: 'flex', gap: 24 }}>
      <div style={{ flex: 1 }}>
        <div className="page-header">
          <h1>{t('Command Center', 'ಸೈನ್ಯಾಧಿಕಾರಿ ಕೇಂದ್ರ')}</h1>
          <p>{t('Real-time district crime intelligence and priority alerts', 'ನೈಜ-ಸಮಯದ ಜಿಲ್ಲಾ ಅಪರಾಧ ಗುಪ್ತಚರ ಮತ್ತು ಆದ್ಯತೆಯ ಎಚ್ಚರಿಕೆಗಳು')}</p>
        </div>

        {/* KPI Cards */}
        <div className="grid-4" style={{ marginBottom: 24 }}>
          {kpIs.map((kpi, i) => (
            <div key={i} className="card kpi-card" style={{ padding: 20 }}>
              <div className="kpi-value" style={{ fontSize: 28 }}>{kpi.value}</div>
              <div className="kpi-label" style={{ fontSize: 12 }}>{kpi.label}</div>
              <div style={{ fontSize: 12, marginTop: 4, color: kpi.up ? 'var(--success)' : 'var(--danger)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 4 }}>
                {kpi.up ? <TrendingUp size={14} /> : <TrendingDown size={14} />}
                {kpi.change}
              </div>
            </div>
          ))}
        </div>

        <div className="grid-2" style={{ marginBottom: 24 }}>
          {/* Map */}
          <div className="card">
            <div className="card-header flex items-center gap-2"><MapPin size={16} /> {t('Crime Heat Map — Karnataka', 'ಅಪರಾಧ ಶಾಖ ನಕ್ಷೆ — ಕರ್ನಾಟಕ')}</div>
            <canvas ref={canvasRef} width={400} height={320} style={{ width: '100%', height: 320, borderRadius: 8 }} />
            <div className="flex gap-2" style={{ marginTop: 12 }}>
              <span className="badge badge-low" style={{ fontSize: 10 }}>{t('Low', 'ಕಡಿಮೆ')}</span>
              <span className="badge badge-moderate" style={{ fontSize: 10 }}>{t('Medium', 'ಮಧ್ಯಮ')}</span>
              <span className="badge badge-elevated" style={{ fontSize: 10 }}>{t('High', 'ಹೆಚ್ಚು')}</span>
              <span className="badge badge-high" style={{ fontSize: 10 }}>{t('Critical', 'ವಿಮರ್ಶಾತ್ಮಕ')}</span>
            </div>
          </div>

          {/* Intelligence Stream */}
          <div className="card" style={{ maxHeight: 420, overflow: 'auto' }}>
            <div className="card-header">{t('Intelligence Stream', 'ಗುಪ್ತಚರ ಸ್ಟ್ರೀಮ್')}</div>
            {intelligenceFeed.map((item, i) => (
              <div key={i} style={{
                display: 'flex', gap: 12, padding: '10px 0', borderBottom: '1px solid var(--border)',
                cursor: 'pointer', alignItems: 'flex-start'
              }} onClick={() => setCommanderMsg(item.event)}>
                <div style={{
                  width: 8, height: 8, borderRadius: '50%', marginTop: 6, flexShrink: 0,
                  background: item.type === 'alert' && item.severity === 'critical' ? 'var(--danger)'
                    : item.type === 'alert' ? 'var(--warning)'
                    : item.type === 'case' ? 'var(--primary)' : 'var(--success)'
                }} />
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{item.event}</div>
                  <div className="text-xs text-muted" style={{ marginTop: 2 }}>{item.time}</div>
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* District Table */}
        <div className="card">
          <div className="card-header">{t('District Crime Summary', 'ಜಿಲ್ಲಾ ಅಪರಾಧ ಸಾರಾಂಶ')}</div>
          <div className="table-container">
            <table>
              <thead><tr><th>{t('District', 'ಜಿಲ್ಲೆ')}</th><th>{t('Total Cases', 'ಒಟ್ಟು ಪ್ರಕರಣಗಳು')}</th><th>{t('Change', 'ಬದಲಾವಣೆ')}</th><th>{t('Status', 'ಸ್ಥಿತಿ')}</th></tr></thead>
              <tbody>
                {districtData.map((d, i) => (
                  <tr key={i}>
                    <td style={{ fontWeight: 500 }}>{d.name}</td>
                    <td>{d.cases.toLocaleString()}</td>
                    <td style={{ color: d.change.startsWith('+') ? 'var(--danger)' : 'var(--success)' }}>{d.change}</td>
                    <td>
                      <span className={`badge ${parseInt(d.change) > 5 ? 'badge-elevated' : parseInt(d.change) < 0 ? 'badge-low' : 'badge-moderate'}`}>
                        {parseInt(d.change) > 5 ? t('Elevated', 'ಏರಿಕೆ') : parseInt(d.change) < 0 ? t('Declining', 'ಇಳಿಕೆ') : t('Stable', 'ಸ್ಥಿರ')}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      {/* CommanderAI Panel */}
      <div style={{ width: 280, flexShrink: 0 }}>
        <div className="card" style={{ position: 'sticky', top: 32 }}>
          <div className="card-header flex justify-between items-center">
            <span className="flex items-center gap-2"><Bot size={20} /> {t('CommanderAI', 'ಸೈನ್ಯಾಧಿಕಾರಿ-ಎಐ')}</span>
            <button className="btn btn-ghost btn-icon" onClick={() => setShowAi(!showAi)}>
              {showAi ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
            </button>
          </div>
          {showAi && (
            <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
              <div style={{ marginBottom: 12, padding: 12, background: 'var(--bg-hover)', borderRadius: 8, fontSize: 13 }}>
                {commanderMsg}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <button className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }}
                  onClick={() => setCommanderMsg(t('Bengaluru Urban has highest crime density (2,847 cases). Theft is the most common crime (42%). Recommend increased patrol in Whitefield and KG Halli.', 'ಬೆಂಗಳೂರು ನಗರದಲ್ಲಿ ಅತಿ ಹೆಚ್ಚು ಅಪರಾಧ ಸಾಂದ್ರತೆ (2,847 ಪ್ರಕರಣಗಳು). ಕಳ್ಳತನ ಸಾಮಾನ್ಯ ಅಪರಾಧ (42%). ವೈಟ್‌ಫೀಲ್ಡ್ ಮತ್ತು ಕೆಜಿ ಹಳ್ಳಿಯಲ್ಲಿ ಹೆಚ್ಚಿನ ಗಸ್ತು ಶಿಫಾರಸು.'))}>
                  <MapPin size={14} /> {t('Hotspot overview?', 'ಹಾಟ್‌ಸ್ಪಾಟ್ ಅವಲೋಕನ?')}
                </button>
                <button className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }}
                  onClick={() => setCommanderMsg(t('Anomaly detected: Hubballi-Dharwad showing +15% increase this month. Recommend reviewing recent case filings and deploying additional resources.', 'ವೈಪರೀತ್ಯ ಪತ್ತೆಯಾಗಿದೆ: ಹುಬ್ಬಳ್ಳಿ-ಧಾರವಾಡ ಈ ತಿಂಗಳು +15% ಹೆಚ್ಚಳ ತೋರಿಸುತ್ತಿದೆ. ಇತ್ತೀಚಿನ ಪ್ರಕರಣ ದಾಖಲಾತಿಗಳನ್ನು ಪರಿಶೀಲಿಸಲು ಮತ್ತು ಹೆಚ್ಚುವರಿ ಸಂಪನ್ಮೂಲಗಳನ್ನು ನಿಯೋಜಿಸಲು ಶಿಫಾರಸು.'))}>
                  <AlertTriangle size={14} /> {t('Anything unusual?', 'ಏನಾದರೂ ಅಸಾಮಾನ್ಯ?')}
                </button>
                <button className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }}
                  onClick={() => setCommanderMsg(t('Forecast: Theft cases expected to rise 12-18% next quarter. Peak during Oct-Dec. Recommend proactive patrolling and community awareness programs.', 'ಮುನ್ಸೂಚನೆ: ಮುಂದಿನ ತ್ರೈಮಾಸಿಕದಲ್ಲಿ ಕಳ್ಳತನ ಪ್ರಕರಣಗಳು 12-18% ಏರಿಕೆಯಾಗುವ ನಿರೀಕ್ಷೆಯಿದೆ. ಅಕ್ಟೋಬರ್-ಡಿಸೆಂಬರ್ ನಲ್ಲಿ ಗರಿಷ್ಠ. ಪೂರ್ವಭಾವಿ ಗಸ್ತು ಮತ್ತು ಸಮುದಾಯ ಜಾಗೃತಿ ಕಾರ್ಯಕ್ರಮಗಳನ್ನು ಶಿಫಾರಸು.'))}>
                  <TrendingUp size={14} /> {t('Forecast this trend', 'ಈ ಪ್ರವೃತ್ತಿಯ ಮುನ್ಸೂಚನೆ')}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
