import React, { useState, useEffect } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { api } from '../services/api';
import { Shield, AlertTriangle, CheckCircle, UserCheck, Lock, Unlock, Users, X, Plus, Clock } from 'lucide-react';
import type { PermissionCheck, TempPermission, DynamicGroup } from '../types';

const RESOURCE_TYPES = ['CASE', 'ARREST', 'CHARGESHEET', 'MESSAGE', 'OFFENDER'];
const ACTIONS = ['CREATE', 'READ', 'UPDATE', 'APPROVE', 'DELETE', 'EXPORT', 'FORWARD'];
const SCOPES = ['assigned', 'own_case', 'own_station', 'own_district', 'all'];

export const AccessControlPage: React.FC = () => {
  const { t } = useLanguage();
  const userStr = localStorage.getItem('user_context');
  const userCtx = userStr ? JSON.parse(userStr) : null;
  const rank = userCtx?.role_name || 'Investigator';
  const employeeId = Number(userCtx?.user_id?.replace(/\D/g, '') || 1);

  const [permResults, setPermResults] = useState<Record<string, PermissionCheck>>({});
  const [checking, setChecking] = useState(false);
  const [delegations, setDelegations] = useState<TempPermission[]>([]);
  const [myGroups, setMyGroups] = useState<DynamicGroup[]>([]);
  const [emergency, setEmergency] = useState(false);
  const [showDelegate, setShowDelegate] = useState(false);
  const [delForm, setDelForm] = useState({ grantee: '', permission: 'APPROVE_CHARGESHEET', scope: 'own_station', reason: '' });

  useEffect(() => { api.listDelegations(undefined, employeeId).then(setDelegations); api.listMyGroups(employeeId).then(setMyGroups); api.getEmergencyStatus().then(setEmergency); }, [employeeId]);

  const runCheck = async (rt: string, action: string) => {
    setChecking(true);
    const key = `${rt}_${action}`;
    const r = await api.checkPermission(rank, rt, action, 'own_station');
    setPermResults(prev => ({ ...prev, [key]: r }));
    setChecking(false);
  };

  const runAllChecks = async () => {
    setChecking(true);
    const results: Record<string, PermissionCheck> = {};
    for (const rt of RESOURCE_TYPES) {
      for (const action of ACTIONS) {
        results[`${rt}_${action}`] = await api.checkPermission(rank, rt, action, 'own_station');
      }
    }
    setPermResults(results);
    setChecking(false);
  };

  const handleDelegate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!delForm.grantee) return;
    await api.delegatePermission(employeeId, Number(delForm.grantee), delForm.permission, delForm.scope, undefined, delForm.reason);
    setShowDelegate(false);
    setDelForm({ grantee: '', permission: 'APPROVE_CHARGESHEET', scope: 'own_station', reason: '' });
    api.listDelegations(undefined, employeeId).then(setDelegations);
  };

  const handleRevoke = async (pid: string) => {
    await api.revokeDelegation(pid);
    api.listDelegations(undefined, employeeId).then(setDelegations);
  };

  const toggleEmergency = async () => {
    const newState = !emergency;
    await api.setEmergency(newState, 72);
    setEmergency(newState);
  };

  return (
    <div>
      <div className="page-header">
        <h1>{t('Access Control', 'ಪ್ರವೇಶ ನಿಯಂತ್ರಣ')}</h1>
        <p>{t('Permissions, delegations and group memberships', 'ಅನುಮತಿಗಳು, ನಿಯೋಗಗಳು ಮತ್ತು ಗುಂಪು ಸದಸ್ಯತ್ವಗಳು')}</p>
      </div>

      {/* Emergency Banner */}
      {emergency && (
        <div className="card" style={{ marginBottom: 16, borderLeft: '4px solid var(--danger)', background: 'rgba(239,68,68,0.08)' }}>
          <div className="flex items-center gap-2">
            <AlertTriangle size={20} style={{ color: 'var(--danger)' }} />
            <span style={{ fontWeight: 600, color: 'var(--danger)' }}>{t('EMERGENCY MODE ACTIVE — All permissions suspended', 'ತುರ್ತು ಮೋಡ್ ಸಕ್ರಿಯ — ಎಲ್ಲಾ ಅನುಮತಿಗಳನ್ನು ಅಮಾನತುಗೊಳಿಸಲಾಗಿದೆ')}</span>
            <button className="btn btn-secondary btn-sm" style={{ marginLeft: 'auto' }} onClick={toggleEmergency}>{t('Deactivate', 'ನಿಷ್ಕ್ರಿಯಗೊಳಿಸಿ')}</button>
          </div>
        </div>
      )}

      <div className="grid-2">
        {/* Permission Checker */}
        <div className="card">
          <div className="card-header flex items-center gap-2"><Shield size={16} /> {t('Permission Matrix', 'ಅನುಮತಿ ಮ್ಯಾಟ್ರಿಕ್ಸ್')}</div>
          <p className="text-xs text-muted" style={{ marginBottom: 12 }}>{t('Your rank', 'ನಿಮ್ಮ ಶ್ರೇಣಿ')}: <strong>{rank}</strong></p>
          <div className="table-container" style={{ maxHeight: 400, overflow: 'auto' }}>
            <table>
              <thead><tr><th>{t('Resource', 'ಸಂಪನ್ಮೂಲ')}</th>{ACTIONS.map(a => <th key={a} style={{ fontSize: 11 }}>{a}</th>)}</tr></thead>
              <tbody>
                {RESOURCE_TYPES.map(rt => (
                  <tr key={rt}>
                    <td style={{ fontWeight: 600, fontSize: 12 }}>{rt}</td>
                    {ACTIONS.map(action => {
                      const key = `${rt}_${action}`;
                      const p = permResults[key];
                      return (
                        <td key={action} style={{ textAlign: 'center' }}
                          onClick={() => runCheck(rt, action)}>
                          {p ? (p.allowed ? <CheckCircle size={14} style={{ color: 'var(--success)' }} /> : <X size={14} style={{ color: 'var(--danger)' }} />)
                            : <span className="text-xs text-muted" style={{ cursor: 'pointer' }}>-</span>}
                        </td>
                      );
                    })}
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <button className="btn btn-ghost btn-sm" style={{ marginTop: 8 }} onClick={runAllChecks} disabled={checking}>
            {checking ? t('Checking...', 'ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ...') : t('Check All', 'ಎಲ್ಲವನ್ನು ಪರಿಶೀಲಿಸಿ')}
          </button>
          {!emergency && (
            <button className="btn btn-ghost btn-sm" style={{ marginLeft: 8 }} onClick={toggleEmergency}>
              <Unlock size={14} /> {t('Activate Emergency Mode', 'ತುರ್ತು ಮೋಡ್ ಸಕ್ರಿಯಗೊಳಿಸಿ')}
            </button>
          )}
        </div>

        {/* Delegations */}
        <div className="card">
          <div className="card-header flex justify-between items-center">
            <span className="flex items-center gap-2"><UserCheck size={16} /> {t('Delegations', 'ನಿಯೋಗಗಳು')}</span>
            <button className="btn btn-primary btn-sm" onClick={() => setShowDelegate(true)}><Plus size={14} /> {t('Delegate', 'ನಿಯೋಗ')}</button>
          </div>
          {delegations.length === 0 ? (
            <p className="text-muted text-sm">{t('No active delegations', 'ಯಾವುದೇ ಸಕ್ರಿಯ ನಿಯೋಗಗಳಿಲ್ಲ')}</p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {delegations.map(d => (
                <div key={d.permission_id} style={{ padding: 12, borderRadius: 8, border: '1px solid var(--border)', borderLeft: `4px solid ${d.status === 'active' ? 'var(--success)' : 'var(--text-muted)'}` }}>
                  <div className="flex justify-between items-center">
                    <div>
                      <div style={{ fontWeight: 600, fontSize: 13 }}>{d.permission}</div>
                      <div className="text-xs text-muted">{t('Grantee', 'ಸ್ವೀಕರ್ತೆ')}: #{d.grantee_employee_id} · {t('Scope', 'ವ್ಯಾಪ್ತಿ')}: {d.scope}</div>
                      {d.reason && <div className="text-xs text-muted">{t('Reason', 'ಕಾರಣ')}: {d.reason}</div>}
                      <div className="text-xs text-muted">{t('Valid until', 'ಮಾನ್ಯವಾಗಿರುವವರೆಗೆ')}: {new Date(d.valid_until).toLocaleDateString('en-IN')}</div>
                    </div>
                    {d.status === 'active' && (
                      <button className="btn btn-ghost btn-icon btn-sm" onClick={() => handleRevoke(d.permission_id)} title={t('Revoke', 'ರದ್ದುಮಾಡಿ')}>
                        <X size={14} />
                      </button>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* My Groups */}
      <div className="card" style={{ marginTop: 16 }}>
        <div className="card-header flex items-center gap-2"><Users size={16} /> {t('My Groups', 'ನನ್ನ ಗುಂಪುಗಳು')}</div>
        {myGroups.length === 0 ? (
          <p className="text-muted text-sm">{t('Not a member of any task force', 'ಯಾವುದೇ ಕಾರ್ಯಪಡೆಯ ಸದಸ್ಯರಲ್ಲ')}</p>
        ) : (
          <div className="grid-3">
            {myGroups.map(g => (
              <div key={g.group_id} style={{ padding: 12, borderRadius: 8, border: '1px solid var(--border)' }}>
                <div style={{ fontWeight: 600, fontSize: 13 }}>{g.group_name}</div>
                <div className="text-xs text-muted">{t('Type', 'ಪ್ರಕಾರ')}: {g.group_type} · {t('Cases', 'ಪ್ರಕರಣಗಳು')}: {g.linked_case_ids.length}</div>
                <span className={`badge ${g.status === 'active' ? 'badge-low' : 'badge-moderate'}`} style={{ fontSize: 10 }}>{g.status}</span>
                {g.dissolve_at && <div className="text-xs text-muted">{t('Dissolves', 'ವಿಸರ್ಜನೆ')}: {new Date(g.dissolve_at).toLocaleDateString('en-IN')}</div>}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Delegate Modal */}
      {showDelegate && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }} onClick={() => setShowDelegate(false)}>
          <div className="card" style={{ width: 480 }} onClick={e => e.stopPropagation()}>
            <div className="card-header flex justify-between items-center">
              <h3>{t('Delegate Permission', 'ಅನುಮತಿ ನಿಯೋಗ')}</h3>
              <button className="btn btn-ghost btn-icon" onClick={() => setShowDelegate(false)}><X size={20} /></button>
            </div>
            <form onSubmit={handleDelegate}>
              <div className="form-group">
                <label>{t('Grantee Employee ID', 'ಸ್ವೀಕರ್ತೆ ಉದ್ಯೋಗಿ ID')}</label>
                <input className="input" type="number" value={delForm.grantee} onChange={e => setDelForm(f => ({ ...f, grantee: e.target.value }))} required />
              </div>
              <div className="form-group">
                <label>{t('Permission', 'ಅನುಮತಿ')}</label>
                <select className="input" value={delForm.permission} onChange={e => setDelForm(f => ({ ...f, permission: e.target.value }))}>
                  <option value="APPROVE_CHARGESHEET">Approve Chargesheet</option>
                  <option value="APPROVE_CASE">Approve Case</option>
                  <option value="MANAGE_GROUP">Manage Group</option>
                </select>
              </div>
              <div className="form-group">
                <label>{t('Scope', 'ವ್ಯಾಪ್ತಿ')}</label>
                <select className="input" value={delForm.scope} onChange={e => setDelForm(f => ({ ...f, scope: e.target.value }))}>
                  {SCOPES.map(s => <option key={s} value={s}>{s}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>{t('Reason', 'ಕಾರಣ')}</label>
                <textarea className="input" value={delForm.reason} onChange={e => setDelForm(f => ({ ...f, reason: e.target.value }))} placeholder={t('e.g. On leave', 'ಉದಾ: ರಜೆಯಲ್ಲಿದ್ದಾರೆ')} />
              </div>
              <div className="flex gap-4" style={{ justifyContent: 'flex-end' }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowDelegate(false)}>{t('Cancel', 'ರದ್ದುಮಾಡಿ')}</button>
                <button type="submit" className="btn btn-primary"><UserCheck size={16} /> {t('Delegate', 'ನಿಯೋಗ')}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};
