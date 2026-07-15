import React, { useState, useEffect } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { api } from '../services/api';
import { GitPullRequest, Plus, CheckCircle, XCircle, Clock, Send, AlertTriangle, Edit3 } from 'lucide-react';
import type { CoordinationRequest } from '../types';

const STATUS_COLORS: Record<string, string> = {
  pending: 'var(--warning)', approved: 'var(--success)', rejected: 'var(--danger)', withdrawn: 'var(--text-muted)'
};

export const CoordinationPage: React.FC = () => {
  const { t } = useLanguage();
  const userStr = localStorage.getItem('user_context');
  const userCtx = userStr ? JSON.parse(userStr) : null;
  const employeeId = Number(userCtx?.user_id?.replace(/\D/g, '') || 1);

  const [requests, setRequests] = useState<CoordinationRequest[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<string>('all');
  const [showForm, setShowForm] = useState(false);
  const [form, setForm] = useState({ request_type: 'JOINT_OPERATION', target_unit_id: '', priority: 'HIGH', description: '', linked_case_ids: '' });
  const [updating, setUpdating] = useState<string | null>(null);

  useEffect(() => { api.listCoordination().then(r => { setRequests(r); setLoading(false); }); }, []);

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!form.target_unit_id || !form.description) return;
    const caseIds = form.linked_case_ids.split(',').map(s => Number(s.trim())).filter(Boolean);
    await api.createCoordination(form.request_type, Number(form.target_unit_id), form.priority, form.description, caseIds);
    setShowForm(false);
    setForm({ request_type: 'JOINT_OPERATION', target_unit_id: '', priority: 'HIGH', description: '', linked_case_ids: '' });
    api.listCoordination().then(setRequests);
  };

  const handleUpdate = async (id: string, status: string) => {
    setUpdating(id);
    await api.updateCoordination(id, status, employeeId);
    api.listCoordination().then(r => { setRequests(r); setUpdating(null); });
  };

  const filtered = filter === 'all' ? requests : requests.filter(r => r.status === filter);

  return (
    <div>
      <div className="page-header flex justify-between items-center">
        <div>
          <h1>{t('Coordination', 'ಸಮನ್ವಯ')}</h1>
          <p>{t('Inter-station coordination requests', 'ಅಂತರ-ಠಾಣೆ ಸಮನ್ವಯ ವಿನಂತಿಗಳು')}</p>
        </div>
        <button className="btn btn-primary btn-sm" onClick={() => setShowForm(true)}>
          <Plus size={16} /> {t('New Request', 'ಹೊಸ ವಿನಂತಿ')}
        </button>
      </div>

      {showForm && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-header flex justify-between items-center">
            <h3>{t('New Coordination Request', 'ಹೊಸ ಸಮನ್ವಯ ವಿನಂತಿ')}</h3>
            <button className="btn btn-ghost btn-sm" onClick={() => setShowForm(false)}><XCircle size={18} /></button>
          </div>
          <form onSubmit={handleCreate}>
            <div className="grid-2">
              <div className="form-group">
                <label>{t('Request Type', 'ವಿನಂತಿ ಪ್ರಕಾರ')}</label>
                <select className="input" value={form.request_type} onChange={e => setForm(f => ({ ...f, request_type: e.target.value }))}>
                  <option value="JOINT_OPERATION">{t('Joint Operation', 'ಜಂಟಿ ಕಾರ್ಯಾಚರಣೆ')}</option>
                  <option value="INFORMATION_SHARING">{t('Information Sharing', 'ಮಾಹಿತಿ ಹಂಚಿಕೆ')}</option>
                  <option value="RESOURCE_REQUEST">{t('Resource Request', 'ಸಂಪನ್ಮೂಲ ವಿನಂತಿ')}</option>
                  <option value="WITNESS_TRANSFER">{t('Witness Transfer', 'ಸಾಕ್ಷಿ ವರ್ಗಾವಣೆ')}</option>
                </select>
              </div>
              <div className="form-group">
                <label>{t('Target Unit ID', 'ಗುರಿ ಘಟಕ ID')}</label>
                <input className="input" type="number" value={form.target_unit_id} onChange={e => setForm(f => ({ ...f, target_unit_id: e.target.value }))} required />
              </div>
              <div className="form-group">
                <label>{t('Priority', 'ಆದ್ಯತೆ')}</label>
                <select className="input" value={form.priority} onChange={e => setForm(f => ({ ...f, priority: e.target.value }))}>
                  <option value="LOW">{t('Low', 'ಕಡಿಮೆ')}</option>
                  <option value="HIGH">{t('High', 'ಹೆಚ್ಚಿನ')}</option>
                  <option value="CRITICAL">{t('Critical', 'ನಿರ್ಣಾಯಕ')}</option>
                </select>
              </div>
              <div className="form-group">
                <label>{t('Linked Case IDs', 'ಲಿಂಕ್ ಮಾಡಿದ ಪ್ರಕರಣ ID')}</label>
                <input className="input" value={form.linked_case_ids} placeholder="e.g. 101, 102" />
              </div>
            </div>
            <div className="form-group">
              <label>{t('Description', 'ವಿವರಣೆ')}</label>
              <textarea className="input" style={{ minHeight: 80 }} value={form.description} onChange={e => setForm(f => ({ ...f, description: e.target.value }))} required />
            </div>
            <div className="flex gap-4" style={{ justifyContent: 'flex-end' }}>
              <button type="button" className="btn btn-secondary" onClick={() => setShowForm(false)}>{t('Cancel', 'ರದ್ದುಮಾಡಿ')}</button>
              <button type="submit" className="btn btn-primary"><Send size={16} /> {t('Send Request', 'ವಿನಂತಿ ಕಳುಹಿಸಿ')}</button>
            </div>
          </form>
        </div>
      )}

      <div className="tabs" style={{ marginBottom: 16 }}>
        <button className={`tab ${filter === 'all' ? 'active' : ''}`} onClick={() => setFilter('all')}>{t('All', 'ಎಲ್ಲಾ')}</button>
        <button className={`tab ${filter === 'pending' ? 'active' : ''}`} onClick={() => setFilter('pending')}>{t('Pending', 'ಬಾಕಿ')}</button>
        <button className={`tab ${filter === 'approved' ? 'active' : ''}`} onClick={() => setFilter('approved')}>{t('Approved', 'ಅನುಮೋದಿಸಲಾಗಿದೆ')}</button>
        <button className={`tab ${filter === 'rejected' ? 'active' : ''}`} onClick={() => setFilter('rejected')}>{t('Rejected', 'ತಿರಸ್ಕರಿಸಲಾಗಿದೆ')}</button>
      </div>

      {loading ? (
        <div className="card" style={{ padding: 48, textAlign: 'center' }}><p className="text-muted">{t('Loading...', 'ಲೋಡ್ ಆಗುತ್ತಿದೆ...')}</p></div>
      ) : filtered.length === 0 ? (
        <div className="card" style={{ padding: 48, textAlign: 'center' }}>
          <GitPullRequest size={48} style={{ color: 'var(--text-muted)', marginBottom: 16 }} />
          <p className="text-muted">{t('No coordination requests', 'ಯಾವುದೇ ಸಮನ್ವಯ ವಿನಂತಿಗಳಿಲ್ಲ')}</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {filtered.map(req => (
            <div key={req.request_id} className="card" style={{ borderLeft: `4px solid ${STATUS_COLORS[req.status] || 'var(--text-muted)'}` }}>
              <div className="flex justify-between items-center">
                <div style={{ flex: 1 }}>
                  <div className="flex items-center gap-2" style={{ marginBottom: 4 }}>
                    <span style={{ fontWeight: 600, fontSize: 14 }}>{req.request_type.replace(/_/g, ' ')}</span>
                    <span className={`badge ${req.priority === 'CRITICAL' ? 'badge-elevated' : req.priority === 'HIGH' ? 'badge-moderate' : 'badge-low'}`} style={{ fontSize: 10 }}>{req.priority}</span>
                    <span className="badge" style={{ fontSize: 10, background: STATUS_COLORS[req.status], color: '#fff' }}>{req.status}</span>
                  </div>
                  <p className="text-sm" style={{ color: 'var(--text-secondary)', marginBottom: 4 }}>{req.description}</p>
                  <div className="text-xs text-muted">
                    {t('From', 'ರಿಂದ')}: {req.requesting_unit_id} → {t('To', 'ಗೆ')}: {req.target_unit_id}
                    {' · '}{t('Created', 'ರಚಿಸಲಾಗಿದೆ')}: {new Date(req.created_at).toLocaleDateString('en-IN')}
                    {req.responded_at ? ` · ${t('Responded', 'ಪ್ರತಿಕ್ರಿಯಿಸಲಾಗಿದೆ')}: ${new Date(req.responded_at).toLocaleDateString('en-IN')}` : ''}
                  </div>
                  {req.linked_case_ids.length > 0 && (
                    <div className="flex gap-2" style={{ marginTop: 4 }}>
                      {req.linked_case_ids.map(cid => <span key={cid} className="badge badge-info" style={{ fontSize: 10 }}>#{cid}</span>)}
                    </div>
                  )}
                </div>
                {req.status === 'pending' && (
                  <div className="flex gap-2" style={{ marginLeft: 16 }}>
                    <button className="btn btn-primary btn-sm" onClick={() => handleUpdate(req.request_id, 'approved')} disabled={updating === req.request_id}>
                      <CheckCircle size={14} /> {t('Approve', 'ಅನುಮೋದಿಸಿ')}
                    </button>
                    <button className="btn btn-secondary btn-sm" onClick={() => handleUpdate(req.request_id, 'rejected')} disabled={updating === req.request_id}>
                      <XCircle size={14} /> {t('Reject', 'ತಿರಸ್ಕರಿಸಿ')}
                    </button>
                  </div>
                )}
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
