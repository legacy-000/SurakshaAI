import React, { useState, useEffect, useRef } from 'react';
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { MapPin, TrendingUp, AlertCircle } from 'lucide-react';
import L from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { api } from '../services/api';

export const AnalyticsPage: React.FC = () => {
  const [activeTab, setActiveTab] = useState<'trends' | 'hotspots'>('trends');
  const [trends, setTrends] = useState<any[]>([]);
  const [hotspots, setHotspots] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const mapRef = useRef<HTMLDivElement>(null);
  const mapInstanceRef = useRef<L.Map | null>(null);

  useEffect(() => {
    Promise.all([api.getTrends(), api.getHotspots()]).then(([t, h]) => {
      setTrends(t); setHotspots(h); setLoading(false);
    });
  }, []);

  useEffect(() => {
    if (activeTab !== 'hotspots' || !mapRef.current || mapInstanceRef.current || hotspots.length === 0) return;

    delete (L.Icon.Default.prototype as any)._getIconUrl;
    L.Icon.Default.mergeOptions({
      iconRetinaUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon-2x.png',
      iconUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-icon.png',
      shadowUrl: 'https://unpkg.com/leaflet@1.9.4/dist/images/marker-shadow.png',
    });

    const map = L.map(mapRef.current).setView([12.9716, 77.5946], 12);
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      attribution: '&copy; OpenStreetMap contributors',
    }).addTo(map);

    hotspots.forEach(cluster => {
      L.circleMarker([cluster.centroid_lat, cluster.centroid_lng], {
        radius: Math.min(cluster.case_count * 3, 30),
        color: cluster.case_count > 10 ? '#EF4444' : '#F59E0B',
        fillColor: cluster.case_count > 10 ? '#EF4444' : '#F59E0B',
        fillOpacity: 0.5,
        weight: 2,
      }).addTo(map).bindPopup(`<b>${cluster.crime_type}</b><br/>${cluster.case_count} cases<br/>${cluster.radius_km}km radius`);
    });

    mapInstanceRef.current = map;
  }, [activeTab, hotspots]);

  return (
    <div>
      <div className="page-header">
        <h1>Crime Analytics</h1>
        <p>Trends, patterns, and hotspot analysis</p>
      </div>

      <div className="tabs">
        <button className={`tab ${activeTab === 'trends' ? 'active' : ''}`} onClick={() => setActiveTab('trends')}>
          <TrendingUp size={16} style={{ marginRight: 6 }} /> Trends
        </button>
        <button className={`tab ${activeTab === 'hotspots' ? 'active' : ''}`} onClick={() => setActiveTab('hotspots')}>
          <MapPin size={16} style={{ marginRight: 6 }} /> Hotspots
        </button>
      </div>

      {loading ? (
        <div className="skeleton" style={{ width: '100%', height: 400, borderRadius: 'var(--radius-card)' }} />
      ) : activeTab === 'trends' ? (
        <div className="card">
          <div className="card-header flex justify-between">
            <span>Monthly Crime Trends</span>
            <div className="flex gap-2">
              <button className="btn btn-ghost btn-sm">Monthly</button>
              <button className="btn btn-ghost btn-sm">Weekly</button>
              <button className="btn btn-ghost btn-sm">Yearly</button>
            </div>
          </div>
          <ResponsiveContainer width="100%" height={400}>
            <LineChart data={trends}>
              <CartesianGrid strokeDasharray="3 3" stroke="var(--border)" />
              <XAxis dataKey="period" stroke="var(--text-muted)" fontSize={12} />
              <YAxis stroke="var(--text-muted)" fontSize={12} />
              <Tooltip
                contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, color: 'var(--text-primary)' }}
              />
              <Line type="monotone" dataKey="count" stroke="var(--primary)" strokeWidth={2} dot={{ fill: 'var(--primary)', r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      ) : (
        <div className="grid-2">
          <div className="card">
            <div className="card-header">DBSCAN Hotspot Clusters — Bangalore</div>
            <div ref={mapRef} style={{ height: 400, borderRadius: 8, overflow: 'hidden', zIndex: 1 }} />
          </div>
          <div>
            {hotspots.map(cluster => (
              <div key={cluster.cluster_id} className="card" style={{ marginBottom: 12 }}>
                <div className="flex justify-between items-center">
                  <div>
                    <div style={{ fontWeight: 600, fontSize: 14 }}>{cluster.crime_type}</div>
                    <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{cluster.case_count} cases · {cluster.radius_km}km radius</div>
                  </div>
                  <span className={`badge ${cluster.case_count > 10 ? 'badge-elevated' : 'badge-moderate'}`}>
                    {cluster.case_count} cases
                  </span>
                </div>
              </div>
            ))}
            <div className="card">
              <div className="flex gap-2 items-center" style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                <AlertCircle size={14} />
                Algorithm: DBSCAN (eps=0.5km, min_samples=5, metric=haversine)
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
