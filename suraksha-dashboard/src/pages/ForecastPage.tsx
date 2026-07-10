import React, { useState, useEffect } from 'react';
import { AreaChart, Area, BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, Cell } from 'recharts';
import { TrendingUp, BarChart3, Download } from 'lucide-react';
import { api } from '../services/api';
import { ForecastDataPoint } from '../types';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';

const COLORS = ['#6C63FF', '#22C55E', '#F59E0B', '#EF4444', '#3B82F6'];

export const ForecastPage: React.FC = () => {
  const [multiData, setMultiData] = useState<{ category: string; data: ForecastDataPoint[] }[]>([]);
  const [districtData, setDistrictData] = useState<{ district: string; data: ForecastDataPoint[] }[]>([]);
  const [activeView, setActiveView] = useState<'crime' | 'district'>('crime');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      api.getMultiForecast(),
      api.getDistrictForecasts(),
    ]).then(([multi, districts]) => {
      setMultiData(multi);
      setDistrictData(districts);
      setLoading(false);
    });
  }, []);

  const exportPdf = async () => {
    const el = document.getElementById('forecast-content');
    if (!el) return;
    const canvas = await html2canvas(el, { backgroundColor: null, scale: 2 });
    const imgData = canvas.toDataURL('image/png');
    const pdf = new jsPDF('l', 'mm', 'a4');
    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
    pdf.addImage(imgData, 'PNG', 0, 0, pdfWidth, pdfHeight);
    pdf.save('suraksha-forecast-export.pdf');
  };

  if (loading) {
    return (
      <div>
        <div className="page-header"><h1>Crime Forecast</h1><p>Prophet time-series forecasting</p></div>
        {[1, 2, 3].map(i => <div key={i} className="skeleton" style={{ width: '100%', height: 300, borderRadius: 'var(--radius-card)', marginBottom: 24 }} />)}
      </div>
    );
  }

  const multiChartData = multiData.length > 0 ? multiData[0].data.map((_, i) => {
    const row: Record<string, any> = { date: `Day ${i + 1}` };
    multiData.forEach(m => { row[m.category] = m.data[i]?.predicted ?? 0; });
    return row;
  }) : [];

  return (
    <div>
      <div className="page-header flex justify-between items-center">
        <div>
          <h1>Crime Forecast</h1>
          <p>Prophet time-series forecasting with multi-category and district-level projections</p>
        </div>
        <button className="btn btn-primary btn-sm" onClick={exportPdf}><Download size={16} /> Export PDF</button>
      </div>

      <div className="tabs" style={{ marginBottom: 24 }}>
        <button className={`tab ${activeView === 'crime' ? 'active' : ''}`} onClick={() => setActiveView('crime')}>
          <TrendingUp size={16} style={{ marginRight: 6 }} /> By Crime Type
        </button>
        <button className={`tab ${activeView === 'district' ? 'active' : ''}`} onClick={() => setActiveView('district')}>
          <BarChart3 size={16} style={{ marginRight: 6 }} /> By District
        </button>
      </div>

      <div id="forecast-content">
        <div className="grid-4" style={{ marginBottom: 24 }}>
          {[
            { label: 'Forecast Model', value: 'Prophet v1.0' },
            { label: 'Confidence Interval', value: '80%' },
            { label: 'Forecast Horizon', value: '30 days' },
            { label: 'Data Granularity', value: 'Daily' },
          ].map(m => (
            <div key={m.label} className="card kpi-card">
              <div className="kpi-value" style={{ fontSize: 24 }}>{m.value}</div>
              <div className="kpi-label">{m.label}</div>
            </div>
          ))}
        </div>

        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-header">
            {activeView === 'crime'
              ? '30-Day Forecast by Crime Type — Bengaluru Urban'
              : '30-Day Forecast (Theft) by District'}
          </div>
          <ResponsiveContainer width="100%" height={400}>
            <AreaChart data={activeView === 'crime'
              ? (multiData[0]?.data || [])
              : (districtData[0]?.data || [])}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={12} />
              <YAxis stroke="var(--text-muted)" fontSize={12} />
              <Tooltip
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)' }}
              />
              <Area type="monotone" dataKey="upper" stroke="transparent" fill="var(--primary)" fillOpacity={0.1} />
              <Area type="monotone" dataKey="lower" stroke="transparent" fill="var(--primary)" fillOpacity={0.05} />
              <Area type="monotone" dataKey="predicted" stroke="var(--primary)" strokeWidth={2} fill="var(--primary)" fillOpacity={0.3} dot={false} />
              <Area type="monotone" dataKey="actual" stroke="#22C55E" strokeWidth={2} fill="transparent" dot={{ r: 3, fill: '#22C55E' }} />
            </AreaChart>
          </ResponsiveContainer>
        </div>

        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-header">
            {activeView === 'crime' ? 'Predicted Cases by Crime Type (Day 30)' : 'Predicted Theft Cases by District (Day 30)'}
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={(activeView === 'crime' ? multiData : districtData).map((d: any) => ({
              name: activeView === 'crime' ? d.category : d.district,
              value: (d.data[d.data.length - 1]?.predicted || 0),
            }))}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="name" stroke="var(--text-muted)" fontSize={12} />
              <YAxis stroke="var(--text-muted)" fontSize={12} />
              <Tooltip
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)' }}
              />
              <Bar dataKey="value" fill="var(--primary)" radius={[4, 4, 0, 0]}>
                {(activeView === 'crime' ? multiData : districtData).map((_: any, i: number) => (
                  <Cell key={i} fill={COLORS[i % COLORS.length]} />
                ))}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>

        {activeView === 'crime' && multiData.length > 1 && (
          <div className="card">
            <div className="card-header">Multi-Category Forecast Comparison</div>
            <ResponsiveContainer width="100%" height={350}>
              <AreaChart data={multiChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
                <XAxis dataKey="date" stroke="var(--text-muted)" fontSize={12} interval={5} />
                <YAxis stroke="var(--text-muted)" fontSize={12} />
                <Tooltip
                  contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)' }}
                />
                {multiData.map((m, i) => (
                  <Area key={m.category} type="monotone" dataKey={m.category} stroke={COLORS[i % COLORS.length]} strokeWidth={2} fill="transparent" dot={false} />
                ))}
              </AreaChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
};
