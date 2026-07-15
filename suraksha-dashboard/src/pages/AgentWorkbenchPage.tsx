import React, { useState } from 'react';
import { Bot, Send, CheckCircle, XCircle, Clock, ChevronDown, ChevronUp, Activity } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';
import { api } from '../services/api';

const AGENTS = [
  { id: 'database_query', label: 'Database Agent', color: '#3B82F6' },
  { id: 'trend_analysis', label: 'Trend Agent', color: '#22C55E' },
  { id: 'geospatial_analysis', label: 'Geospatial Agent', color: '#F59E0B' },
  { id: 'offender_profile', label: 'Offender Agent', color: '#EF4444' },
];

export const AgentWorkbenchPage: React.FC = () => {
  const { t } = useLanguage();
  const [query, setQuery] = useState('');
  const [result, setResult] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [expandedTasks, setExpandedTasks] = useState<Set<string>>(new Set());

  const handleQuery = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const res = await api.commanderQuery(query);
      setResult(res);
    } finally {
      setLoading(false);
    }
  };

  const toggleTask = (id: string) => {
    setExpandedTasks(prev => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id); else next.add(id);
      return next;
    });
  };

  return (
    <div>
      <div className="page-header">
        <h1><Bot size={24} style={{ verticalAlign: 'middle', marginRight: 8 }} />{t('Agent Workbench', 'ಏಜೆಂಟ್ ವರ್ಕ್‌ಬೆಂಚ್')}</h1>
        <p>{t('Multi-agent orchestration — Commander coordinates task execution across specialized agents.', 'ಮಲ್ಟಿ-ಏಜೆಂಟ್ ಆರ್ಕೆಸ್ಟ್ರೇಶನ್ — ಕಮಾಂಡರ್ ವಿಶೇಷ ಏಜೆಂಟ್‌ಗಳಾದ್ಯಂತ ಕಾರ್ಯ ನಿರ್ವಹಣೆಯನ್ನು ಸಂಯೋಜಿಸುತ್ತದೆ.')}</p>
      </div>

      <div className="row" style={{ gap: 16, marginBottom: 24 }}>
        {AGENTS.map(a => (
          <div key={a.id} className="card" style={{ flex: 1, textAlign: 'center', padding: 16 }}>
            <Activity size={24} color={a.color} style={{ marginBottom: 8 }} />
            <div style={{ fontSize: 13, fontWeight: 600 }}>{a.label}</div>
            <div style={{ fontSize: 11, color: 'var(--text-muted)' }}>{a.id}</div>
          </div>
        ))}
      </div>

      <div className="card" style={{ marginBottom: 24 }}>
        <div className="flex" style={{ gap: 8, alignItems: 'center' }}>
          <input
            className="input flex-1"
            value={query}
            onChange={e => setQuery(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleQuery()}
            placeholder={t('Ask the Commander...', 'ಕಮಾಂಡರ್‌ನನ್ನು ಕೇಳಿ...')}
          />
          <button className="btn btn-primary" onClick={handleQuery} disabled={loading}>
            <Send size={16} /> {t('Execute', 'ನಿರ್ವಹಿಸು')}
          </button>
        </div>
      </div>

      {loading && (
        <div className="card" style={{ textAlign: 'center', padding: 32 }}>
          <div className="spinner" style={{ width: 32, height: 32, border: '3px solid var(--border)', borderTopColor: 'var(--primary)', borderRadius: '50%', animation: 'spin 0.8s linear infinite', margin: '0 auto 12px' }} />
          <p style={{ color: 'var(--text-muted)' }}>{t('Agents are working...', 'ಏಜೆಂಟ್‌ಗಳು ಕಾರ್ಯನಿರ್ವಹಿಸುತ್ತಿವೆ...')}</p>
        </div>
      )}

      {result && (
        <div className="card">
          <div className="flex justify-between" style={{ marginBottom: 16 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600 }}>
              {t('Mission', 'ಮಿಷನ್')}: {result.mission_id?.slice(0, 8)}...
            </h3>
            <span className={`badge ${result.status === 'completed' ? 'badge-info' : 'badge-high'}`}>
              {result.status}
            </span>
          </div>
          <p style={{ color: 'var(--text-secondary)', fontSize: 14, marginBottom: 16 }}>{result.summary}</p>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {result.tasks?.map((task: any) => {
              const expanded = expandedTasks.has(task.task_id);
              const agent = AGENTS.find(a => a.id === task.agent);
              return (
                <div key={task.task_id} className="card" style={{ padding: '12px 16px', cursor: 'pointer' }} onClick={() => toggleTask(task.task_id)}>
                  <div className="flex justify-between" style={{ alignItems: 'center' }}>
                    <div className="flex" style={{ gap: 8, alignItems: 'center' }}>
                      {task.status === 'completed' ? <CheckCircle size={18} color="#22C55E" /> : task.status === 'running' ? <Clock size={18} color="#F59E0B" /> : <XCircle size={18} color="#EF4444" />}
                      <span style={{ fontWeight: 500 }}>{agent?.label || task.agent}</span>
                    </div>
                    {expanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                  </div>
                  {expanded && (
                    <div style={{ marginTop: 12, paddingTop: 12, borderTop: '1px solid var(--border)' }}>
                      <pre style={{ fontSize: 13, color: 'var(--text-secondary)', whiteSpace: 'pre-wrap', marginBottom: 8 }}>{task.result || task.status}</pre>
                      {task.evidence?.length > 0 && (
                        <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>
                          {task.evidence.map((ev: any, i: number) => (
                            <div key={i}>#{ev.evidence_id?.slice(0, 6)} — {ev.evidence_type} ({ev.source_table})</div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      )}

      <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
    </div>
  );
};
