import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, FileText, ChevronDown, ChevronUp, CheckCircle, AlertTriangle, HelpCircle } from 'lucide-react';
import { ChatMessage } from '../types';
import { api } from '../services/api';
import { useLanguage } from '../context/LanguageContext';
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
  const [messages, setMessages] = useState<ChatMessage[]>([
    { message_id: '0', message_type: 'ai_response', content_text: 'Hello! I am Suraksha AI. Ask me about crime data in Karnataka — in English or Kannada.', content_kannada: 'ನಮಸ್ಕಾರ! ನಾನು ಸುರಕ್ಷಾ ಎಐ. ಕರ್ನಾಟಕದ ಅಪರಾಧ ಡೇಟಾ ಕುರಿತು ಇಂಗ್ಲಿಷ್ ಅಥವಾ ಕನ್ನಡದಲ್ಲಿ ಕೇಳಿ.', created_at: '' },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const { lang, t } = useLanguage();
  const endRef = useRef<HTMLDivElement>(null);
  const chatRef = useRef<HTMLDivElement>(null);

  useEffect(() => { endRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [messages]);

  const sendMessage = async () => {
    if (!input.trim() || loading) return;
    const userMsg: ChatMessage = {
      message_id: Math.random().toString(36).slice(2),
      message_type: 'user_query',
      content_text: input,
      created_at: new Date().toISOString(),
    };
    setMessages(prev => [...prev, userMsg]);
    setInput('');
    setLoading(true);
    try {
      const response = await api.chatQuery(input);
      setMessages(prev => [...prev, response]);
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

  return (
    <div>
      <div className="page-header flex justify-between items-center">
        <div>
          <h1>{t('AI Chat', 'ಎಐ ಚಾಟ್')}</h1>
          <p>{t('Conversational crime intelligence interface', 'ಸಂವಾದಾತ್ಮಕ ಅಪರಾಧ ಗುಪ್ತಚರ ಇಂಟರ್ಫೇಸ್')}</p>
        </div>
        <div className="flex gap-2">
          <button className="btn btn-primary btn-sm" onClick={exportPdf}>
            <FileText size={16} /> {t('Export PDF', 'ಪಿಡಿಎಫ್ ರಫ್ತು')}
          </button>
        </div>
      </div>

      <div className="card chat-container" ref={chatRef}>
        <div className="chat-messages">
          {messages.map(msg => (
            <div key={msg.message_id}>
              <div className={`message ${msg.message_type === 'user_query' ? 'user' : 'ai'}`}>
                {msg.message_type === 'ai_response' && lang === 'kn' && msg.content_kannada
                  ? msg.content_kannada : msg.content_text}
              </div>
              <MessageQueryDrawer msg={msg} />
              {msg.suggested_followups && msg.suggested_followups.length > 0 && (
                <div style={{ marginTop: 8, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {msg.suggested_followups.map((s, i) => (
                    <button key={i} className="btn btn-ghost btn-sm" onClick={() => setInput(s)}>{s}</button>
                  ))}
                </div>
              )}
            </div>
          ))}
          {loading && <div className="message ai"><div className="skeleton" style={{ width: 200, height: 20 }} /></div>}
          <div ref={endRef} />
        </div>

        <div className="chat-input-area">
          <input className="input" placeholder={t('Ask about crime data...', 'ಅಪರಾಧ ಡೇಟಾ ಕುರಿತು ಕೇಳಿ...')} value={input}
            onChange={e => setInput(e.target.value)} onKeyDown={e => e.key === 'Enter' && sendMessage()} />
          <button className="btn btn-ghost btn-icon"><Mic size={18} /></button>
          <button className="btn btn-primary btn-icon" onClick={sendMessage} disabled={loading}>
            <Send size={18} />
          </button>
        </div>
      </div>
    </div>
  );
};
