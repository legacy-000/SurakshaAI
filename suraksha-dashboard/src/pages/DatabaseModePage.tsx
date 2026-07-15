import React, { useState } from 'react';
import { CheckCircle, AlertTriangle, HelpCircle, Database, Filter } from 'lucide-react';
import { api } from '../services/api';
import { useLanguage } from '../context/LanguageContext';

const CONFIDENCE_COLORS: Record<string, string> = {
  high: '#22C55E', medium: '#F59E0B', low: '#EF4444', insufficient_data: '#6B7280',
};

const DatabaseModePage: React.FC = () => {
  const { t } = useLanguage();
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState('');
  const [drawerOpen, setDrawerOpen] = useState(true);
  const [filtersExpanded, setFiltersExpanded] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    setLoading(true);
    setError('');
    setResult(null);
    try {
      const res = await api.chatQuery(query);
      setResult(res);
    } catch (err: any) {
      setError(err.message || 'Query failed');
    } finally {
      setLoading(false);
    }
  };

  const toolParams = result?.tool_params || {};
  const filterChips = toolParams?.where?.map((w: any) => `${w.column} ${w.operator} ${w.value}`) || [];

  return (
    <div>
      <div className="page-header">
        <h1><Database size={24} style={{ verticalAlign: 'middle', marginRight: 8 }} />{t('Database Mode', 'ಡೇಟಾಬೇಸ್ ಮೋಡ್')}</h1>
        <p>{t('View generated ZCQL, tool parameters, evidence, and data-quality warnings.', 'ಉತ್ಪತ್ತಿಯಾದ ZCQL, ಟೂಲ್ ಪ್ಯಾರಾಮೀಟರ್‌ಗಳು, ಸಾಕ್ಷ್ಯ ಮತ್ತು ಡೇಟಾ ಗುಣಮಟ್ಟ ಎಚ್ಚರಿಕೆಗಳನ್ನು ವೀಕ್ಷಿಸಿ.')}</p>
      </div>

      <div className="card" style={{ marginBottom: 24 }}>
        <form onSubmit={handleSubmit} style={{ display: 'flex', gap: 12 }}>
          <input type="text" value={query} onChange={e => setQuery(e.target.value)}
            placeholder={t('Ask a question about crime data...', 'ಅಪರಾಧ ಡೇಟಾ ಕುರಿತು ಪ್ರಶ್ನೆ ಕೇಳಿ...')}
            style={{ flex: 1, padding: '10px 14px', borderRadius: 8, border: '1px solid var(--border)', background: 'var(--bg-card)', color: 'var(--text)' }} />
          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? t('Querying...', 'ಪ್ರಶ್ನಿಸಲಾಗುತ್ತಿದೆ...') : t('Run', 'ಚಲಾಯಿಸು')}
          </button>
        </form>
      </div>

      {error && (
        <div className="card" style={{ borderLeft: '4px solid var(--danger)', marginBottom: 16 }}>
          <p style={{ color: 'var(--danger)' }}>{error}</p>
        </div>
      )}

      {result && (
        <div className="row" style={{ gap: 16 }}>
          <div style={{ flex: 2, minWidth: 0 }}>
            {/* Answer */}
            <div className="card" style={{ marginBottom: 16 }}>
              <div className="card-header flex justify-between">
                <h3>{t('Answer', 'ಉತ್ತರ')}</h3>
                <div className="flex" style={{ gap: 8, alignItems: 'center' }}>
                  {result.confidence_class && (
                    <span style={{ color: CONFIDENCE_COLORS[result.confidence_class] || '#6B7280', fontSize: 12, fontWeight: 600 }}>
                      {result.confidence_class === 'high' && <CheckCircle size={14} style={{ verticalAlign: 'middle', marginRight: 4 }} />}
                      {result.confidence_class === 'medium' && <AlertTriangle size={14} style={{ verticalAlign: 'middle', marginRight: 4 }} />}
                      {result.confidence_class === 'low' && <HelpCircle size={14} style={{ verticalAlign: 'middle', marginRight: 4 }} />}
                      {result.confidence_class}
                    </span>
                  )}
                  {result.grounding_status && (
                    <span className={`badge ${result.grounding_status === 'verified' ? 'badge-info' : 'badge-elevated'}`}>
                      {result.grounding_status}
                    </span>
                  )}
                </div>
              </div>
              <p>{result.content_text}</p>
            </div>

            {/* Data Quality Warnings */}
            {result.data_quality_warnings?.length > 0 && (
              <div className="card" style={{ marginBottom: 16, borderLeft: '4px solid var(--warning)' }}>
                <div className="card-header"><h3>{t('Data Quality Warnings', 'ಡೇಟಾ ಗುಣಮಟ್ಟ ಎಚ್ಚರಿಕೆಗಳು')}</h3></div>
                <ul style={{ margin: 0, paddingLeft: 20 }}>
                  {result.data_quality_warnings.map((w: string, i: number) => (
                    <li key={i} style={{ color: 'var(--warning)', marginBottom: 4 }}>⚠ {w}</li>
                  ))}
                </ul>
              </div>
            )}

            {/* Suggested Follow-ups */}
            {result.suggested_followups?.length > 0 && (
              <div className="card">
                <div className="card-header"><h3>{t('Suggested Follow-ups', 'ಸೂಚಿಸಿದ ಅನುಸರಣೆ')}</h3></div>
                <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {result.suggested_followups.map((f: string, i: number) => (
                    <button key={i} className="btn btn-ghost btn-sm" onClick={() => setQuery(f)}>{f}</button>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div style={{ flex: 1, minWidth: 280 }}>
            {/* Query Plan Drawer */}
            <div className="card" style={{ marginBottom: 16 }}>
              <div className="card-header flex justify-between" style={{ cursor: 'pointer' }} onClick={() => setDrawerOpen(!drawerOpen)}>
                <h3>{t('Query Plan', 'ಕ್ವೆರಿ ಯೋಜನೆ')}</h3>
              </div>
              {drawerOpen && (
                <div style={{ fontSize: 13 }}>
                  {/* Table */}
                  {toolParams.table && (
                    <div style={{ marginBottom: 12 }}>
                      <strong style={{ color: 'var(--text-muted)', fontSize: 11, textTransform: 'uppercase' }}>{t('Table', 'ಟೇಬಲ್')}</strong>
                      <div style={{ marginTop: 4, padding: '6px 10px', background: 'var(--bg-secondary)', borderRadius: 6, fontFamily: 'monospace' }}>{toolParams.table}</div>
                    </div>
                  )}

                  {/* Columns */}
                  {toolParams.columns?.length > 0 && (
                    <div style={{ marginBottom: 12 }}>
                      <strong style={{ color: 'var(--text-muted)', fontSize: 11, textTransform: 'uppercase' }}>{t('Columns', 'ಕಾಲಮ್‌ಗಳು')}</strong>
                      <div style={{ marginTop: 4, display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                        {toolParams.columns.map((c: string, i: number) => (
                          <span key={i} className="badge badge-info">{c}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Filter Chips */}
                  {filterChips.length > 0 && (
                    <div style={{ marginBottom: 12 }}>
                      <div className="flex justify-between" style={{ cursor: 'pointer', alignItems: 'center' }} onClick={() => setFiltersExpanded(!filtersExpanded)}>
                        <strong style={{ color: 'var(--text-muted)', fontSize: 11, textTransform: 'uppercase' }}>
                          <Filter size={12} style={{ verticalAlign: 'middle', marginRight: 4 }} />{t('Filters', 'ಫಿಲ್ಟರ್‌ಗಳು')} ({filterChips.length})
                        </strong>
                      </div>
                      <div style={{ marginTop: 4, display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                        {filterChips.map((f: string, i: number) => (
                          <span key={i} className="badge" style={{ background: 'var(--primary)', color: '#fff' }}>{f}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Limit */}
                  {toolParams.limit && (
                    <div style={{ marginBottom: 12 }}>
                      <strong style={{ color: 'var(--text-muted)', fontSize: 11, textTransform: 'uppercase' }}>{t('Limit', 'ಮಿತಿ')}</strong>
                      <div style={{ marginTop: 4 }}>{toolParams.limit} {t('rows', 'ಸಾಲುಗಳು')}</div>
                    </div>
                  )}

                  {/* Evidence */}
                  {result.evidence_refs?.length > 0 && (
                    <div style={{ marginBottom: 12 }}>
                      <strong style={{ color: 'var(--text-muted)', fontSize: 11, textTransform: 'uppercase' }}>{t('Evidence', 'ಸಾಕ್ಷ್ಯ')}</strong>
                      <div style={{ marginTop: 4, display: 'flex', gap: 4, flexWrap: 'wrap' }}>
                        {result.evidence_refs.map((ev: any, i: number) => (
                          <span key={i} className="badge badge-info">{ev.display_label || `${ev.source_record_count} records`}</span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Raw ZCQL */}
                  {result.sql_text && (
                    <div>
                      <strong style={{ color: 'var(--text-muted)', fontSize: 11, textTransform: 'uppercase' }}>{t('Generated ZCQL', 'ಉತ್ಪತ್ತಿಯಾದ ZCQL')}</strong>
                      <pre style={{ marginTop: 4, padding: 10, background: 'var(--bg-code, #1e1e2e)', color: '#a6e3a1', borderRadius: 6, fontSize: 12, fontFamily: 'monospace', overflowX: 'auto' }}>{result.sql_text}</pre>
                    </div>
                  )}

                  {/* Raw Tool Params */}
                  {Object.keys(toolParams).length > 0 && (
                    <details style={{ marginTop: 12 }}>
                      <summary style={{ color: 'var(--text-muted)', fontSize: 11, cursor: 'pointer', textTransform: 'uppercase' }}>{t('Raw Tool Params', 'ಕಚ್ಚಾ ಟೂಲ್ ಪ್ಯಾರಾಮೀಟರ್‌ಗಳು')}</summary>
                      <pre style={{ marginTop: 4, padding: 10, background: 'var(--bg-code, #1e1e2e)', color: '#89b4fa', borderRadius: 6, fontSize: 11, fontFamily: 'monospace', overflowX: 'auto' }}>{JSON.stringify(toolParams, null, 2)}</pre>
                    </details>
                  )}
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DatabaseModePage;
