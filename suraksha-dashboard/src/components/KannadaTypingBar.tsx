import React, { useState, useEffect, useCallback } from 'react';
import { Keyboard, X } from 'lucide-react';
import { useLanguage } from '../context/LanguageContext';

// ponytail: simple phonetic mapping, full Akshara mukha integration when available
const PHONETIC_MAP: Record<string, string> = {
  'a': 'ಅ', 'aa': 'ಆ', 'i': 'ಇ', 'ii': 'ಈ', 'u': 'ಉ', 'uu': 'ಊ',
  'e': 'ಎ', 'ee': 'ಏ', 'ai': 'ಐ', 'o': 'ಒ', 'oo': 'ಓ', 'au': 'ಔ',
  'ka': 'ಕ', 'kha': 'ಖ', 'ga': 'ಗ', 'gha': 'ಘ', 'nga': 'ಙ',
  'ca': 'ಚ', 'cha': 'ಛ', 'ja': 'ಜ', 'jha': 'ಝ', 'nya': 'ಞ',
  'ta': 'ಟ', 'tha': 'ಠ', 'da': 'ಡ', 'dha': 'ಢ', 'na': 'ಣ',
  't': 'ತ', 'th': 'ಥ', 'd': 'ದ', 'dh': 'ಧ', 'n': 'ನ',
  'pa': 'ಪ', 'pha': 'ಫ', 'ba': 'ಬ', 'bha': 'ಭ', 'ma': 'ಮ',
  'ya': 'ಯ', 'ra': 'ರ', 'la': 'ಲ', 'va': 'ವ', 'sha': 'ಶ',
  'ssa': 'ಷ', 'sa': 'ಸ', 'ha': 'ಹ', 'lla': 'ಳ',
  'ksha': 'ಕ್ಷ', 'jnya': 'ಜ್ಞ',
  '0': '೦', '1': '೧', '2': '೨', '3': '೩', '4': '೪',
  '5': '೫', '6': '೬', '7': '೭', '8': '೮', '9': '೯',
};

const TYPEWRITER_KEYS = [
  ['ಅ', 'ಆ', 'ಇ', 'ಈ', 'ಉ', 'ಊ', 'ಋ'],
  ['ಎ', 'ಏ', 'ಐ', 'ಒ', 'ಓ', 'ಔ', 'ಅಂ'],
  ['ಕ', 'ಖ', 'ಗ', 'ಘ', 'ಙ', 'ಚ', 'ಛ'],
  ['ಜ', 'ಝ', 'ಞ', 'ಟ', 'ಠ', 'ಡ', 'ಢ'],
  ['ಣ', 'ತ', 'ಥ', 'ದ', 'ಧ', 'ನ', 'ಪ'],
  ['ಫ', 'ಬ', 'ಭ', 'ಮ', 'ಯ', 'ರ', 'ಲ'],
  ['ವ', 'ಶ', 'ಷ', 'ಸ', 'ಹ', 'ಳ', 'ಕ್ಷ'],
];

interface Props {
  targetInput: string | null;
  onInput: (text: string) => void;
  onClose: () => void;
}

export const KannadaTypingBar: React.FC<Props> = ({ targetInput, onInput, onClose }) => {
  const { t } = useLanguage();
  const [mode, setMode] = useState<'phonetic' | 'typewriter'>('phonetic');
  const [buffer, setBuffer] = useState('');

  const handlePhoneticKey = useCallback((key: string) => {
    setBuffer(prev => {
      const newBuf = prev + key;
      // Try longest match first
      for (let len = Math.min(newBuf.length, 4); len >= 1; len--) {
        const chunk = newBuf.slice(-len);
        if (PHONETIC_MAP[chunk]) {
          const prefix = newBuf.slice(0, -len);
          onInput(PHONETIC_MAP[chunk]);
          return prefix;
        }
      }
      return newBuf;
    });
  }, [onInput]);

  const handleTypewriterKey = (char: string) => {
    onInput(char);
  };

  useEffect(() => {
    if (mode !== 'phonetic') return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === ' ') { handlePhoneticKey(' '); e.preventDefault(); }
      else if (e.key === 'Backspace') { setBuffer(prev => prev.slice(0, -1)); }
      else if (e.key.length === 1 && /[a-zA-Z0-9]/.test(e.key)) { handlePhoneticKey(e.key); }
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, [mode, handlePhoneticKey]);

  if (!targetInput) return null;

  return (
    <div style={{
      position: 'fixed', bottom: 0, left: 0, right: 0, zIndex: 2000,
      background: 'var(--bg-card)', borderTop: '2px solid var(--primary)',
      padding: '12px 24px', boxShadow: '0 -4px 20px rgba(0,0,0,0.15)'
    }}>
      <div className="flex justify-between items-center" style={{ marginBottom: 8 }}>
        <div className="flex items-center gap-2">
          <Keyboard size={16} />
          <span style={{ fontSize: 13, fontWeight: 600 }}>{t('Kannada Input', 'ಕನ್ನಡ ಇನ್‌ಪುಟ್')}</span>
          <span className="text-xs text-muted" style={{ background: 'var(--bg-hover)', padding: '2px 8px', borderRadius: 4 }}>
            {targetInput}
          </span>
        </div>
        <div className="flex items-center gap-2">
          <button className={`btn btn-ghost btn-sm ${mode === 'phonetic' ? 'active' : ''}`} onClick={() => setMode('phonetic')}>
            {t('Phonetic', 'ಫೋನೆಟಿಕ್')}
          </button>
          <button className={`btn btn-ghost btn-sm ${mode === 'typewriter' ? 'active' : ''}`} onClick={() => setMode('typewriter')}>
            {t('Typewriter', 'ಟೈಪ್‌ರೈಟರ್')}
          </button>
          <button className="btn btn-ghost btn-icon" onClick={onClose}><X size={16} /></button>
        </div>
      </div>

      {mode === 'phonetic' && (
        <div style={{ fontSize: 13, color: 'var(--text-muted)' }}>
          {t('Type using English keyboard (e.g., "namaskara" → ನಮಸ್ಕಾರ)', 'ಇಂಗ್ಲಿಷ್ ಕೀಬೋರ್ಡ್ ಬಳಸಿ ಟೈಪ್ ಮಾಡಿ (ಉದಾ: "namaskara" → ನಮಸ್ಕಾರ)')}
          {buffer && <span style={{ color: 'var(--warning)', marginLeft: 8 }}>({buffer})</span>}
        </div>
      )}

      {mode === 'typewriter' && (
        <div style={{ overflowX: 'auto' }}>
          {TYPEWRITER_KEYS.map((row, ri) => (
            <div key={ri} className="flex gap-1" style={{ marginBottom: 4, justifyContent: 'center' }}>
              {row.map(char => (
                <button key={char} type="button"
                  style={{
                    width: 36, height: 36, border: '1px solid var(--border)', borderRadius: 6,
                    background: 'var(--bg-hover)', cursor: 'pointer', fontSize: 16, color: 'var(--text-primary)'
                  }}
                  onClick={() => handleTypewriterKey(char)}>
                  {char}
                </button>
              ))}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
