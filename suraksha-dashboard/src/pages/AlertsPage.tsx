import React from 'react';
import { Check, AlertTriangle, TrendingUp, MapPin } from 'lucide-react';

const alerts = [
  {
    id: 1, type: 'critical', rule: 'EW-001', title: 'Crime Count Spike Detected — Bangalore Urban',
    description: '7-day crime count is 2.5x above 30-day average. Z-score: 2.3',
    trigger: 'Z = (count_7d - mean_30d) / std_30d > 2.0',
    icon: TrendingUp,
  },
  {
    id: 2, type: 'warning', rule: 'EW-002', title: 'Emerging Hotspot — Mysuru',
    description: 'New DBSCAN cluster detected: 8 cases in 0.5km radius (Robbery)',
    trigger: 'New cluster not present in previous 30 days',
    icon: MapPin,
  },
  {
    id: 3, type: 'warning', rule: 'EW-003', title: 'Repeat Accused Activity — Ravi Kumar',
    description: '2 new cases linked to entity in last 30 days. Total: 8 cases.',
    trigger: 'Resolved entity with >=2 new cases in window AND >=3 historical cases',
    icon: AlertTriangle,
  },
];

export const AlertsPage: React.FC = () => {
  return (
    <div>
      <div className="page-header">
        <h1>Early Warning Alerts</h1>
        <p>Automated crime pattern detection and alerting</p>
      </div>

      {alerts.map(alert => (
        <div key={alert.id} className={`alert-card ${alert.type}`}>
          <div className="flex justify-between">
            <div className="flex gap-3" style={{ flex: 1 }}>
              <alert.icon size={24} color={alert.type === 'critical' ? 'var(--danger)' : alert.type === 'warning' ? 'var(--warning)' : 'var(--blue)'} />
              <div>
                <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 4 }}>
                  <span className={`badge ${alert.type === 'critical' ? 'badge-high' : alert.type === 'warning' ? 'badge-elevated' : 'badge-info'}`}>
                    {alert.type.toUpperCase()}
                  </span>
                  <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>Rule: {alert.rule}</span>
                </div>
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>{alert.title}</h3>
                <p style={{ fontSize: 14, color: 'var(--text-secondary)' }}>{alert.description}</p>
                <div style={{ marginTop: 12, padding: '8px 12px', background: 'var(--bg-secondary)', borderRadius: 8, fontFamily: 'monospace', fontSize: 12, color: 'var(--text-muted)' }}>
                  {alert.trigger}
                </div>
              </div>
            </div>
            <button className="btn btn-secondary btn-sm" style={{ alignSelf: 'flex-start' }}>
              <Check size={14} /> Acknowledge
            </button>
          </div>
        </div>
      ))}
    </div>
  );
};
