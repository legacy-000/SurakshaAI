import React, { useState, useEffect } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { api } from '../services/api';
import { Clock, Link, Lightbulb, FileText, Plus, UserCheck, X, Bot, ChevronDown, ChevronUp, MessageSquare, Camera, Save, AlertTriangle, CheckCircle, Search, FolderOpen, Loader } from 'lucide-react';
import type { Investigation, SimilarCase, InvestigativeLead, TimelineEvent } from '../types';

const COLUMNS = ['To Do', 'In Progress', 'Blocked', 'Complete'];

const initialTasks: Record<string, { id: string; text: string; priority: string; assignee: string }[]> = {
  'To Do': [
    { id: 't1', text: 'Collect CCTV footage from location', priority: 'high', assignee: 'IO Ravi' },
    { id: 't2', text: 'Interview witness W3', priority: 'medium', assignee: 'IO Ravi' },
  ],
  'In Progress': [
    { id: 't3', text: 'Forensic analysis of evidence #1', priority: 'high', assignee: 'Forensic Lab' },
  ],
  'Blocked': [
    { id: 't4', text: 'Awaiting bank statement from HDFC', priority: 'medium', assignee: 'IO Ravi' },
  ],
  'Complete': [
    { id: 't5', text: 'FIR registration complete', priority: 'high', assignee: 'Station Staff' },
    { id: 't6', text: 'Scene of crime photographed', priority: 'medium', assignee: 'Forensic Lab' },
  ],
};

export const WorkspacePage: React.FC = () => {
  const { t } = useLanguage();
  const [activeView, setActiveView] = useState<'overview' | 'kanban' | 'arrest' | 'notes'>('overview');
  const [tasks, setTasks] = useState(initialTasks);
  const [showArrestForm, setShowArrestForm] = useState(false);
  const [showMilestoneModal, setShowMilestoneModal] = useState(false);
  const [showInvestigationAI, setShowInvestigationAI] = useState(true);
  const [aiMsg, setAiMsg] = useState(t('I am InvestigationAI. Ask me about gaps, next steps, or evidence.', 'ನಾನು ತನಿಖೆ-ಎಐ. ಅಂತರಗಳು, ಮುಂದಿನ ಹಂತಗಳು ಅಥವಾ ಸಾಕ್ಷ್ಯದ ಬಗ್ಗೆ ಕೇಳಿ.'));

  // ── Investigation state ───────────────────────────────────────────
  const [investigations, setInvestigations] = useState<Investigation[]>([]);
  const [loadingList, setLoadingList] = useState(true);
  const [activeInvId, setActiveInvId] = useState<string | null>(null);
  const [activeInv, setActiveInv] = useState<Investigation | null>(null);
  const [showNewInvModal, setShowNewInvModal] = useState(false);
  const [newInvTitle, setNewInvTitle] = useState('');
  const [newInvDesc, setNewInvDesc] = useState('');

  // Case-specific data
  const [similarCases, setSimilarCases] = useState<SimilarCase[]>([]);
  const [leads, setLeads] = useState<InvestigativeLead[]>([]);
  const [timeline, setTimeline] = useState<TimelineEvent[]>([]);
  const [loadingData, setLoadingData] = useState(false);

  useEffect(() => { api.listInvestigations().then(list => { setInvestigations(list); setLoadingList(false); }); }, []);

  useEffect(() => {
    if (!activeInvId) { setActiveInv(null); setSimilarCases([]); setLeads([]); setTimeline([]); return; }
    setLoadingData(true);
    api.getInvestigation(activeInvId).then(inv => {
      if (!inv) { setLoadingData(false); return; }
      setActiveInv(inv);
      if (!inv.cases?.length) { setLoadingData(false); return; }
      const caseId = inv.cases[0].case_master_id;
      return Promise.all([api.getCaseSimilarity(caseId), api.getCaseLeads(caseId), api.getCaseTimeline(caseId)]);
    }).then(results => {
      if (!results) return;
      const [sim, leads_, tl] = results;
      if (sim) setSimilarCases(sim);
      if (leads_) setLeads(leads_);
      if (tl) setTimeline(tl);
      setLoadingData(false);
    }).catch(() => setLoadingData(false));
  }, [activeInvId]);

  const handleCreateInvestigation = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newInvTitle.trim()) return;
    const inv: Investigation = await api.createInvestigation(newInvTitle, newInvDesc);
    setInvestigations(prev => [...prev, inv]);
    setActiveInvId(inv.investigation_id);
    setShowNewInvModal(false);
    setNewInvTitle('');
    setNewInvDesc('');
  };

  const handleGenerateReport = async () => {
    if (!activeInvId) return;
    const report = await api.generateInvestigationReport(activeInvId);
    setAiMsg(t(`Report generated: ${report.status} — ${report.stratus_url || 'PDF ready'}`, `ವರದಿ ರಚಿಸಲಾಗಿದೆ: ${report.status} — ${report.stratus_url || 'PDF ಸಿದ್ಧವಾಗಿದೆ'}`));
  };

  const [arrestForm, setArrestForm] = useState({
    accused_name: '', arrest_type: 'Arrest', arrest_date: '', location: '',
    court: '', io_name: '', is_accused: true, is_complainant_accused: false, photo: '',
  });
  const [arrestFilter, setArrestFilter] = useState({ status: '', date_from: '', date_to: '', io: '' });

  const [notes, setNotes] = useState<{ text: string; timestamp: string; pinned: boolean }[]>([]);
  const [noteText, setNoteText] = useState('');

  const [milestoneForm, setMilestoneForm] = useState({ title: '', date: new Date().toISOString().split('T')[0], description: '' });

  const [dragCol, setDragCol] = useState<string | null>(null);
  const [dragIdx, setDragIdx] = useState<number | null>(null);

  const arrears = [
    { accused: 'Ravi Kumar', type: 'Arrest', date: '2026-03-18', location: 'Bengaluru South', io: 'SI Sharma', status: 'In Custody' },
    { accused: 'Suresh P', type: 'Surrender', date: '2026-04-02', location: 'Mysuru', io: 'SI Sharma', status: 'Bailed' },
  ];

  const handleArrestSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setShowArrestForm(false);
    setArrestForm({ accused_name: '', arrest_type: 'Arrest', arrest_date: '', location: '', court: '', io_name: '', is_accused: true, is_complainant_accused: false, photo: '' });
  };

  const addNote = () => {
    if (!noteText.trim()) return;
    setNotes(prev => [{ text: noteText, timestamp: new Date().toISOString(), pinned: false }, ...prev]);
    setNoteText('');
  };

  const togglePin = (i: number) => {
    setNotes(prev => prev.map((n, idx) => idx === i ? { ...n, pinned: !n.pinned } : n));
  };

  const addMilestone = (e: React.FormEvent) => {
    e.preventDefault();
    setShowMilestoneModal(false);
    setMilestoneForm({ title: '', date: new Date().toISOString().split('T')[0], description: '' });
  };

  const handleDragStart = (col: string, idx: number) => { setDragCol(col); setDragIdx(idx); };
  const handleDrop = (toCol: string) => {
    if (dragCol === null || dragIdx === null || dragCol === toCol) return;
    const task = tasks[dragCol][dragIdx];
    const newTasks = { ...tasks };
    newTasks[dragCol] = newTasks[dragCol].filter((_, i) => i !== dragIdx);
    newTasks[toCol] = [...newTasks[toCol], task];
    setTasks(newTasks);
    setDragCol(null);
    setDragIdx(null);
  };

  const filteredArrests = arrears.filter(a => {
    if (arrestFilter.status && a.status !== arrestFilter.status) return false;
    if (arrestFilter.io && !a.io.toLowerCase().includes(arrestFilter.io.toLowerCase())) return false;
    return true;
  });

  return (
    <div>
      <div className="page-header flex justify-between items-center">
        <div>
          <h1>{t('Investigation Workspace', 'ತನಿಖೆ ಕಾರ್ಯಕ್ಷೇತ್ರ')}</h1>
          <p>{t('Track investigation progress and manage evidence', 'ತನಿಖೆ ಪ್ರಗತಿ ಮತ್ತು ಸಾಕ್ಷ್ಯ ನಿರ್ವಹಣೆ')}</p>
        </div>
        <div className="flex gap-2">
          <button className="btn btn-secondary btn-sm" onClick={() => setShowNewInvModal(true)}><FolderOpen size={16} /> {t('New Investigation', 'ಹೊಸ ತನಿಖೆ')}</button>
          {activeInv && <><button className="btn btn-primary btn-sm" onClick={() => setShowArrestForm(true)}><UserCheck size={16} /> {t('Record Arrest', 'ಬಂಧನ ದಾಖಲಿಸಿ')}</button>
          <button className="btn btn-secondary btn-sm" onClick={() => setShowMilestoneModal(true)}><Plus size={16} /> {t('Add Milestone', 'ಮೈಲಿಗಲ್ಲು ಸೇರಿಸಿ')}</button></>}
        </div>
      </div>

      {/* Investigation selector bar */}
      <div className="card" style={{ marginBottom: 16, padding: '8px 16px' }}>
        <div className="flex items-center gap-3">
          <Search size={16} className="text-muted" />
          <select className="input" style={{ flex: 1 }} value={activeInvId || ''} onChange={e => setActiveInvId(e.target.value || null)}>
            <option value="">{loadingList ? t('Loading...', 'ಲೋಡ್ ಆಗುತ್ತಿದೆ...') : t('-- Select Investigation --', '-- ತನಿಖೆ ಆಯ್ಕೆಮಾಡಿ --')}</option>
            {investigations.map(inv => (
              <option key={inv.investigation_id} value={inv.investigation_id}>{inv.title} ({inv.status})</option>
            ))}
          </select>
          {activeInv && (
            <span className="badge badge-info" style={{ whiteSpace: 'nowrap' }}>
              {t('Cases', 'ಪ್ರಕರಣಗಳು')}: {activeInv.case_count}
            </span>
          )}
        </div>
      </div>

      <div className="tabs" style={{ marginBottom: 24 }}>
        <button className={`tab ${activeView === 'overview' ? 'active' : ''}`} onClick={() => setActiveView('overview')}>{t('Overview', 'ಅವಲೋಕನ')}</button>
        <button className={`tab ${activeView === 'notes' ? 'active' : ''}`} onClick={() => setActiveView('notes')}>{t('Notes', 'ಟಿಪ್ಪಣಿಗಳು')}</button>
        <button className={`tab ${activeView === 'kanban' ? 'active' : ''}`} onClick={() => setActiveView('kanban')}>{t('Task Board', 'ಕಾರ್ಯ ಫಲಕ')}</button>
        <button className={`tab ${activeView === 'arrest' ? 'active' : ''}`} onClick={() => setActiveView('arrest')}>{t('Arrests', 'ಬಂಧನಗಳು')}</button>
      </div>

      <div style={{ display: 'flex', gap: 24 }}>
        <div style={{ flex: 1 }}>
          {!activeInv ? (
            <div className="card" style={{ textAlign: 'center', padding: 48 }}>
              <FolderOpen size={48} style={{ color: 'var(--text-muted)', marginBottom: 16 }} />
              <p className="text-muted">{t('Select or create an investigation to begin', 'ಪ್ರಾರಂಭಿಸಲು ತನಿಖೆಯನ್ನು ಆಯ್ಕೆಮಾಡಿ ಅಥವಾ ರಚಿಸಿ')}</p>
            </div>
          ) : loadingData ? (
            <div className="card" style={{ textAlign: 'center', padding: 48 }}>
              <Loader size={32} className="spin" style={{ color: 'var(--text-muted)' }} />
              <p className="text-muted" style={{ marginTop: 12 }}>{t('Loading investigation data...', 'ತನಿಖಾ ಡೇಟಾವನ್ನು ಲೋಡ್ ಮಾಡಲಾಗುತ್ತಿದೆ...')}</p>
            </div>
          ) : (
            <>
              {activeView === 'overview' && (
                <>
                  {/* Investigation info */}
                  <div className="card" style={{ marginBottom: 24 }}>
                    <h3 style={{ marginBottom: 4 }}>{activeInv.title}</h3>
                    <p className="text-muted text-sm">{activeInv.description}</p>
                    <div className="flex gap-4" style={{ marginTop: 8 }}>
                      <span className="badge badge-info">{activeInv.status}</span>
                      <span className="text-xs text-muted">{t('Created', 'ರಚಿಸಲಾಗಿದೆ')}: {new Date(activeInv.created_at).toLocaleDateString('en-IN')}</span>
                    </div>
                  </div>

                  <div className="grid-2" style={{ marginBottom: 24 }}>
                    <div className="card">
                      <div className="card-header flex items-center gap-2">
                        <Clock size={16} /> {t('Case Timeline', 'ಪ್ರಕರಣದ ಕಾಲರೇಖೆ')}
                      </div>
                      {timeline.length === 0 ? (
                        <p className="text-muted text-sm">{t('No timeline data. Add a case to this investigation.', 'ಯಾವುದೇ ಸಮಯಾವಳಿ ಡೇಟಾ ಇಲ್ಲ. ಈ ತನಿಖೆಗೆ ಪ್ರಕರಣ ಸೇರಿಸಿ.')}</p>
                      ) : timeline.map((ev, i) => (
                        <div key={ev.event_id} style={{ display: 'flex', gap: 16, padding: '12px 0', borderBottom: '1px solid var(--border)', cursor: 'pointer' }}
                          onClick={() => setAiMsg(`${ev.description} (${ev.event_date}) — ${t('Source', 'ಮೂಲ')}: ${ev.source_table}`)}>
                          <div style={{ width: 100, fontSize: 12, color: 'var(--text-muted)', flexShrink: 0 }}>{ev.event_date}</div>
                          <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>{ev.description}</div>
                        </div>
                      ))}
                    </div>

                    <div className="card">
                      <div className="card-header flex items-center gap-2"><Link size={16} /> {t('Similar Cases', 'ಹೋಲುವ ಪ್ರಕರಣಗಳು')}</div>
                      {similarCases.length === 0 ? (
                        <p className="text-muted text-sm">{t('No similar cases found.', 'ಯಾವುದೇ ಹೋಲುವ ಪ್ರಕರಣಗಳು ಕಂಡುಬಂದಿಲ್ಲ.')}</p>
                      ) : (
                        <>
                          <div className="table-container">
                            <table>
                              <thead><tr><th>{t('Crime No', 'ಅಪರಾಧ ಸಂಖ್ಯೆ')}</th><th>{t('Type', 'ಪ್ರಕಾರ')}</th><th>{t('Similarity', 'ಹೋಲಿಕೆ')}</th><th>{t('District', 'ಜಿಲ್ಲೆ')}</th></tr></thead>
                              <tbody>
                                {similarCases.map(c => (
                                  <tr key={c.case_master_id}>
                                    <td style={{ fontFamily: 'monospace', fontSize: 12 }}>{c.crime_no}</td>
                                    <td>{c.crime_sub_head}</td>
                                    <td><span className="badge badge-info">{(c.similarity_score * 100).toFixed(0)}%</span></td>
                                    <td>{c.district_name}</td>
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                          <button className="btn btn-ghost btn-sm" style={{ marginTop: 8 }}
                            onClick={() => setAiMsg(t('Similar cases analysis — checking for co-accused and shared evidence patterns.', 'ಹೋಲುವ ಪ್ರಕರಣಗಳ ವಿಶ್ಲೇಷಣೆ — ಸಹ-ಆರೋಪಿಗಳು ಮತ್ತು ಹಂಚಿಕೆಯ ಸಾಕ್ಷ್ಯ ಮಾದರಿಗಳನ್ನು ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ.'))}>
                            {t('Analyze patterns', 'ಮಾದರಿಗಳನ್ನು ವಿಶ್ಲೇಷಿಸಿ')}
                          </button>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Investigative Leads */}
                  <div className="card" style={{ marginBottom: 24 }}>
                    <div className="card-header flex items-center gap-2"><Lightbulb size={16} /> {t('Generated Leads', 'ರಚಿಸಲಾದ ಸುಳಿವುಗಳು')}</div>
                    {leads.length === 0 ? (
                      <p className="text-muted text-sm">{t('No leads generated yet. Add a case to generate leads.', 'ಇನ್ನೂ ಸುಳಿವುಗಳನ್ನು ರಚಿಸಲಾಗಿಲ್ಲ. ಸುಳಿವುಗಳನ್ನು ರಚಿಸಲು ಪ್ರಕರಣ ಸೇರಿಸಿ.')}</p>
                    ) : (
                      <div className="flex gap-4">
                        {leads.map(lead => (
                          <div key={lead.lead_id} className="card" style={{ flex: 1, borderLeft: `4px solid ${lead.confidence_class === 'high' ? 'var(--success)' : lead.confidence_class === 'medium' ? 'var(--warning)' : 'var(--text-muted)'}`, cursor: 'pointer' }}
                            onClick={() => setAiMsg(`${lead.lead_description} [${t('Confidence', 'ವಿಶ್ವಾಸ')}: ${(lead.confidence_score * 100).toFixed(0)}%]`)}>
                            <div className="flex justify-between items-center">
                              <div>
                                <div style={{ fontWeight: 600, fontSize: 14 }}>{t(lead.lead_type === 'co_accused_link' ? 'Co-Accused Link' : lead.lead_type === 'location_pattern' ? 'Location Pattern' : 'Witness Lead', lead.lead_type)}</div>
                                <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>{lead.lead_description}</div>
                              </div>
                              <span className="badge badge-info">{t('Confidence', 'ವಿಶ್ವಾಸ')}: {(lead.confidence_score * 100).toFixed(0)}%</span>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                </>
              )}

              {activeView === 'notes' && (
                <div className="card">
                  <div className="card-header">{t('Investigation Notes', 'ತನಿಖಾ ಟಿಪ್ಪಣಿಗಳು')}</div>
                  <div style={{ display: 'flex', gap: 8, marginBottom: 16 }}>
                    <textarea className="input" style={{ flex: 1, minHeight: 80, resize: 'vertical' }}
                      placeholder={t('Enter investigation notes...', 'ತನಿಖಾ ಟಿಪ್ಪಣಿಗಳನ್ನು ನಮೂದಿಸಿ...')}
                      value={noteText} onChange={e => setNoteText(e.target.value)} />
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      <button className="btn btn-primary btn-sm" onClick={addNote}><Save size={16} /></button>
                      <button className="btn btn-ghost btn-icon" title={t('Attach file', 'ಫೈಲ್ ಲಗತ್ತಿಸಿ')}><Camera size={16} /></button>
                    </div>
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                    {notes.length === 0 && <p className="text-muted text-sm">{t('No notes yet. Start typing above.', 'ಇನ್ನೂ ಟಿಪ್ಪಣಿಗಳಿಲ್ಲ. ಮೇಲೆ ಟೈಪ್ ಮಾಡಲು ಪ್ರಾರಂಭಿಸಿ.')}</p>}
                    {notes.map((n, i) => (
                      <div key={i} style={{
                        padding: 12, borderRadius: 8, border: '1px solid var(--border)',
                        borderLeft: n.pinned ? '4px solid var(--warning)' : '4px solid var(--primary)',
                        background: 'var(--bg-card)'
                      }}>
                        <div className="flex justify-between items-start">
                          <p style={{ fontSize: 14, color: 'var(--text-secondary)', flex: 1, whiteSpace: 'pre-wrap' }}>{n.text}</p>
                          <button className={`btn btn-ghost btn-icon ${n.pinned ? 'active' : ''}`} onClick={() => togglePin(i)}
                            title={n.pinned ? t('Unpin', 'ಅನ್ಪಿನ್') : t('Pin to top', 'ಮೇಲೆ ಪಿನ್ ಮಾಡಿ')}>
                            <ChevronDown size={14} style={{ color: n.pinned ? 'var(--warning)' : 'var(--text-muted)' }} />
                          </button>
                        </div>
                        <div className="text-xs text-muted" style={{ marginTop: 4 }}>
                          {new Date(n.timestamp).toLocaleString('en-IN')}
                          {n.pinned && <span className="badge badge-moderate" style={{ marginLeft: 8, fontSize: 10 }}>{t('Pinned', 'ಪಿನ್ ಮಾಡಲಾಗಿದೆ')}</span>}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {activeView === 'kanban' && (
                <div style={{ display: 'flex', gap: 16, minHeight: 400 }}>
                  {COLUMNS.map(col => (
                    <div key={col} style={{ flex: 1, background: 'var(--bg-hover)', borderRadius: 12, padding: 16 }}
                      onDragOver={e => e.preventDefault()} onDrop={() => handleDrop(col)}>
                      <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 12, color: 'var(--text-primary)' }}>
                        {t(col, col)} <span className="badge badge-info" style={{ marginLeft: 8 }}>{tasks[col].length}</span>
                      </div>
                      {tasks[col].map((task, idx) => (
                        <div key={task.id} draggable onDragStart={() => handleDragStart(col, idx)}
                          style={{
                            padding: '12px', marginBottom: 8, borderRadius: 8, background: 'var(--bg-card)',
                            border: '1px solid var(--border)', cursor: 'grab', fontSize: 13,
                            borderLeft: `4px solid ${task.priority === 'high' ? 'var(--danger)' : task.priority === 'medium' ? 'var(--warning)' : 'var(--success)'}`
                          }}>
                          <div style={{ fontWeight: 500, marginBottom: 4 }}>{task.text}</div>
                          <div className="flex justify-between items-center">
                            <span className="text-xs text-muted">{task.assignee}</span>
                            <span className={`badge ${task.priority === 'high' ? 'badge-elevated' : task.priority === 'medium' ? 'badge-moderate' : 'badge-low'}`}
                              style={{ fontSize: 10 }}>{task.priority}</span>
                          </div>
                        </div>
                      ))}
                      {tasks[col].length === 0 && (
                        <div style={{ padding: 24, border: '2px dashed var(--border)', borderRadius: 8, textAlign: 'center' }}>
                          <p className="text-xs text-muted">{t('Drop tasks here', 'ಕಾರ್ಯಗಳನ್ನು ಇಲ್ಲಿ ಎಳೆಯಿರಿ')}</p>
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              )}

              {activeView === 'arrest' && (
                <div className="card">
                  <div className="card-header flex justify-between items-center">
                    <h3>{t('Arrest Records', 'ಬಂಧನ ದಾಖಲೆಗಳು')}</h3>
                    <button className="btn btn-primary btn-sm" onClick={() => setShowArrestForm(true)}>
                      <Plus size={16} /> {t('New Arrest', 'ಹೊಸ ಬಂಧನ')}
                    </button>
                  </div>
                  <div className="grid-3" style={{ marginBottom: 16 }}>
                    <div className="form-group">
                      <label>{t('Filter by Status', 'ಸ್ಥಿತಿ ಫಿಲ್ಟರ್')}</label>
                      <select className="input" value={arrestFilter.status} onChange={e => setArrestFilter(f => ({ ...f, status: e.target.value }))}>
                        <option value="">{t('All', 'ಎಲ್ಲಾ')}</option>
                        <option value="In Custody">{t('In Custody', 'ವಶದಲ್ಲಿ')}</option>
                        <option value="Bailed">{t('Bailed', 'ಜಾಮೀನು')}</option>
                        <option value="Chargesheeted">{t('Chargesheeted', 'ಪ್ರಸ್ತಾವನೆ ಸಲ್ಲಿಸಲಾಗಿದೆ')}</option>
                      </select>
                    </div>
                    <div className="form-group">
                      <label>{t('Filter by IO', 'ತನಿಖಾಧಿಕಾರಿ ಫಿಲ್ಟರ್')}</label>
                      <input className="input" placeholder={t('IO name...', 'ತನಿಖಾಧಿಕಾರಿ ಹೆಸರು...')} value={arrestFilter.io} onChange={e => setArrestFilter(f => ({ ...f, io: e.target.value }))} />
                    </div>
                  </div>
                  <div className="table-container">
                    <table>
                      <thead>
                        <tr>
                          <th>{t('Accused', 'ಆರೋಪಿ')}</th>
                          <th>{t('Type', 'ಪ್ರಕಾರ')}</th>
                          <th>{t('Date', 'ದಿನಾಂಕ')}</th>
                          <th>{t('Location', 'ಸ್ಥಳ')}</th>
                          <th>{t('IO', 'ತನಿಖಾಧಿಕಾರಿ')}</th>
                          <th>{t('Status', 'ಸ್ಥಿತಿ')}</th>
                          <th>{t('Actions', 'ಕ್ರಿಯೆಗಳು')}</th>
                        </tr>
                      </thead>
                      <tbody>
                        {filteredArrests.length === 0 ? (
                          <tr><td colSpan={7} className="text-center text-muted">{t('No arrest records found', 'ಯಾವುದೇ ಬಂಧನ ದಾಖಲೆಗಳು ಕಂಡುಬಂದಿಲ್ಲ')}</td></tr>
                        ) : filteredArrests.map((a, i) => (
                          <tr key={i}>
                            <td>{a.accused}</td>
                            <td><span className={`badge ${a.type === 'Arrest' ? 'badge-low' : 'badge-info'}`}>{a.type}</span></td>
                            <td>{a.date}</td>
                            <td>{a.location}</td>
                            <td>{a.io}</td>
                            <td><span className={`badge ${a.status === 'In Custody' ? 'badge-elevated' : 'badge-low'}`}>{a.status}</span></td>
                            <td>
                              <div className="flex gap-2">
                                <button className="btn btn-ghost btn-icon btn-sm" title={t('Mark ready for chargesheet', 'ಪ್ರಸ್ತಾವನೆಗೆ ಸಿದ್ಧ ಎಂದು ಗುರುತಿಸಿ')}>
                                  <FileText size={14} />
                                </button>
                              </div>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* InvestigationAI Sidebar */}
        <div style={{ width: 280, flexShrink: 0 }}>
          <div className="card" style={{ position: 'sticky', top: 32 }}>
            <div className="card-header flex justify-between items-center">
              <span className="flex items-center gap-2"><Bot size={20} /> {t('InvestigationAI', 'ತನಿಖೆ-ಎಐ')}</span>
              <button className="btn btn-ghost btn-icon" onClick={() => setShowInvestigationAI(!showInvestigationAI)}>
                {showInvestigationAI ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
              </button>
            </div>

            {activeInv && (
              <div className="grid-2" style={{ marginBottom: 12, gap: 8 }}>
                <div style={{ textAlign: 'center', padding: 8, background: 'var(--bg-hover)', borderRadius: 8 }}>
                  <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--primary)' }}>{activeInv.case_count}</div>
                  <div className="text-xs text-muted">{t('Linked Cases', 'ಲಿಂಕ್ ಮಾಡಲಾದ ಪ್ರಕರಣಗಳು')}</div>
                </div>
                <div style={{ textAlign: 'center', padding: 8, background: 'var(--bg-hover)', borderRadius: 8 }}>
                  <div style={{ fontSize: 18, fontWeight: 700, color: 'var(--warning)' }}>{leads.length}</div>
                  <div className="text-xs text-muted">{t('Active Leads', 'ಸಕ್ರಿಯ ಸುಳಿವುಗಳು')}</div>
                </div>
              </div>
            )}

            {showInvestigationAI && (
              <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
                <div style={{ marginBottom: 12, padding: 12, background: 'var(--bg-hover)', borderRadius: 8, fontSize: 13, minHeight: 40 }}>
                  {aiMsg}
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                  <button className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }}
                    onClick={() => setAiMsg(t('Evidence gaps identified: (1) No forensic report for weapon, (2) Missing CCTV footage from Main Road, (3) Witness W3 statement not recorded.', 'ಸಾಕ್ಷ್ಯ ಅಂತರಗಳು ಗುರುತಿಸಲಾಗಿದೆ: (1) ಆಯುಧದ ಫೋರೆನ್ಸಿಕ್ ವರದಿ ಇಲ್ಲ, (2) ಮುಖ್ಯ ರಸ್ತೆಯ ಸಿಸಿಟಿವಿ ದೃಶ್ಯಾವಳಿ ಕಾಣೆಯಾಗಿದೆ, (3) ಸಾಕ್ಷಿ W3 ಹೇಳಿಕೆ ದಾಖಲಾಗಿಲ್ಲ.'))}>
                    <AlertTriangle size={14} /> {t('What gaps remain?', 'ಯಾವ ಅಂತರಗಳು ಉಳಿದಿವೆ?')}
                  </button>
                  <button className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }}
                    onClick={() => setAiMsg(t('Recommended next steps: (1) Interview witness W3 about timeline discrepancy, (2) Collect bank statement from HDFC, (3) Cross-check A2 alibi with CCTV.', 'ಶಿಫಾರಸು ಮಾಡಲಾದ ಮುಂದಿನ ಹಂತಗಳು: (1) ಸಮಯಾವಧಿ ವ್ಯತ್ಯಾಸದ ಬಗ್ಗೆ ಸಾಕ್ಷಿ W3 ಅವರನ್ನು ಸಂದರ್ಶಿಸಿ, (2) HDFC ಯಿಂದ ಬ್ಯಾಂಕ್ ಸ್ಟೇಟ್‌ಮೆಂಟ್ ಸಂಗ್ರಹಿಸಿ, (3) ಸಿಸಿಟಿವಿಯೊಂದಿಗೆ A2 ಅಲಿಬಿಯನ್ನು ಕ್ರಾಸ್-ಚೆಕ್ ಮಾಡಿ.'))}>
                    <Lightbulb size={14} /> {t('Suggest next steps', 'ಮುಂದಿನ ಹಂತಗಳನ್ನು ಸೂಚಿಸಿ')}
                  </button>
                  <button className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }}
                    onClick={() => setAiMsg(t('No contradictions found in current statements. All witness accounts are consistent with FIR timeline.', 'ಪ್ರಸ್ತುತ ಹೇಳಿಕೆಗಳಲ್ಲಿ ಯಾವುದೇ ವಿರೋಧಾಭಾಸಗಳು ಕಂಡುಬಂದಿಲ್ಲ. ಎಲ್ಲಾ ಸಾಕ್ಷಿ ಖಾತೆಗಳು ಎಫ್ಐಆರ್ ಸಮಯಾವಧಿಯೊಂದಿಗೆ ಸ್ಥಿರವಾಗಿವೆ.'))}>
                    <MessageSquare size={14} /> {t('Any contradictions?', 'ಯಾವುದೇ ವಿರೋಧಾಭಾಸಗಳು?')}
                  </button>
                  <button className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }}
                    onClick={() => setAiMsg(t('Recommend collecting: (1) Weapon forensic report, (2) Phone records of accused, (3) CCTV from KG Halli junction.', 'ಸಂಗ್ರಹಿಸಲು ಶಿಫಾರಸು: (1) ಆಯುಧ ಫೋರೆನ್ಸಿಕ್ ವರದಿ, (2) ಆರೋಪಿಯ ಫೋನ್ ದಾಖಲೆಗಳು, (3) ಕೆಜಿ ಹಳ್ಳಿ ಜಂಕ್ಷನ್ನ ಸಿಸಿಟಿವಿ.'))}>
                    <Camera size={14} /> {t('Recommend evidence', 'ಸಾಕ್ಷ್ಯ ಶಿಫಾರಸು ಮಾಡಿ')}
                  </button>
                  <button className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }} onClick={handleGenerateReport}>
                    <FileText size={14} /> {t('Generate investigation report', 'ತನಿಖಾ ವರದಿ ರಚಿಸಿ')}
                  </button>
                  <button className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }}
                    onClick={() => setAiMsg(t('Linking cases — check co-accused and shared evidence across linked cases.', 'ಪ್ರಕರಣಗಳನ್ನು ಲಿಂಕ್ ಮಾಡಲಾಗುತ್ತಿದೆ — ಲಿಂಕ್ ಮಾಡಲಾದ ಪ್ರಕರಣಗಳಾದ್ಯಂತ ಸಹ-ಆರೋಪಿಗಳು ಮತ್ತು ಹಂಚಿಕೆಯ ಸಾಕ್ಷ್ಯವನ್ನು ಪರಿಶೀಲಿಸಿ.'))}>
                    <Link size={14} /> {t('Link to other cases', 'ಇತರ ಪ್ರಕರಣಗಳಿಗೆ ಲಿಂಕ್ ಮಾಡಿ')}
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Arrest Form Modal */}
      {showArrestForm && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }} onClick={() => setShowArrestForm(false)}>
          <div className="card" style={{ width: 600, maxHeight: '85vh', overflow: 'auto' }}
            onClick={e => e.stopPropagation()}>
            <div className="card-header flex justify-between items-center">
              <h3>{t('Record Arrest / Surrender', 'ಬಂಧನ / ಶರಣಾಗತಿ ದಾಖಲಿಸಿ')}</h3>
              <button className="btn btn-ghost btn-icon" onClick={() => setShowArrestForm(false)}><X size={20} /></button>
            </div>
            <form onSubmit={handleArrestSubmit}>
              <div className="grid-2">
                <div className="form-group">
                  <label>{t('Accused Name', 'ಆರೋಪಿಯ ಹೆಸರು')}</label>
                  <select className="input" value={arrestForm.accused_name} onChange={e => setArrestForm(f => ({ ...f, accused_name: e.target.value }))} required>
                    <option value="">-- {t('Select', 'ಆಯ್ಕೆಮಾಡಿ')} --</option>
                    <option value="Ravi Kumar">Ravi Kumar (A1)</option>
                    <option value="Suresh P">Suresh P (A2)</option>
                  </select>
                </div>
                <div className="form-group">
                  <label>{t('Type', 'ಪ್ರಕಾರ')}</label>
                  <select className="input" value={arrestForm.arrest_type} onChange={e => setArrestForm(f => ({ ...f, arrest_type: e.target.value }))}>
                    <option value="Arrest">{t('Arrest', 'ಬಂಧನ')}</option>
                    <option value="Voluntary Surrender">{t('Voluntary Surrender', 'ಸ್ವಯಂ ಶರಣಾಗತಿ')}</option>
                  </select>
                </div>
              </div>
              <div className="grid-2">
                <div className="form-group">
                  <label>{t('Date/Time of Arrest', 'ಬಂಧನದ ದಿನಾಂಕ/ಸಮಯ')}</label>
                  <input className="input" type="datetime-local" value={arrestForm.arrest_date} onChange={e => setArrestForm(f => ({ ...f, arrest_date: e.target.value }))} required />
                </div>
                <div className="form-group">
                  <label>{t('Location', 'ಸ್ಥಳ')}</label>
                  <input className="input" placeholder={t('District / Station', 'ಜಿಲ್ಲೆ / ಠಾಣೆ')} value={arrestForm.location} onChange={e => setArrestForm(f => ({ ...f, location: e.target.value }))} />
                </div>
              </div>
              <div className="grid-2">
                <div className="form-group">
                  <label>{t('Court Produced Before', 'ನ್ಯಾಯಾಲಯ ಹಾಜರುಪಡಿಸಿದ')}</label>
                  <input className="input" placeholder={t('Court name', 'ನ್ಯಾಯಾಲಯದ ಹೆಸರು')} value={arrestForm.court} onChange={e => setArrestForm(f => ({ ...f, court: e.target.value }))} />
                </div>
                <div className="form-group">
                  <label>{t('Investigating Officer', 'ತನಿಖಾಧಿಕಾರಿ')}</label>
                  <input className="input" value={arrestForm.io_name} onChange={e => setArrestForm(f => ({ ...f, io_name: e.target.value }))} />
                </div>
              </div>
              <div className="grid-2">
                <div className="form-group">
                  <label>{t('Is Accused Flag', 'ಆರೋಪಿ ಫ್ಲ್ಯಾಗ್')}</label>
                  <label className="flex items-center gap-2" style={{ cursor: 'pointer' }}>
                    <input type="checkbox" checked={arrestForm.is_accused} onChange={e => setArrestForm(f => ({ ...f, is_accused: e.target.checked }))} />
                    {t('This person is accused in this case', 'ಈ ವ್ಯಕ್ತಿ ಈ ಪ್ರಕರಣದಲ್ಲಿ ಆರೋಪಿ')}
                  </label>
                </div>
                <div className="form-group">
                  <label>{t('Is Complainant Accused', 'ದೂರುದಾರ ಆರೋಪಿ')}</label>
                  <label className="flex items-center gap-2" style={{ cursor: 'pointer' }}>
                    <input type="checkbox" checked={arrestForm.is_complainant_accused} onChange={e => setArrestForm(f => ({ ...f, is_complainant_accused: e.target.checked }))} />
                    {t('Complainant is also accused', 'ದೂರುದಾರರು ಸಹ ಆರೋಪಿ')}
                  </label>
                </div>
              </div>
              <div className="form-group">
                <label>{t('Photo of Accused (URL)', 'ಆರೋಪಿಯ ಫೋಟೋ (URL)')}</label>
                <div style={{ display: 'flex', gap: 8 }}>
                  <input className="input" placeholder={t('Paste image URL or upload', 'ಚಿತ್ರ URL ಅಂಟಿಸಿ ಅಥವಾ ಅಪ್‌ಲೋಡ್ ಮಾಡಿ')} value={arrestForm.photo} onChange={e => setArrestForm(f => ({ ...f, photo: e.target.value }))} style={{ flex: 1 }} />
                  <button type="button" className="btn btn-ghost btn-icon" title={t('Upload photo', 'ಫೋಟೋ ಅಪ್‌ಲೋಡ್')}><Camera size={18} /></button>
                </div>
              </div>
              <div className="flex gap-4" style={{ justifyContent: 'flex-end', marginTop: 24 }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowArrestForm(false)}>{t('Cancel', 'ರದ್ದುಮಾಡಿ')}</button>
                <button type="submit" className="btn btn-primary"><UserCheck size={16} /> {t('Submit Arrest Record', 'ಬಂಧನ ದಾಖಲೆ ಸಲ್ಲಿಸಿ')}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* Milestone Modal */}
      {showMilestoneModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }} onClick={() => setShowMilestoneModal(false)}>
          <div className="card" style={{ width: 480 }} onClick={e => e.stopPropagation()}>
            <div className="card-header flex justify-between items-center">
              <h3>{t('Add Investigation Milestone', 'ತನಿಖಾ ಮೈಲಿಗಲ್ಲು ಸೇರಿಸಿ')}</h3>
              <button className="btn btn-ghost btn-icon" onClick={() => setShowMilestoneModal(false)}><X size={20} /></button>
            </div>
            <form onSubmit={addMilestone}>
              <div className="form-group">
                <label>{t('Milestone Title', 'ಮೈಲಿಗಲ್ಲು ಶೀರ್ಷಿಕೆ')}</label>
                <input className="input" value={milestoneForm.title} onChange={e => setMilestoneForm(f => ({ ...f, title: e.target.value }))} required />
              </div>
              <div className="form-group">
                <label>{t('Date', 'ದಿನಾಂಕ')}</label>
                <input className="input" type="date" value={milestoneForm.date} onChange={e => setMilestoneForm(f => ({ ...f, date: e.target.value }))} required />
              </div>
              <div className="form-group">
                <label>{t('Description', 'ವಿವರಣೆ')}</label>
                <textarea className="input" style={{ minHeight: 80 }} value={milestoneForm.description} onChange={e => setMilestoneForm(f => ({ ...f, description: e.target.value }))} />
              </div>
              <div className="flex gap-4" style={{ justifyContent: 'flex-end', marginTop: 16 }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowMilestoneModal(false)}>{t('Cancel', 'ರದ್ದುಮಾಡಿ')}</button>
                <button type="submit" className="btn btn-primary"><CheckCircle size={16} /> {t('Add Milestone', 'ಮೈಲಿಗಲ್ಲು ಸೇರಿಸಿ')}</button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* New Investigation Modal */}
      {showNewInvModal && (
        <div style={{
          position: 'fixed', top: 0, left: 0, right: 0, bottom: 0, background: 'rgba(0,0,0,0.5)',
          display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000
        }} onClick={() => setShowNewInvModal(false)}>
          <div className="card" style={{ width: 480 }} onClick={e => e.stopPropagation()}>
            <div className="card-header flex justify-between items-center">
              <h3>{t('New Investigation', 'ಹೊಸ ತನಿಖೆ')}</h3>
              <button className="btn btn-ghost btn-icon" onClick={() => setShowNewInvModal(false)}><X size={20} /></button>
            </div>
            <form onSubmit={handleCreateInvestigation}>
              <div className="form-group">
                <label>{t('Title', 'ಶೀರ್ಷಿಕೆ')}</label>
                <input className="input" value={newInvTitle} onChange={e => setNewInvTitle(e.target.value)} placeholder={t('e.g. KG Halli Theft Ring', 'ಉದಾ: ಕೆಜಿ ಹಳ್ಳಿ ಕಳ್ಳತನ ಸಮೂಹ')} required />
              </div>
              <div className="form-group">
                <label>{t('Description', 'ವಿವರಣೆ')}</label>
                <textarea className="input" style={{ minHeight: 80 }} value={newInvDesc} onChange={e => setNewInvDesc(e.target.value)} placeholder={t('Optional description...', 'ಐಚ್ಛಿಕ ವಿವರಣೆ...')} />
              </div>
              <div className="flex gap-4" style={{ justifyContent: 'flex-end', marginTop: 16 }}>
                <button type="button" className="btn btn-secondary" onClick={() => setShowNewInvModal(false)}>{t('Cancel', 'ರದ್ದುಮಾಡಿ')}</button>
                <button type="submit" className="btn btn-primary"><FolderOpen size={16} /> {t('Create', 'ರಚಿಸಿ')}</button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};