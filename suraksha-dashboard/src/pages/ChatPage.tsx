import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, FileText, ChevronDown, ChevronUp, CheckCircle, AlertTriangle, HelpCircle, Volume2, VolumeX, MicOff, Activity, Plus, Paperclip, Trash2, LogOut, Languages } from 'lucide-react';
import { ChatMessage } from '../types';
import { api } from '../services/api';
import { useLanguage } from '../context/LanguageContext';
import { useAuth } from '../context/AuthContext';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';

const CONFIDENCE_COLORS: Record<string, string> = {
  high: '#22C55E', medium: '#F59E0B', low: '#EF4444', insufficient_data: '#6B7280',
};

const MessageQueryDrawer: React.FC<{ msg: ChatMessage }> = ({ msg }) => {
  const [open, setOpen] = useState(false);
  const hasPlan = msg.sql_text || (msg.tool_params && Object.keys(msg.tool_params).length > 0) ||
                  msg.data_quality_warnings?.length || msg.evidence_refs?.length;
  if (!hasPlan) return null;
  return (
    <div style={{ marginTop: 8 }}>
      <button className="btn btn-ghost btn-sm" onClick={() => setOpen(!open)} style={{ fontSize: 12 }}>
        {open ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
        {' '}Query Plan
      </button>
      {open && (
        <div style={{ marginTop: 8, background: 'var(--bg-secondary)', borderRadius: 8, padding: 12, fontSize: 12 }}>
          {msg.confidence_class && (
            <div style={{ display: 'flex', gap: 12, marginBottom: 8, alignItems: 'center' }}>
              <span style={{ color: CONFIDENCE_COLORS[msg.confidence_class] || '#6B7280', fontWeight: 600 }}>
                {msg.confidence_class === 'high' && <CheckCircle size={14} style={{ verticalAlign: 'middle', marginRight: 4 }} />}
                {msg.confidence_class === 'medium' && <AlertTriangle size={14} style={{ verticalAlign: 'middle', marginRight: 4 }} />}
                {msg.confidence_class === 'low' && <HelpCircle size={14} style={{ verticalAlign: 'middle', marginRight: 4 }} />}
                Confidence: {msg.confidence_class}
              </span>
              {msg.grounding_status && (
                <span className={`badge ${msg.grounding_status === 'verified' ? 'badge-info' : 'badge-elevated'}`}>
                  {msg.grounding_status}
                </span>
              )}
            </div>
          )}
          {msg.sql_text && (
            <div style={{ marginBottom: 8 }}>
              <strong style={{ color: 'var(--text-muted)' }}>ZCQL:</strong>
              <pre style={{ margin: '4px 0 0', fontFamily: 'monospace', color: '#a6e3a1', whiteSpace: 'pre-wrap' }}>{msg.sql_text}</pre>
            </div>
          )}
          {msg.tool_params && Object.keys(msg.tool_params).length > 0 && (
            <div style={{ marginBottom: 8 }}>
              <strong style={{ color: 'var(--text-muted)' }}>Tool Params:</strong>
              <pre style={{ margin: '4px 0 0', fontFamily: 'monospace', color: '#89b4fa', whiteSpace: 'pre-wrap', fontSize: 11 }}>
                {JSON.stringify(msg.tool_params, null, 2)}
              </pre>
            </div>
          )}
          {msg.data_quality_warnings && msg.data_quality_warnings.length > 0 && (
            <div style={{ marginBottom: 8, color: 'var(--warning)' }}>
              <strong>Data Quality:</strong>
              {msg.data_quality_warnings.map((w, i) => <div key={i} style={{ marginTop: 2 }}>⚠ {w}</div>)}
            </div>
          )}
          {msg.evidence_refs && msg.evidence_refs.length > 0 && (
            <div>
              <strong style={{ color: 'var(--text-muted)' }}>Evidence:</strong>
              <div style={{ display: 'flex', gap: 4, flexWrap: 'wrap', marginTop: 4 }}>
                {msg.evidence_refs.map(ev => (
                  <span key={ev.evidence_id} className="badge badge-info">{ev.display_label}</span>
                ))}
              </div>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export const ChatPage: React.FC = () => {
  const [conversations, setConversations] = useState<any[]>([]);
  const [conversationId, setConversationId] = useState<string | null>(null);
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [recording, setRecording] = useState(false);
  const [playingMsgId, setPlayingMsgId] = useState<string | null>(null);

  const { lang, t, toggleLang } = useLanguage();
  const { logout } = useAuth();
  const endRef = useRef<HTMLDivElement>(null);
  const chatRef = useRef<HTMLDivElement>(null);
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  useEffect(() => {
    api.listConversations().then(setConversations).catch(() => {});
  }, []);

  useEffect(() => {
    const saved = sessionStorage.getItem('chat_conv_id');
    if (saved) loadConversation(saved);
  }, []);

  const loadConversation = async (id: string) => {
    try {
      const conv = await api.getConversation(id);
      setConversationId(id);
      sessionStorage.setItem('chat_conv_id', id);
      const msgs: ChatMessage[] = (conv.messages || []).map((m: any) => ({
        message_id: m.message_id,
        message_type: m.role === 'user' ? 'user_query' : (m.message_type || 'ai_response'),
        content_text: m.content_text || '',
        content_kannada: m.content_kannada,
        sql_text: m.sql_text,
        confidence_class: m.confidence_class,
        evidence_refs: m.evidence_json ? (typeof m.evidence_json === 'string' ? JSON.parse(m.evidence_json) : m.evidence_json) : [],
        suggested_followups: m.followups_json ? (typeof m.followups_json === 'string' ? JSON.parse(m.followups_json) : m.followups_json) : [],
        created_at: m.created_at || '',
      }));
      setMessages(msgs);
    } catch { /* ignore */ }
  };

  const newConversation = () => {
    setConversationId(null);
    setMessages([]);
    sessionStorage.removeItem('chat_conv_id');
  };

  const refreshList = () => {
    api.listConversations().then(setConversations).catch(() => {});
  };

  const sendMessage = async (text?: string) => {
    const msg = (text ?? input).trim();
    if (!msg || loading) return;
    const userMsg: ChatMessage = {
      message_id: Math.random().toString(36).slice(2),
      message_type: 'user_query',
      content_text: msg,
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    try {
      const response = await api.chatQuery(msg, conversationId || undefined);
      if (!conversationId && response.conversation_id) {
        setConversationId(response.conversation_id);
        sessionStorage.setItem('chat_conv_id', response.conversation_id);
      }
      setMessages(prev => [...prev, response]);
      refreshList();
    } catch {
      setMessages(prev => [...prev, {
        message_id: Math.random().toString(36).slice(2),
        message_type: 'ai_response',
        content_text: 'Sorry, I encountered an error. Please try again.',
        created_at: new Date().toISOString(),
      }]);
    }
    setLoading(false);
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    let cid = conversationId;
    if (!cid) {
      try {
        const resp = await api.chatQuery(`Uploading file: ${file.name}`);
        cid = resp.conversation_id || null;
        setConversationId(cid);
        if (cid) sessionStorage.setItem('chat_conv_id', cid);
      } catch {
        setMessages(prev => [...prev, {
          message_id: Math.random().toString(36).slice(2),
          message_type: 'ai_response',
          content_text: 'Failed to create conversation for upload.',
          created_at: new Date().toISOString(),
        }]);
        if (fileRef.current) fileRef.current.value = '';
        return;
      }
    }
    setMessages(prev => [...prev, {
      message_id: Math.random().toString(36).slice(2),
      message_type: 'user_query',
      content_text: `📎 Uploading: ${file.name}`,
      created_at: new Date().toISOString(),
    }]);
    try {
      const res = await api.uploadFile(cid!, file);
      setMessages(prev => [...prev, {
        message_id: Math.random().toString(36).slice(2),
        message_type: 'file_upload',
        content_text: `File uploaded: ${res.file_name}`,
        created_at: new Date().toISOString(),
      }]);
      refreshList();
    } catch {
      setMessages(prev => [...prev, {
        message_id: Math.random().toString(36).slice(2),
        message_type: 'ai_response',
        content_text: 'File upload failed.',
        created_at: new Date().toISOString(),
      }]);
    }
    if (fileRef.current) fileRef.current.value = '';
  };

  const handleMicClick = () => {
    if (recording) return;
    setRecording(true);
    setTimeout(async () => {
      setRecording(false);
      try {
        let mockBytes = [77, 79, 67, 75, 95, 69, 78];
        if (lang === 'kn') mockBytes = [77, 79, 67, 75, 95, 75, 78];
        else if (lang === 'hi') mockBytes = [77, 79, 67, 75, 95, 72, 73];
        const text = await api.speechToText(mockBytes, lang);
        setInput(text);
      } catch { /* ignore */ }
    }, 2500);
  };

  const toggleSpeech = async (msg: ChatMessage) => {
    if (playingMsgId === msg.message_id) {
      if (audioRef.current) { audioRef.current.pause(); audioRef.current = null; }
      setPlayingMsgId(null);
      return;
    }
    if (audioRef.current) audioRef.current.pause();
    const textToSpeak = lang === 'kn' && msg.content_kannada ? msg.content_kannada : msg.content_text;
    try {
      const audioBytes = await api.textToSpeech(textToSpeak, lang);
      const uint8 = new Uint8Array(audioBytes);
      const blob = new Blob([uint8], { type: 'audio/wav' });
      const url = URL.createObjectURL(blob);
      const audio = new Audio(url);
      audioRef.current = audio;
      setPlayingMsgId(msg.message_id);
      audio.onended = () => setPlayingMsgId(null);
      await audio.play();
    } catch { setPlayingMsgId(null); }
  };

  const exportPdf = async () => {
    if (!chatRef.current) return;
    const canvas = await html2canvas(chatRef.current, { backgroundColor: null });
    const imgData = canvas.toDataURL('image/png');
    const pdf = new jsPDF('p', 'mm', 'a4');
    const pdfWidth = pdf.internal.pageSize.getWidth();
    const pdfHeight = (canvas.height * pdfWidth) / canvas.width;
    let heightLeft = pdfHeight;
    let position = 0;
    const pageHeight = pdf.internal.pageSize.getHeight();
    pdf.addImage(imgData, 'PNG', 0, position, pdfWidth, pdfHeight);
    heightLeft -= pageHeight;
    while (heightLeft > 0) {
      position = heightLeft - pdfHeight;
      pdf.addPage();
      pdf.addImage(imgData, 'PNG', 0, position, pdfWidth, pdfHeight);
      heightLeft -= pageHeight;
    }
    pdf.save('suraksha-chat-export.pdf');
  };

  const sidebarWidth = 260;
  return (
    <div>
      <div className="page-header flex justify-between items-center">
        <div>
          <h1>{t('AI Chat', 'ಎಐ ಚಾಟ್')}</h1>
          <p>{t('Conversational crime intelligence interface', 'ಸಂವಾದಾತ್ಮಕ ಅಪರಾಧ ಗುಪ್ತಚರ ಇಂಟರ್ಫೇಸ್')}</p>
        </div>
        <div className="flex gap-2">
          <button className="btn btn-ghost btn-sm" onClick={toggleLang} title="Language">
            <Languages size={16} /> {lang === 'en' ? 'EN' : lang === 'kn' ? 'ಕನ್ನಡ' : 'हिंदी'}
          </button>
          <button className="btn btn-primary btn-sm" onClick={exportPdf}>
            <FileText size={16} /> {t('Export PDF', 'ಪಿಡಿಎಫ್ ರಫ್ತು')}
          </button>
          <button className="btn btn-ghost btn-sm" onClick={logout} title="Logout">
            <LogOut size={16} /> {t('Logout', 'ನಿರ್ಗಮಿಸಿ')}
          </button>
        </div>
      </div>

      <div style={{ display: 'flex', gap: 16, alignItems: 'stretch' }}>
        <div className="card" style={{ width: sidebarWidth, flexShrink: 0, display: 'flex', flexDirection: 'column', padding: 0, overflow: 'hidden' }}>
          <div style={{ padding: '12px', borderBottom: '1px solid var(--border)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <strong style={{ fontSize: 14 }}>{t('Conversations', 'ಸಂಭಾಷಣೆಗಳು')}</strong>
            <button className="btn btn-ghost btn-sm" onClick={newConversation} title="New Chat">
              <Plus size={16} />
            </button>
          </div>
          <div style={{ flex: 1, overflowY: 'auto', padding: '4px 0' }}>
            {conversations.map((c: any) => (
              <div key={c.conversation_id}
                onClick={() => loadConversation(c.conversation_id)}
                style={{
                  padding: '10px 12px', cursor: 'pointer', fontSize: 13,
                  borderLeft: conversationId === c.conversation_id ? '3px solid var(--accent)' : '3px solid transparent',
                  background: conversationId === c.conversation_id ? 'var(--bg-secondary)' : 'transparent',
                  display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 500, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {c.title || 'New Chat'}
                  </div>
                  <div style={{ fontSize: 11, color: 'var(--text-muted)', marginTop: 2 }}>
                    {c.message_count || 0} msgs · {(c.updated_at || '').slice(0, 10)}
                  </div>
                </div>
                <button className="btn btn-ghost btn-icon" style={{ opacity: 0.4, flexShrink: 0 }}
                  onClick={async (e) => { e.stopPropagation(); await api.deleteConversation(c.conversation_id); refreshList(); if (conversationId === c.conversation_id) newConversation(); }}
                  title="Delete">
                  <Trash2 size={14} />
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="card chat-container" ref={chatRef} style={{ flex: 1, minWidth: 0 }}>
          <div className="chat-messages">
            {messages.length === 0 && (
              <div className="message ai" style={{ textAlign: 'center', opacity: 0.7 }}>
                {lang === 'kn'
                  ? 'ನಮಸ್ಕಾರ! ನಾನು ಸುರಕ್ಷಾ ಎಐ. ಕರ್ನಾಟಕದ ಆಪರಾಧ ಡೇಟಾ ಕುರಿತು ಇಂಗ್ಲಿಷ್ ಅಥವಾ ಕನ್ನಡದಲ್ಲಿ ಕೇಳಿ.'
                  : 'Hello! I am Suraksha AI. Ask me about crime data in Karnataka — in English or Kannada.'}
              </div>
            )}
            {messages.map(msg => (
              <div key={msg.message_id}>
                {msg.message_type === 'file_upload' ? (
                  <div className="message ai" style={{ opacity: 0.8, fontSize: 13 }}>
                    <Paperclip size={14} style={{ marginRight: 6, verticalAlign: 'middle' }} />
                    {msg.content_text}
                  </div>
                ) : (
                  <div className={`message ${msg.message_type === 'user_query' ? 'user' : 'ai'}`}>
                    {msg.message_type === 'ai_response' && lang === 'kn' && msg.content_kannada
                      ? msg.content_kannada : msg.content_text}
                  </div>
                )}
                {msg.message_type !== 'file_upload' && (
                  <div style={{ display: 'flex', gap: 12, alignItems: 'center' }}>
                    <MessageQueryDrawer msg={msg} />
                    {msg.message_type === 'ai_response' && (
                      <button className="btn btn-ghost btn-sm" onClick={() => toggleSpeech(msg)} style={{ fontSize: 12, padding: '4px 8px' }}>
                        {playingMsgId === msg.message_id ? <VolumeX size={14} style={{ marginRight: 4, color: 'var(--accent)' }} /> : <Volume2 size={14} style={{ marginRight: 4 }} />}
                        {playingMsgId === msg.message_id ? t('Mute', 'ಮೌನಗೊಳಿಸು') : t('Listen', 'ಕೇಳಿ')}
                      </button>
                    )}
                  </div>
                )}
                {msg.suggested_followups && msg.suggested_followups.length > 0 && (
                  <div style={{ marginTop: 8, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                    {msg.suggested_followups.map((s, i) => (
                      <button key={i} className="btn btn-ghost btn-sm" onClick={() => sendMessage(s)}>{s}</button>
                    ))}
                  </div>
                )}
              </div>
            ))}
            {loading && <div className="message ai"><div className="skeleton" style={{ width: 200, height: 20 }} /></div>}
            <div ref={endRef} />
          </div>

          {recording && (
            <div style={{ display: 'flex', gap: 8, justifyContent: 'center', alignItems: 'center', background: 'var(--bg-secondary)', padding: '8px 16px', borderRadius: 8, margin: '8px 16px', border: '1px solid var(--accent)' }}>
              <Activity size={16} className="animate-pulse" style={{ color: 'var(--accent)' }} />
              <span style={{ fontSize: 13, fontWeight: 500, color: 'var(--text-primary)' }}>
                {lang === 'kn' ? 'ಕನ್ನಡ ಧ್ವನಿ ರೆಕಾರ್ಡ್ ಮಾಡಲಾಗುತ್ತಿದೆ...' : 'Recording speech input (simulated)...'}
              </span>
            </div>
          )}

          <div className="chat-input-area">
            <input className="input" placeholder={recording ? t('Listening...', 'ಕೇಳಿಸಿಕೊಳ್ಳಲಾಗುತ್ತಿದೆ...') : t('Ask about crime data...', 'ಅಪರಾಧ ಡೇಟಾ ಕುರಿತು ಕೇಳಿ...')} value={input}
              disabled={recording} onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendMessage()} />
            <input ref={fileRef} type="file" style={{ display: 'none' }} onChange={handleFileSelect} />
            <button className="btn btn-ghost btn-icon" onClick={() => fileRef.current?.click()} disabled={loading} title="Upload file">
              <Paperclip size={18} />
            </button>
            <button className={`btn btn-ghost btn-icon ${recording ? 'active animate-pulse' : ''}`} onClick={handleMicClick} disabled={loading || recording}>
              {recording ? <MicOff size={18} style={{ color: 'var(--accent)' }} /> : <Mic size={18} />}
            </button>
            <button className="btn btn-primary btn-icon" onClick={() => sendMessage()} disabled={loading || recording}>
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};