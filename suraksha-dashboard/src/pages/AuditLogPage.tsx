import React, { useState, useEffect, useCallback } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { api } from '../services/api';
import { Activity, Clock, Search, AlertTriangle, CheckCircle, Info, XCircle, Shield, RefreshCw } from 'lucide-react';
import type { AuditLogEntry } from '../types';

const CATEGORY_ICONS: Record<string, React.ReactNode> = {
  access_control: <Shield size={14} />,
  communication: <Activity size={14} />,
  group_management: <Info size={14} />,
  coordination: <Activity size={14} />,
  authentication: <Shield size={14} />,
};

const RESULT_COLORS: Record<string, string> = {
  allowed: 'var(--success)', success: 'var(--success)', active: 'var(--info)',
  pending: 'var(--warning)', warning: 'var(--warning)', info: 'var(--info)',
  error: 'var(--danger)', denied: 'var(--danger)', not_found: 'var(--text-muted)', skipped: 'var(--text-muted)',
};

export const AuditLogPage: React.FC = () => {
  const { t } = useLanguage();
  const [logs, setLogs] = useState<AuditLogEntry[]>([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState<string>('all');

  const fetchLogs = useCallback(async () => {
    const data = await api.listAuditLog(200);
    setLogs(data);
    setLoading(false);
  }, []);

  useEffect(() => { fetchLogs(); }, [fetchLogs]);

  const categories = Array.from(new Set(logs.map(l => l.category).filter(Boolean)));

  const filtered = logs.filter(l => {
    if (categoryFilter !== 'all' && l.category !== categoryFilter) return false;
    if (search && !l.detail.toLowerCase().includes(search.toLowerCase()) && !l.actor_kgid.toLowerCase().includes(search.toLowerCase()) && !l.actor_role.toLowerCase().includes(search.toLowerCase())) return false;
    return true;
  });

  return (
    <div>
      <div className="page-header flex justify-between items-center">
        <div>
          <h1>{t('Audit Log', 'ಆಡಿಟ್ ಲಾಗ್')}</h1>
          <p>{t('Activity trail of all communications and access events', 'ಎಲ್ಲಾ ಸಂವಹನ ಮತ್ತು ಪ್ರವೇಶ ಘಟನೆಗಳ ಚಟುವಟಿಕೆ ಜಾಡು')}</p>
        </div>
        <button className="btn btn-ghost btn-sm" onClick={fetchLogs}><RefreshCw size={14} /> {t('Refresh', 'ರಿಫ್ರೆಶ್')}</button>
      </div>

      <div className="card" style={{ marginBottom: 16 }}>
        <div className="flex gap-4 items-center" style={{ flexWrap: 'wrap' }}>
          <div className="form-group" style={{ flex: 1, minWidth: 200, marginBottom: 0 }}>
            <div className="flex items-center gap-2" style={{ border: '1px solid var(--border)', borderRadius: 8, padding: '4px 12px' }}>
              <Search size={16} style={{ color: 'var(--text-muted)' }} />
              <input className="input" style={{ border: 'none', outline: 'none', padding: 8 }} placeholder={t('Search logs...', 'ಲಾಗ್‌ಗಳನ್ನು ಹುಡುಕಿ...')}
                value={search} onChange={e => setSearch(e.target.value)} />
            </div>
          </div>
          <div className="form-group" style={{ minWidth: 180, marginBottom: 0 }}>
            <select className="input" value={categoryFilter} onChange={e => setCategoryFilter(e.target.value)}>
              <option value="all">{t('All Categories', 'ಎಲ್ಲಾ ವರ್ಗಗಳು')}</option>
              {categories.map(c => <option key={c} value={c}>{c.replace(/_/g, ' ')}</option>)}
            </select>
          </div>
          <span className="text-xs text-muted">{filtered.length} {t('events', 'ಘಟನೆಗಳು')}</span>
        </div>
      </div>

      {loading ? (
        <div className="card" style={{ padding: 48, textAlign: 'center' }}><p className="text-muted">{t('Loading...', 'ಲೋಡ್ ಆಗುತ್ತಿದೆ...')}</p></div>
      ) : filtered.length === 0 ? (
        <div className="card" style={{ padding: 48, textAlign: 'center' }}>
          <Activity size={48} style={{ color: 'var(--text-muted)', marginBottom: 16 }} />
          <p className="text-muted">{t('No matching events', 'ಯಾವುದೇ ಹೊಂದಾಣಿಕೆಯ ಘಟನೆಗಳಿಲ್ಲ')}</p>
        </div>
      ) : (
        <div className="card" style={{ padding: 0, overflow: 'hidden' }}>
          <div style={{ maxHeight: '70vh', overflow: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: 'var(--bg-hover)' }}>
                  <th style={{ padding: '10px 12px', textAlign: 'left', fontSize: 12, fontWeight: 600 }}>{t('Time', 'ಸಮಯ')}</th>
                  <th style={{ padding: '10px 12px', textAlign: 'left', fontSize: 12, fontWeight: 600 }}>{t('Event', 'ಘಟನೆ')}</th>
                  <th style={{ padding: '10px 12px', textAlign: 'left', fontSize: 12, fontWeight: 600 }}>{t('Actor', 'ನಟ')}</th>
                  <th style={{ padding: '10px 12px', textAlign: 'left', fontSize: 12, fontWeight: 600 }}>{t('Detail', 'ವಿವರ')}</th>
                  <th style={{ padding: '10px 12px', textAlign: 'center', fontSize: 12, fontWeight: 600 }}>{t('Result', 'ಫಲಿತಾಂಶ')}</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((l, i) => (
                  <tr key={l.entry_id} style={{ borderBottom: '1px solid var(--border)', background: i % 2 === 0 ? undefined : 'var(--bg-hover)' }}>
                    <td style={{ padding: '10px 12px', whiteSpace: 'nowrap', fontSize: 12 }}>
                      <div className="flex items-center gap-1">
                        <Clock size={12} style={{ color: 'var(--text-muted)' }} />
                        <span>{new Date(l.timestamp).toLocaleString('en-IN')}</span>
                      </div>
                    </td>
                    <td style={{ padding: '10px 12px' }}>
                      <div className="flex items-center gap-2">
                        <span style={{ color: 'var(--text-muted)' }}>{CATEGORY_ICONS[l.category] || <Info size={14} />}</span>
                        <span style={{ fontSize: 12, fontWeight: 500 }}>{l.event_type.replace(/_/g, ' ')}</span>
                      </div>
                    </td>
                    <td style={{ padding: '10px 12px', fontSize: 12 }}>{l.actor_role} {l.actor_kgid}</td>
                    <td style={{ padding: '10px 12px', fontSize: 12 }}>
                      {l.detail}
                      {l.resource_id && <span className="badge badge-info" style={{ marginLeft: 8, fontSize: 10 }}>{l.resource_type || ''}: {l.resource_id}</span>}
                    </td>
                    <td style={{ padding: '10px 12px', textAlign: 'center' }}>
                      <span style={{ display: 'inline-flex', alignItems: 'center', gap: 4, fontSize: 11, color: RESULT_COLORS[l.result] || 'var(--text-muted)' }}>
                        {l.result === 'error' || l.result === 'denied' ? <XCircle size={12} /> :
                         l.result === 'warning' ? <AlertTriangle size={12} /> : <CheckCircle size={12} />}
                        {l.result}
                      </span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
};
