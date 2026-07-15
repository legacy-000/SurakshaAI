import React, { useState, useEffect } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { api } from '../services/api';
import { Plus, X, Users, UserPlus, UserMinus, AlertTriangle, Clock, Shield } from 'lucide-react';
import type { DynamicGroup, GroupMember } from '../types';

const GROUP_TYPES = ['TASK_FORCE', 'STRIKE_TEAM', 'SURVEILLANCE_TEAM', 'JOINT_PATROL'];

export const GroupManagerPage: React.FC = () => {
  const { t } = useLanguage();
  const userStr = localStorage.getItem('user_context');
  const userCtx = userStr ? JSON.parse(userStr) : null;
  const employeeId = Number(userCtx?.user_id?.replace(/\D/g, '') || 1);

  const [groups, setGroups] = useState<DynamicGroup[]>([]);
  const [loading, setLoading] = useState(true);
  const [showCreate, setShowCreate] = useState(false);
  const [createForm, setCreateForm] = useState({ group_name: '', group_type: 'TASK_FORCE', description: '', case_ids: '', dissolve_hours: '48' });
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [members, setMembers] = useState<GroupMember[]>([]);
  const [addMember, setAddMember] = useState('');
  const [editGroupId, setEditGroupId] = useState<string | null>(null);
  const [editForm, setEditForm] = useState({ group_name: '', description: '' });

  useEffect(() => { api.listDynamicGroups().then(g => { setGroups(g); setLoading(false); }); }, []);

  const loadMembers = async (gid: string) => {
    if (expandedId === gid) { setExpandedId(null); return; }
    setExpandedId(gid);
    const m = await api.listGroupMembers(gid);
    setMembers(m);
    const g = groups.find(x => x.group_id === gid);
    if (g) setEditForm({ group_name: g.group_name, description: g.description || '' });
  };

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!createForm.group_name) return;
    const caseIds = createForm.case_ids.split(',').map(s => Number(s.trim())).filter(Boolean);
    const dissolveH = Number(createForm.dissolve_hours) || 48;
    await api.createDynamicGroup(createForm.group_name, createForm.group_type, employeeId, caseIds, dissolveH, createForm.description);
    setShowCreate(false);
    setCreateForm({ group_name: '', group_type: 'TASK_FORCE', description: '', case_ids: '', dissolve_hours: '48' });
    setGroups(await api.listDynamicGroups());
  };

  const handleDissolve = async (gid: string) => {
    if (!window.confirm(t('Dissolve this group?', 'ಈ ಗುಂಪನ್ನು ವಿಸರ್ಜಿಸುವುದೇ?'))) return;
    await api.dissolveGroup(gid);
    setGroups(prev => prev.map(g => g.group_id === gid ? { ...g, status: 'dissolved' } : g));
  };

  const handleAddMember = async () => {
    if (!addMember || !expandedId) return;
    await api.addGroupMember(expandedId, Number(addMember), 'member');
    setAddMember('');
    const m = await api.listGroupMembers(expandedId);
    setMembers(m);
  };

  const handleRemoveMember = async (empId: number) => {
    if (!expandedId) return;
    await api.removeGroupMember(expandedId, empId);
    const m = await api.listGroupMembers(expandedId);
    setMembers(m);
  };

  const handleEdit = async () => {
    if (!editGroupId) return;
    // ponytail: update group name/desc via group manager (backend supports dissolve but not partial update yet)
    setEditGroupId(null);
  };

  return (
    <div>
      <div className="page-header flex justify-between items-center">
        <div>
          <h1>{t('Group Manager', 'ಗುಂಪು ನಿರ್ವಾಹಕ')}</h1>
          <p>{t('Task forces, strike teams, and surveillance teams', 'ಕಾರ್ಯಪಡೆಗಳು, ಸ್ಟ್ರೈಕ್ ತಂಡಗಳು ಮತ್ತು ಕಣ್ಗಾವಲು ತಂಡಗಳು')}</p>
        </div>
        <button className="btn btn-primary btn-sm" onClick={() => setShowCreate(true)}><Plus size={16} /> {t('Create Group', 'ಗುಂಪು ರಚಿಸಿ')}</button>
      </div>

      {showCreate && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-header flex justify-between items-center">
            <h3>{t('Create Dynamic Group', 'ಡೈನಾಮಿಕ್ ಗುಂಪು ರಚಿಸಿ')}</h3>
            <button className="btn btn-ghost btn-sm" onClick={() => setShowCreate(false)}><X size={18} /></button>
          </div>
          <form onSubmit={handleCreate}>
            <div className="grid-2">
              <div className="form-group">
                <label>{t('Group Name', 'ಗುಂಪಿನ ಹೆಸರು')}</label>
                <input className="input" value={createForm.group_name} onChange={e => setCreateForm(f => ({ ...f, group_name: e.target.value }))} required />
              </div>
              <div className="form-group">
                <label>{t('Type', 'ಪ್ರಕಾರ')}</label>
                <select className="input" value={createForm.group_type} onChange={e => setCreateForm(f => ({ ...f, group_type: e.target.value }))}>
                  {GROUP_TYPES.map(gt => <option key={gt} value={gt}>{gt.replace(/_/g, ' ')}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>{t('Linked Case IDs', 'ಲಿಂಕ್ ಮಾಡಿದ ಪ್ರಕರಣ ID')}</label>
                <input className="input" value={createForm.case_ids} placeholder="e.g. 101, 102" />
              </div>
              <div className="form-group">
                <label>{t('Auto-dissolve (hours)', 'ಸ್ವಯಂ ವಿಸರ್ಜನೆ (ಗಂಟೆಗಳು)')}</label>
                <input className="input" type="number" value={createForm.dissolve_hours} onChange={e => setCreateForm(f => ({ ...f, dissolve_hours: e.target.value }))} />
              </div>
            </div>
            <div className="form-group">
              <label>{t('Description', 'ವಿವರಣೆ')}</label>
              <textarea className="input" style={{ minHeight: 60 }} value={createForm.description} onChange={e => setCreateForm(f => ({ ...f, description: e.target.value }))} />
            </div>
            <div className="flex gap-4" style={{ justifyContent: 'flex-end' }}>
              <button type="button" className="btn btn-secondary" onClick={() => setShowCreate(false)}>{t('Cancel', 'ರದ್ದುಮಾಡಿ')}</button>
              <button type="submit" className="btn btn-primary"><Users size={16} /> {t('Create', 'ರಚಿಸಿ')}</button>
            </div>
          </form>
        </div>
      )}

      {loading ? (
        <div className="card" style={{ padding: 48, textAlign: 'center' }}><p className="text-muted">{t('Loading...', 'ಲೋಡ್ ಆಗುತ್ತಿದೆ...')}</p></div>
      ) : groups.length === 0 ? (
        <div className="card" style={{ padding: 48, textAlign: 'center' }}>
          <Users size={48} style={{ color: 'var(--text-muted)', marginBottom: 16 }} />
          <p className="text-muted">{t('No groups created yet', 'ಇನ್ನೂ ಯಾವುದೇ ಗುಂಪುಗಳನ್ನು ರಚಿಸಲಾಗಿಲ್ಲ')}</p>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
          {groups.map(g => (
            <div key={g.group_id} className="card" style={{ borderLeft: `4px solid ${g.status === 'active' ? 'var(--success)' : 'var(--text-muted)'}` }}>
              <div className="flex justify-between items-center" style={{ cursor: 'pointer' }} onClick={() => loadMembers(g.group_id)}>
                <div>
                  <div className="flex items-center gap-2">
                    <span style={{ fontWeight: 600, fontSize: 14 }}>{g.group_name}</span>
                    <span className="badge" style={{ fontSize: 10 }}>{g.group_type.replace(/_/g, ' ')}</span>
                    <span className={`badge ${g.status === 'active' ? 'badge-low' : 'badge-moderate'}`} style={{ fontSize: 10 }}>{g.status}</span>
                  </div>
                  {g.description && <p className="text-sm text-muted" style={{ marginTop: 2 }}>{g.description}</p>}
                  <div className="text-xs text-muted" style={{ marginTop: 4 }}>
                    {t('Lead', 'ನಾಯಕ')}: #{g.lead_employee_id} · {t('Cases', 'ಪ್ರಕರಣಗಳು')}: {g.linked_case_ids.length} · {t('Created', 'ರಚಿಸಲಾಗಿದೆ')}: {new Date(g.created_at).toLocaleDateString('en-IN')}
                    {g.dissolve_at ? ` · ${t('Dissolves', 'ವಿಸರ್ಜನೆ')}: ${new Date(g.dissolve_at).toLocaleDateString('en-IN')}` : ''}
                  </div>
                </div>
                <div className="flex gap-2 items-center">
                  {g.status === 'active' && (
                    <button className="btn btn-ghost btn-sm" onClick={e => { e.stopPropagation(); handleDissolve(g.group_id); }}>
                      <X size={14} /> {t('Dissolve', 'ವಿಸರ್ಜಿಸಿ')}
                    </button>
                  )}
                  <Shield size={16} style={{ color: 'var(--text-muted)' }} />
                </div>
              </div>

              {expandedId === g.group_id && (
                <div style={{ marginTop: 16, paddingTop: 16, borderTop: '1px solid var(--border)' }}>
                  <div className="flex gap-2" style={{ marginBottom: 12 }}>
                    <input className="input" style={{ width: 200 }} type="number" value={addMember} onChange={e => setAddMember(e.target.value)}
                      placeholder={t('Employee ID...', 'ಉದ್ಯೋಗಿ ID...')} />
                    <button className="btn btn-primary btn-sm" onClick={handleAddMember}><UserPlus size={14} /> {t('Add', 'ಸೇರಿಸಿ')}</button>
                  </div>
                  {members.length === 0 ? (
                    <p className="text-xs text-muted">{t('No members', 'ಯಾವುದೇ ಸದಸ್ಯರಿಲ್ಲ')}</p>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 4 }}>
                      {members.map(m => (
                        <div key={m.employee_id} className="flex justify-between items-center" style={{ padding: '6px 8px', borderRadius: 4, background: 'var(--bg-hover)' }}>
                          <div className="flex items-center gap-2">
                            <span style={{ fontWeight: 600, fontSize: 13 }}>#{m.employee_id}</span>
                            {m.rank && <span className="text-xs text-muted">{m.rank}</span>}
                            <span className="badge" style={{ fontSize: 10 }}>{m.role_in_group}</span>
                            {m.joined_at && <span className="text-xs text-muted">{new Date(m.joined_at).toLocaleDateString('en-IN')}</span>}
                          </div>
                          <button className="btn btn-ghost btn-icon btn-sm" onClick={() => handleRemoveMember(m.employee_id)} title={t('Remove', 'ತೆಗೆದುಹಾಕಿ')}>
                            <UserMinus size={14} />
                          </button>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
