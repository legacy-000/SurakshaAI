import React, { useState, useEffect } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { Check, AlertTriangle, Activity, RefreshCw, Eye, Clock, ChevronDown, ChevronUp } from 'lucide-react';
import { api } from '../services/api';

type Alert = {
  id: string; severity: string; title: string; description: string;
  rule_id: string; trigger_condition: string; created_at: string;
  acknowledged: boolean; evidence?: any[];
};

const SEVERITY_ORDER = ['critical', 'warning', 'info'];

export const AlertsPage: React.FC = () => {
  const { t } = useLanguage();
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [loading, setLoading] = useState(true);
  const [expanded, setExpanded] = useState<string | null>(null);
  const [filter, setFilter] = useState<'all' | 'critical' | 'warning' | 'info'>('all');

  const loadAlerts = async () => {
    setLoading(true);
    try {
      const data = await api.getAlerts();
      setAlerts(data || []);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { loadAlerts(); }, []);

  const acknowledgeAlert = (id: string) => {
    setAlerts(prev => prev.map(a => a.id === id ? { ...a, acknowledged: true } : a));
  };

  const filtered = alerts
    .filter(a => filter === 'all' || a.severity === filter)
    .sort((a, b) => SEVERITY_ORDER.indexOf(a.severity) - SEVERITY_ORDER.indexOf(b.severity));

  const counts = { critical: alerts.filter(a => a.severity === 'critical' && !a.acknowledged).length };

  return (
    <div>
      <div className="page-header">
        <h1>{t('Early Warning Alerts', 'ಮುಂಚಿನ ಎಚ್ಚರಿಕೆ ಅಲರ್ಟ್‌ಗಳು')}</h1>
        <p>{t('Deterministic early-warning signal triage', 'ನಿರ್ಣಾಯಕ ಮುಂಚಿನ ಎಚ್ಚರಿಕೆ ಸಂಕೇತ ತ್ರಿಯೇಜ್')}</p>
      </div>

      {counts.critical > 0 && (
        <div className="alert-card critical" style={{ marginBottom: 16, padding: 12, display: 'flex', gap: 8, alignItems: 'center' }}>
          <AlertTriangle size={20} />
          <span style={{ fontWeight: 600 }}>{counts.critical} {t('unacknowledged critical alert(s)', 'ದೃಢೀಕರಿಸದ ನಿರ್ಣಾಯಕ ಎಚ್ಚರಿಕೆ(ಗಳು)')}</span>
        </div>
      )}

      <div className="flex" style={{ gap: 8, marginBottom: 16 }}>
        {(['all', 'critical', 'warning', 'info'] as const).map(f => (
          <button key={f} className={`btn btn-sm ${filter === f ? 'btn-primary' : 'btn-secondary'}`} onClick={() => setFilter(f)}>
            {f === 'critical' && <AlertTriangle size={14} />}
            {f === 'warning' && <Activity size={14} />}
            {f === 'info' && <Eye size={14} />}
            {t(f.charAt(0).toUpperCase() + f.slice(1), f === 'all' ? 'ಎಲ್ಲಾ' : f === 'critical' ? 'ನಿರ್ಣಾಯಕ' : f === 'warning' ? 'ಎಚ್ಚರಿಕೆ' : 'ಮಾಹಿತಿ')}
          </button>
        ))}
        <button className="btn btn-secondary btn-sm" onClick={loadAlerts} style={{ marginLeft: 'auto' }}>
          <RefreshCw size={14} /> {t('Refresh', 'ರಿಫ್ರೆಶ್')}
        </button>
      </div>

      {loading ? (
        <div className="card" style={{ textAlign: 'center', padding: 32, color: 'var(--text-muted)' }}>{t('Loading alerts...', 'ಎಚ್ಚರಿಕೆಗಳನ್ನು ಲೋಡ್ ಮಾಡಲಾಗುತ್ತಿದೆ...')}</div>
      ) : filtered.length === 0 ? (
        <div className="card" style={{ textAlign: 'center', padding: 32, color: 'var(--text-muted)' }}>{t('No alerts match filter.', 'ಯಾವುದೇ ಎಚ್ಚರಿಕೆಗಳು ಹೊಂದಾಣಿಕೆಯಾಗಲಿಲ್ಲ.')}</div>
      ) : (
        filtered.map(alert => {
          const isExpanded = expanded === alert.id;
          const severityIcon = alert.severity === 'critical' ? AlertTriangle : alert.severity === 'warning' ? Activity : Eye;
          const SeverityIcon = severityIcon;
          return (
            <div key={alert.id} className={`alert-card ${alert.severity}`} style={{ opacity: alert.acknowledged ? 0.6 : 1 }}>
              <div className="flex justify-between">
                <div className="flex gap-3" style={{ flex: 1 }}>
                  <SeverityIcon size={24} color={alert.severity === 'critical' ? 'var(--danger)' : alert.severity === 'warning' ? 'var(--warning)' : 'var(--blue)'} />
                  <div>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center', marginBottom: 4 }}>
                      <span className={`badge ${alert.severity === 'critical' ? 'badge-high' : alert.severity === 'warning' ? 'badge-elevated' : 'badge-info'}`}>
                        {alert.severity.toUpperCase()}
                      </span>
                      <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{t('Rule', 'ನಿಯಮ')}: {alert.rule_id}</span>
                      {alert.acknowledged && <span className="badge badge-info">{t('Acknowledged', 'ದೃಢೀಕರಿಸಲಾಗಿದೆ')}</span>}
                    </div>
                    <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 4 }}>{alert.title}</h3>
                    <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 8 }}>{alert.description}</p>
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center', fontSize: 12, color: 'var(--text-muted)' }}>
                      <Clock size={12} /> {new Date(alert.created_at).toLocaleString()}
                    </div>

                    <div style={{ marginTop: 12, background: 'var(--bg-secondary)', borderRadius: 8, overflow: 'hidden' }}>
                      <div
                        className="flex justify-between"
                        style={{ padding: '8px 12px', cursor: 'pointer', alignItems: 'center' }}
                        onClick={() => setExpanded(isExpanded ? null : alert.id)}
                      >
                        <span style={{ fontSize: 12, fontFamily: 'monospace', color: 'var(--text-muted)' }}>
                          {t('Trigger condition', 'ಪ್ರಚೋದಕ ಸ್ಥಿತಿ')}
                        </span>
                        {isExpanded ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
                      </div>
                      {isExpanded && (
                        <div style={{ padding: '8px 12px', borderTop: '1px solid var(--border)' }}>
                          <code style={{ fontSize: 12, color: 'var(--text-secondary)' }}>{alert.trigger_condition}</code>
                          {alert.evidence && alert.evidence.length > 0 && (
                            <div style={{ marginTop: 8, fontSize: 12, color: 'var(--text-muted)' }}>
                              {alert.evidence.map((ev: any, i: number) => (
                                <div key={i} style={{ marginBottom: 4 }}>
                                  <strong>{ev.evidence_type}:</strong> {JSON.stringify(ev)}
                                </div>
                              ))}
                            </div>
                          )}
                        </div>
                      )}
                    </div>
                  </div>
                </div>
                {!alert.acknowledged && (
                  <button className="btn btn-secondary btn-sm" style={{ alignSelf: 'flex-start' }} onClick={() => acknowledgeAlert(alert.id)}>
                    <Check size={14} /> {t('Acknowledge', 'ದೃಢೀಕರಿಸಿ')}
                  </button>
                )}
              </div>
            </div>
          );
        })
      )}
    </div>
  );
};
