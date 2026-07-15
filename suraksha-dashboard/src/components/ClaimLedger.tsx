import React, { useState } from 'react';
import { Shield, AlertTriangle, CheckCircle, HelpCircle, X } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

export interface Claim {
  id: string;
  statement: string;
  classification: 'DATABASE_FACT' | 'COMPUTED_FINDING' | 'MODEL_PREDICTION' | 'MODEL_HYPOTHESIS';
  producer: string;
  model_version?: string;
  evidence_refs: string[];
  confidence?: number;
  confidence_label?: string;
  validation_status: 'Accepted' | 'Under Review' | 'Disputed' | 'Rejected';
}

const CLASS_STYLES: Record<string, { color: string; bg: string; label: string }> = {
  DATABASE_FACT: { color: '#3B82F6', bg: 'rgba(59,130,246,0.12)', label: 'Database Fact' },
  COMPUTED_FINDING: { color: '#F59E0B', bg: 'rgba(245,158,11,0.12)', label: 'Computed Finding' },
  MODEL_PREDICTION: { color: '#8B5CF6', bg: 'rgba(139,92,246,0.12)', label: 'Model Prediction' },
  MODEL_HYPOTHESIS: { color: '#EF4444', bg: 'rgba(239,68,68,0.12)', label: 'Model Hypothesis' },
};

const VALID_STYLES: Record<string, { color: string; bg: string }> = {
  Accepted: { color: '#22C55E', bg: 'rgba(34,197,94,0.12)' },
  'Under Review': { color: '#F59E0B', bg: 'rgba(245,158,11,0.12)' },
  Disputed: { color: '#EF4444', bg: 'rgba(239,68,68,0.12)' },
  Rejected: { color: '#6B7280', bg: 'rgba(107,114,128,0.12)' },
};

const SAMPLE_CLAIMS: Claim[] = [
  { id: 'c1', statement: 'FIR registered on 2026-03-15 at City Police Station', classification: 'DATABASE_FACT', producer: 'CaseMaster', evidence_refs: ['CaseMaster:10443...001'], validation_status: 'Accepted' },
  { id: 'c2', statement: 'Incident location within 500m of 2 prior theft cases', classification: 'COMPUTED_FINDING', producer: 'Geospatial Agent', model_version: 'v1.2', evidence_refs: ['CaseMaster:10443...001', 'Hotspot:cluster_3'], confidence: 0.89, validation_status: 'Under Review' },
  { id: 'c3', statement: 'Offender has ELEVATED recidivism risk', classification: 'MODEL_PREDICTION', producer: 'Priority Score Engine', model_version: '1.0.0', evidence_refs: ['PriorityScore:INV001'], confidence: 0.76, confidence_label: 'High', validation_status: 'Under Review' },
  { id: 'c4', statement: 'Unknown third party may be involved based on evidence gaps', classification: 'MODEL_HYPOTHESIS', producer: 'InvestigationAI', model_version: 'claude-sonnet-4-6', evidence_refs: ['Evidence:missing_weapon_report'], confidence: 0.35, validation_status: 'Disputed' },
];

interface Props {
  claims?: Claim[];
  caseId?: string;
  onClose?: () => void;
}

export const ClaimLedger: React.FC<Props> = ({ claims = SAMPLE_CLAIMS, caseId = '104430006202600001', onClose }) => {
  const { t } = useLanguage();
  const [statusFilter, setStatusFilter] = useState<string>('all');
  const [classFilter, setClassFilter] = useState<string>('all');

  const filtered = claims.filter(c => {
    if (statusFilter !== 'all' && c.validation_status !== statusFilter) return false;
    if (classFilter !== 'all' && c.classification !== classFilter) return false;
    return true;
  });

  // Check for contradictions
  const contradictions: { a: Claim; b: Claim }[] = [];
  for (let i = 0; i < claims.length; i++) {
    for (let j = i + 1; j < claims.length; j++) {
      if (claims[i].classification === 'DATABASE_FACT' && claims[j].classification === 'DATABASE_FACT') continue;
      // Simple contradiction heuristic: overlapping evidence refs with different conclusions
      const sharedRefs = claims[i].evidence_refs.filter(r => claims[j].evidence_refs.includes(r));
      if (sharedRefs.length > 0 && claims[i].confidence && claims[j].confidence &&
          Math.abs(claims[i].confidence! - claims[j].confidence!) > 0.5) {
        contradictions.push({ a: claims[i], b: claims[j] });
      }
    }
  }

  return (
    <div className="card">
      <div className="card-header flex justify-between items-center">
        <span className="flex items-center gap-2"><Shield size={20} /> {t('Claim Ledger', 'ಹಕ್ಕು ಪಂಜಿ')}</span>
        {onClose && <button className="btn btn-ghost btn-icon" onClick={onClose}><X size={18} /></button>}
      </div>
      <p className="text-xs text-muted" style={{ marginBottom: 16 }}>{t('Case', 'ಪ್ರಕರಣ')}: {caseId}</p>

      {contradictions.length > 0 && (
        <div style={{ marginBottom: 16, padding: 12, background: 'rgba(239,68,68,0.08)', borderRadius: 8, border: '1px solid rgba(239,68,68,0.3)' }}>
          <div className="flex items-center gap-2" style={{ marginBottom: 8, color: 'var(--danger)', fontWeight: 600, fontSize: 14 }}>
            <AlertTriangle size={16} /> {t('Contradictions Detected', 'ವಿರೋಧಾಭಾಸಗಳು ಪತ್ತೆಯಾಗಿವೆ')}
          </div>
          {contradictions.map((ct, i) => (
            <div key={i} style={{ fontSize: 13, marginBottom: 8, padding: 8, background: 'rgba(255,255,255,0.05)', borderRadius: 6 }}>
              <div>⚠️ "{ct.a.statement}" <span className="text-xs text-muted">({ct.a.confidence})</span></div>
              <div style={{ marginLeft: 16 }}>↔ "{ct.b.statement}" <span className="text-xs text-muted">({ct.b.confidence})</span></div>
            </div>
          ))}
        </div>
      )}

      <div className="flex gap-2" style={{ marginBottom: 16, flexWrap: 'wrap' }}>
        <select className="input" style={{ width: 'auto', fontSize: 12, padding: '4px 8px' }} value={statusFilter} onChange={e => setStatusFilter(e.target.value)}>
          <option value="all">{t('All Statuses', 'ಎಲ್ಲಾ ಸ್ಥಿತಿಗಳು')}</option>
          <option value="Accepted">{t('Accepted', 'ಸ್ವೀಕರಿಸಲಾಗಿದೆ')}</option>
          <option value="Under Review">{t('Under Review', 'ಪರಿಶೀಲನೆಯಲ್ಲಿದೆ')}</option>
          <option value="Disputed">{t('Disputed', 'ವಿವಾದಿತ')}</option>
          <option value="Rejected">{t('Rejected', 'ತಿರಸ್ಕರಿಸಲಾಗಿದೆ')}</option>
        </select>
        <select className="input" style={{ width: 'auto', fontSize: 12, padding: '4px 8px' }} value={classFilter} onChange={e => setClassFilter(e.target.value)}>
          <option value="all">{t('All Types', 'ಎಲ್ಲಾ ಪ್ರಕಾರಗಳು')}</option>
          <option value="DATABASE_FACT">{t('Database Fact', 'ಡೇಟಾಬೇಸ್ ಫ್ಯಾಕ್ಟ್')}</option>
          <option value="COMPUTED_FINDING">{t('Computed Finding', 'ಲೆಕ್ಕಾಚಾರದ ಸಂಶೋಧನೆ')}</option>
          <option value="MODEL_PREDICTION">{t('Model Prediction', 'ಮಾದರಿ ಮುನ್ಸೂಚನೆ')}</option>
          <option value="MODEL_HYPOTHESIS">{t('Model Hypothesis', 'ಮಾದರಿ ಊಹೆ')}</option>
        </select>
      </div>

      <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
        {filtered.map(claim => {
          const cs = CLASS_STYLES[claim.classification];
          const vs = VALID_STYLES[claim.validation_status];
          return (
            <div key={claim.id} style={{
              padding: 12, borderRadius: 8, border: '1px solid var(--border)',
              borderLeft: `4px solid ${cs.color}`
            }}>
              <div className="flex justify-between items-start" style={{ marginBottom: 6 }}>
                <div className="flex gap-2">
                  <span style={{ background: cs.bg, color: cs.color, padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600 }}>
                    {cs.label}
                  </span>
                  <span style={{ background: vs.bg, color: vs.color, padding: '2px 8px', borderRadius: 4, fontSize: 11, fontWeight: 600 }}>
                    {claim.validation_status}
                  </span>
                </div>
                {claim.confidence && (
                  <span className="text-xs text-muted">{claim.confidence_label || `${Math.round(claim.confidence * 100)}%`}</span>
                )}
              </div>
              <p style={{ fontSize: 14, color: 'var(--text-secondary)', marginBottom: 4 }}>{claim.statement}</p>
              <div className="flex gap-2 items-center text-xs text-muted">
                <span>{t('Producer', 'ನಿರ್ಮಾಪಕ')}: {claim.producer}</span>
                {claim.model_version && <span>| {t('v', 'ಆವೃತ್ತಿ')}: {claim.model_version}</span>}
              </div>
              {claim.evidence_refs.length > 0 && (
                <div className="flex gap-1" style={{ marginTop: 6, flexWrap: 'wrap' }}>
                  {claim.evidence_refs.map(ref => (
                    <span key={ref} className="badge badge-info" style={{ fontSize: 10, padding: '2px 6px' }}>{ref}</span>
                  ))}
                </div>
              )}
              <div className="flex gap-2" style={{ marginTop: 8 }}>
                <button className="btn btn-ghost btn-sm" style={{ fontSize: 11 }}>
                  <CheckCircle size={12} /> {t('Accept', 'ಸ್ವೀಕರಿಸಿ')}
                </button>
                <button className="btn btn-ghost btn-sm" style={{ fontSize: 11 }}>
                  <AlertTriangle size={12} /> {t('Flag as contradiction', 'ವಿರೋಧಾಭಾಸ ಎಂದು ಗುರುತಿಸಿ')}
                </button>
                <button className="btn btn-ghost btn-sm" style={{ fontSize: 11 }}>
                  <HelpCircle size={12} /> {t('Add note', 'ಟಿಪ್ಪಣಿ ಸೇರಿಸಿ')}
                </button>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};
