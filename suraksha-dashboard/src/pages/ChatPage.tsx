import React, { useState, useRef, useEffect } from 'react';
import { Send, Mic, FileText, Eye, EyeOff } from 'lucide-react';
import { ChatMessage } from '../types';
import { api } from '../services/api';
import { useLanguage } from '../context/LanguageContext';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';

export const ChatPage: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([
    { message_id: '0', message_type: 'ai_response', content_text: 'Hello! I am Suraksha AI. Ask me about crime data in Karnataka — in English or Kannada.', content_kannada: 'ನಮಸ್ಕಾರ! ನಾನು ಸುರಕ್ಷಾ ಎಐ. ಕರ್ನಾಟಕದ ಅಪರಾಧ ಡೇಟಾ ಕುರಿತು ಇಂಗ್ಲಿಷ್ ಅಥವಾ ಕನ್ನಡದಲ್ಲಿ ಕೇಳಿ.', created_at: '' },
  ]);
  const [input, setInput] = useState('');
  const [showSql, setShowSql] = useState(false);
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
          <button className="btn btn-secondary btn-sm" onClick={() => setShowSql(!showSql)}>
            {showSql ? <EyeOff size={16} /> : <Eye size={16} />} {showSql ? 'Hide SQL' : 'Show SQL'}
          </button>
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
              {showSql && msg.sql_text && (
                <div style={{ marginTop: 4, marginBottom: 8, padding: '8px 12px', background: 'var(--bg-secondary)', borderRadius: 8, fontFamily: 'monospace', fontSize: 11, color: 'var(--text-muted)', overflowX: 'auto', maxWidth: '80%' }}>
                  {msg.sql_text}
                </div>
              )}
              {msg.evidence_refs && msg.evidence_refs.length > 0 && (
                <div style={{ marginTop: 8, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {msg.evidence_refs.map(ev => (
                    <span key={ev.evidence_id} className="badge badge-info">{ev.display_label}</span>
                  ))}
                </div>
              )}
              {msg.suggested_followups && msg.suggested_followups.length > 0 && (
                <div style={{ marginTop: 12, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
                  {msg.suggested_followups.map((s, i) => (
                    <button key={i} className="btn btn-ghost btn-sm" onClick={() => { setInput(s); }}>
                      {s}
                    </button>
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
