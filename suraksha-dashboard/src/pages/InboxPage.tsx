import React, { useState, useEffect } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { api } from '../services/api';
import { Mail, Send, Reply, AlertTriangle, CheckCircle, MessageSquare, ChevronDown, ChevronUp, Paperclip, Clock, X } from 'lucide-react';
import type { Message } from '../types';

const PRIORITY_ICONS: Record<string, { icon: string; color: string }> = {
  CRITICAL: { icon: '🔴', color: 'var(--danger)' },
  HIGH: { icon: '🟠', color: 'var(--warning)' },
  NORMAL: { icon: '🟢', color: 'var(--success)' },
  LOW: { icon: '⚪', color: 'var(--text-muted)' },
};

export const InboxPage: React.FC = () => {
  const { t } = useLanguage();
  const employeeId = Number(localStorage.getItem('user_context') ? JSON.parse(localStorage.getItem('user_context')!).user_id?.replace(/\D/g, '') || 1 : 1);
  const [messages, setMessages] = useState<Message[]>([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'unread' | 'critical' | 'high'>('all');
  const [selectedMsg, setSelectedMsg] = useState<Message | null>(null);
  const [thread, setThread] = useState<Message[]>([]);
  const [showSend, setShowSend] = useState(false);
  const [sendForm, setSendForm] = useState({ to: '', subject: '', body: '', priority: 'NORMAL' as string, type: 'STATUS_UPDATE' });

  useEffect(() => {
    api.listInbox(employeeId).then(msgs => { setMessages(msgs); setLoading(false); });
    const poll = setInterval(() => {
      api.listInbox(employeeId).then(msgs => setMessages(msgs));
    }, 15000);
    return () => clearInterval(poll);
  }, [employeeId]);

  const loadThread = async (msg: Message) => {
    setSelectedMsg(msg);
    if (msg.message_id) api.markRead(msg.message_id, employeeId);
    const t = await api.getThread(msg.message_id);
    setThread(t.length > 0 ? t : [msg]);
  };

  const handleAck = async (msg: Message) => {
    await api.acknowledgeMessage(msg.message_id, employeeId);
    setMessages(prev => prev.map(m => m.message_id === msg.message_id ? { ...m, status: 'ACKNOWLEDGED' } : m));
    if (selectedMsg?.message_id === msg.message_id) setSelectedMsg({ ...selectedMsg, status: 'ACKNOWLEDGED' });
  };

  const handleSend = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!sendForm.to || !sendForm.subject) return;
    const toIds = sendForm.to.split(',').map(s => Number(s.trim())).filter(Boolean);
    const parent = selectedMsg?.message_id;
    await api.sendMessage(sendForm.type, sendForm.subject, sendForm.body, toIds, sendForm.priority, parent);
    setShowSend(false);
    setSendForm({ to: '', subject: '', body: '', priority: 'NORMAL', type: 'STATUS_UPDATE' });
    const msgs = await api.listInbox(employeeId);
    setMessages(msgs);
  };

  const priorityFilter = filter === 'critical' ? 'CRITICAL' : filter === 'high' ? 'HIGH' : undefined;
  const filtered = messages.filter(m => filter === 'all' || filter === 'unread' ? m.status !== 'READ' && m.status !== 'ACKNOWLEDGED' : m.priority === priorityFilter);

  return (
    <div>
      <div className="page-header flex justify-between items-center">
        <div>
          <h1>{t('Message Inbox', 'ಸಂದೇಶಗಳು')}</h1>
          <p>{t('Communication hub', 'ಸಂವಹನ ಕೇಂದ್ರ')}</p>
        </div>
        <button className="btn btn-primary btn-sm" onClick={() => { setShowSend(!showSend); setSelectedMsg(null); }}>
          <Send size={16} /> {t('New Message', 'ಹೊಸ ಸಂದೇಶ')}
        </button>
      </div>

      {showSend && (
        <div className="card" style={{ marginBottom: 16 }}>
          <div className="card-header flex justify-between items-center">
            <h3>{t('Compose Message', 'ಸಂದೇಶ ರಚಿಸಿ')}</h3>
            <button className="btn btn-ghost btn-icon" onClick={() => setShowSend(false)}><X size={18} /></button>
          </div>
          <form onSubmit={handleSend}>
            <div className="grid-2">
              <div className="form-group">
                <label>{t('To (Employee IDs)', 'ಗೆ (ಉದ್ಯೋಗಿ ID)')}</label>
                <input className="input" value={sendForm.to} onChange={e => setSendForm(f => ({ ...f, to: e.target.value }))} placeholder="e.g. 2, 3" required />
              </div>
              <div className="form-group">
                <label>{t('Priority', 'ಆದ್ಯತೆ')}</label>
                <select className="input" value={sendForm.priority} onChange={e => setSendForm(f => ({ ...f, priority: e.target.value }))}>
                  <option value="NORMAL">{t('Normal', 'ಸಾಮಾನ್ಯ')}</option>
                  <option value="HIGH">{t('High', 'ಹೆಚ್ಚಿನ')}</option>
                  <option value="CRITICAL">{t('Critical', 'ನಿರ್ಣಾಯಕ')}</option>
                </select>
              </div>
            </div>
            <div className="form-group">
              <label>{t('Subject', 'ವಿಷಯ')}</label>
              <input className="input" value={sendForm.subject} onChange={e => setSendForm(f => ({ ...f, subject: e.target.value }))} required />
            </div>
            <div className="form-group">
              <label>{t('Body', 'ವಿಷಯ')}</label>
              <textarea className="input" style={{ minHeight: 100 }} value={sendForm.body} onChange={e => setSendForm(f => ({ ...f, body: e.target.value }))} />
            </div>
            <div className="flex gap-4" style={{ justifyContent: 'flex-end' }}>
              <button type="button" className="btn btn-secondary" onClick={() => setShowSend(false)}>{t('Cancel', 'ರದ್ದುಮಾಡಿ')}</button>
              <button type="submit" className="btn btn-primary"><Send size={16} /> {t('Send', 'ಕಳುಹಿಸಿ')}</button>
            </div>
          </form>
        </div>
      )}

      <div className="tabs" style={{ marginBottom: 16 }}>
        <button className={`tab ${filter === 'all' ? 'active' : ''}`} onClick={() => setFilter('all')}>{t('All', 'ಎಲ್ಲಾ')} ({messages.length})</button>
        <button className={`tab ${filter === 'unread' ? 'active' : ''}`} onClick={() => setFilter('unread')}>{t('Unread', 'ಓದಿಲ್ಲ')} ({messages.filter(m => m.status !== 'READ' && m.status !== 'ACKNOWLEDGED').length})</button>
        <button className={`tab ${filter === 'critical' ? 'active' : ''}`} onClick={() => setFilter('critical')}>{t('Critical', 'ನಿರ್ಣಾಯಕ')}</button>
        <button className={`tab ${filter === 'high' ? 'active' : ''}`} onClick={() => setFilter('high')}>{t('High', 'ಹೆಚ್ಚಿನ')}</button>
      </div>

      <div style={{ display: 'flex', gap: 16 }}>
        <div style={{ flex: 1 }}>
          {loading ? (
            <div className="card" style={{ padding: 48, textAlign: 'center' }}>
              <p className="text-muted">{t('Loading...', 'ಲೋಡ್ ಆಗುತ್ತಿದೆ...')}</p>
            </div>
          ) : filtered.length === 0 ? (
            <div className="card" style={{ padding: 48, textAlign: 'center' }}>
              <Mail size={48} style={{ color: 'var(--text-muted)', marginBottom: 16 }} />
              <p className="text-muted">{t('No messages', 'ಯಾವುದೇ ಸಂದೇಶಗಳಿಲ್ಲ')}</p>
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              {filtered.map(msg => {
                const pi = PRIORITY_ICONS[msg.priority] || PRIORITY_ICONS.NORMAL;
                return (
                  <div key={msg.message_id} className="card" style={{ cursor: 'pointer', borderLeft: `4px solid ${pi.color}`, opacity: msg.status === 'READ' || msg.status === 'ACKNOWLEDGED' ? 0.7 : 1 }}
                    onClick={() => loadThread(msg)}>
                    <div className="flex justify-between items-center">
                      <div style={{ flex: 1 }}>
                        <div className="flex items-center gap-2">
                          <span>{pi.icon}</span>
                          <span style={{ fontWeight: msg.status === 'SENT' ? 600 : 400, fontSize: 14 }}>{msg.subject}</span>
                          {msg.status === 'SENT' && <span className="badge badge-elevated" style={{ fontSize: 10 }}>{t('New', 'ಹೊಸ')}</span>}
                        </div>
                        <div style={{ fontSize: 12, color: 'var(--text-muted)', marginTop: 2 }}>
                          {t('From', 'ರಿಂದ')}: {msg.sender.rank} #{msg.sender.employee_id} · {msg.sender.unit?.unit_name || ''} · {msg.sent_at ? new Date(msg.sent_at).toLocaleString('en-IN') : ''}
                        </div>
                        <div style={{ fontSize: 13, color: 'var(--text-secondary)', marginTop: 4, whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: 500 }}>{msg.body}</div>
                      </div>
                      <div className="flex gap-2 items-center">
                        {msg.type === 'APPROVAL_REQUEST' && msg.status === 'SENT' && (
                          <button className="btn btn-primary btn-sm" onClick={e => { e.stopPropagation(); handleAck(msg); }}>
                            <CheckCircle size={14} /> {t('ACK', 'ಸ್ವೀಕಾರ')}
                          </button>
                        )}
                        <ChevronDown size={16} style={{ color: 'var(--text-muted)' }} />
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Detail panel */}
        {selectedMsg && (
          <div className="card" style={{ width: 420, flexShrink: 0, maxHeight: '80vh', overflow: 'auto' }}>
            <div className="card-header flex justify-between items-center">
              <span className="flex items-center gap-2"><MessageSquare size={16} /> {t('Thread', 'ಥ್ರೆಡ್')}</span>
              <button className="btn btn-ghost btn-icon" onClick={() => setSelectedMsg(null)}><X size={18} /></button>
            </div>
            {thread.map((m, i) => (
              <div key={m.message_id} style={{ marginBottom: 12, padding: 12, background: i === thread.length - 1 ? 'var(--bg-hover)' : 'transparent', borderRadius: 8, border: '1px solid var(--border)' }}>
                <div className="flex justify-between items-center" style={{ marginBottom: 4 }}>
                  <span style={{ fontWeight: 600, fontSize: 13 }}>{m.sender.rank} #{m.sender.employee_id}</span>
                  <span className="text-xs text-muted">{m.sent_at ? new Date(m.sent_at).toLocaleString('en-IN') : ''}</span>
                </div>
                <div className="flex gap-2" style={{ marginBottom: 4 }}>
                  <span className={`badge ${m.priority === 'CRITICAL' ? 'badge-elevated' : m.priority === 'HIGH' ? 'badge-moderate' : 'badge-low'}`} style={{ fontSize: 10 }}>{m.priority}</span>
                  <span className="badge badge-info" style={{ fontSize: 10 }}>{m.type}</span>
                  <span className="badge" style={{ fontSize: 10, background: 'var(--bg-hover)', color: 'var(--text-muted)' }}>{m.status}</span>
                </div>
                <p style={{ fontSize: 13, color: 'var(--text-secondary)', marginBottom: 8 }}>{m.body}</p>
                {m.attachments?.length > 0 && (
                  <div className="flex gap-2" style={{ marginBottom: 8 }}>
                    {m.attachments.map(a => (
                      <span key={a.file_id} className="badge badge-info" style={{ fontSize: 10 }}><Paperclip size={10} /> {a.file_name}</span>
                    ))}
                  </div>
                )}
                {m.linked_resources?.map((lr, li) => (
                  <span key={li} className="badge badge-moderate" style={{ fontSize: 10, marginRight: 4 }}>{lr.resourceType}: {lr.resourceId}</span>
                ))}
                {i === thread.length - 1 && m.status === 'SENT' && (
                  <div className="flex gap-2" style={{ marginTop: 8 }}>
                    <button className="btn btn-primary btn-sm" onClick={() => handleAck(m)}><CheckCircle size={14} /> {t('Acknowledge', 'ಸ್ವೀಕರಿಸಿ')}</button>
                    <button className="btn btn-secondary btn-sm" onClick={() => { setSendForm(f => ({ ...f, to: String(m.sender.employee_id), subject: `Re: ${m.subject}` })); setShowSend(true); }}>
                      <Reply size={14} /> {t('Reply', 'ಉತ್ತರ')}
                    </button>
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
};
