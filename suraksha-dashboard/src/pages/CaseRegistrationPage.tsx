import React, { useState } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { useAuth } from '../context/AuthContext';
import { Send, Plus, Trash2, Bot, ChevronDown, ChevronUp, CheckCircle, MapPin, HelpCircle, AlertTriangle } from 'lucide-react';

const crimeCategories = ['FIR', 'UDR', 'PAR', 'Zero FIR'];
const gravityOffences = ['Heinous', 'Non-Heinous'];
const majorHeads = ['Crimes Against Body', 'Crimes Against Property', 'Crimes Against Women', 'Crimes Against Children', 'Economic Offences', 'Cyber Crimes', 'Other Offences'];
const minorHeads: Record<string, string[]> = {
  'Crimes Against Body': ['Murder', 'Attempt to Murder', 'Grievous Hurt', 'Simple Hurt', 'Rape', 'Kidnapping & Abduction'],
  'Crimes Against Property': ['Robbery', 'Burglary', 'Theft', 'Dacoity', 'Criminal Trespass'],
  'Crimes Against Women': ['Dowry Death', 'Cruelty by Husband', 'Sexual Harassment', 'Molestation'],
  'Crimes Against Children': ['Child Marriage', 'Child Labour', 'Child Sexual Abuse', 'Kidnapping of Minor'],
  'Economic Offences': ['Cheating', 'Forgery', 'Counterfeiting', 'Corruption'],
  'Cyber Crimes': ['Phishing', 'Online Fraud', 'Identity Theft', 'Cyber Stalking'],
  'Other Offences': ['Rioting', 'Public Nuisance', 'Criminal Intimidation', 'Unlawful Assembly'],
};
const occupations = ['Farmer', 'Labourer', 'Business', 'Private Employee', 'Government Employee', 'Student', 'Unemployed', 'Retired', 'Housewife', 'Other'];
const religions = ['Hinduism', 'Islam', 'Christianity', 'Sikhism', 'Jainism', 'Buddhism', 'Other'];
const castes = ['General', 'OBC', 'SC', 'ST', 'Other'];
const acts = ['IPC', 'CrPC', 'Indian Evidence Act', 'NDPS Act', 'IT Act', 'Arms Act', 'Dowry Prohibition Act', 'POCSO Act'];
const sections: Record<string, string[]> = {
  'IPC': ['302 (Murder)', '307 (Attempt to Murder)', '324 (Grievous Hurt)', '323 (Simple Hurt)', '376 (Rape)', '379 (Theft)', '392 (Robbery)', '395 (Dacoity)', '420 (Cheating)', '498A (Cruelty by Husband)'],
  'CrPC': ['41 (Arrest)', '154 (FIR)', '161 (Examination of Witnesses)', '164 (Recording of Confession)', '167 (Remand)'],
  'NDPS Act': ['8 (Prohibition)', '15 (Commercial Quantity)', '20 (Cultivation)'],
  'IT Act': ['66 (Computer Related Offences)', '67 (Publishing Obscene Material)'],
  'Arms Act': ['25 (Arms without License)', '27 (Use of Arms)'],
};
const definitions: Record<string, string> = {
  '302 (Murder)': 'Punishment for murder — death or life imprisonment + fine',
  '307 (Attempt to Murder)': 'Attempt to murder — up to 10 years + fine',
  '376 (Rape)': 'Punishment for rape — rigorous imprisonment 10 years to life',
  '379 (Theft)': 'Punishment for theft — up to 3 years or fine or both',
  '392 (Robbery)': 'Punishment for robbery — rigorous imprisonment up to 10 years',
  '420 (Cheating)': 'Cheating and dishonestly inducing delivery of property',
};

const generatedCrimeNo = () => `10443${String(1).padStart(4, '0')}${String(new Date().getFullYear()).slice(-4)}${String(Math.floor(Math.random() * 100000)).padStart(5, '0')}`;

interface FormState {
  incident_from: string; incident_to: string; incident_location: string; lat: string; lng: string; brief_facts: string;
  complainant_name: string; complainant_age: string; complainant_gender: string; complainant_occupation: string;
  complainant_religion: string; complainant_caste: string; complainant_contact: string; complainant_email: string;
  victims: { name: string; age: string; gender: string; isPolice: boolean }[];
  accuseds: { name: string; age: string; gender: string; sorting_id: string }[];
  crime_category: string; gravity_offence: string; crime_major_head: string; crime_minor_head: string;
  acts_sections: { act: string; section: string }[];
}

const emptyForm = (): FormState => ({
  incident_from: '', incident_to: '', incident_location: '', lat: '', lng: '', brief_facts: '',
  complainant_name: '', complainant_age: '', complainant_gender: 'm', complainant_occupation: '',
  complainant_religion: '', complainant_caste: '', complainant_contact: '', complainant_email: '',
  victims: [], accuseds: [],
  crime_category: '', gravity_offence: '', crime_major_head: '', crime_minor_head: '',
  acts_sections: [],
});

const REQUIRED_FIELDS: { step: number; field: keyof FormState; label: string }[] = [
  { step: 1, field: 'incident_from', label: 'Incident From Date' },
  { step: 1, field: 'incident_location', label: 'Incident Location' },
  { step: 1, field: 'brief_facts', label: 'Brief Facts' },
  { step: 2, field: 'complainant_name', label: 'Complainant Name' },
  { step: 2, field: 'complainant_age', label: 'Complainant Age' },
  { step: 5, field: 'crime_category', label: 'Crime Category' },
  { step: 5, field: 'gravity_offence', label: 'Gravity Offence' },
];

export const CaseRegistrationPage: React.FC = () => {
  const { t } = useLanguage();
  const { user } = useAuth();
  const [step, setStep] = useState(1);
  const [showCaseBot, setShowCaseBot] = useState(true);
  const [submitted, setSubmitted] = useState(false);
  const [crimeNo] = useState(generatedCrimeNo);
  const [view, setView] = useState<'register' | 'status'>('register');
  const [form, setForm] = useState<FormState>(emptyForm);
  const [caseBotMsg, setCaseBotMsg] = useState(t('I am CaseBot. I can help with your FIR registration.', 'ನಾನು ಕೇಸ್‌ಬಾಟ್. ನಿಮ್ಮ ಎಫ್ಐಆರ್ ನೋಂದಣಿಗೆ ಸಹಾಯ ಮಾಡಬಲ್ಲೆ.'));
  const [botConfidence, setBotConfidence] = useState<{ missing: string[] } | null>(null);
  const [showMapPicker, setShowMapPicker] = useState(false);

  const wordCount = form.brief_facts.split(/\s+/).filter(Boolean).length;

  const addVictim = () => setForm(f => ({ ...f, victims: [...f.victims, { name: '', age: '', gender: 'm', isPolice: false }] }));
  const removeVictim = (i: number) => setForm(f => ({ ...f, victims: f.victims.filter((_, idx) => idx !== i) }));
  const updVictim = (i: number, k: string, v: any) => setForm(f => {
    const victims = [...f.victims]; (victims[i] as any)[k] = v; return { ...f, victims };
  });

  const addAccused = () => setForm(f => ({ ...f, accuseds: [...f.accuseds, { name: '', age: '', gender: 'm', sorting_id: `A${f.accuseds.length + 1}` }] }));
  const removeAccused = (i: number) => setForm(f => ({ ...f, accuseds: f.accuseds.filter((_, idx) => idx !== i) }));
  const updAccused = (i: number, k: string, v: any) => setForm(f => {
    const accuseds = [...f.accuseds]; (accuseds[i] as any)[k] = v; return { ...f, accuseds };
  });

  const addActSection = () => setForm(f => ({ ...f, acts_sections: [...f.acts_sections, { act: '', section: '' }] }));
  const updActSection = (i: number, k: string, v: string) => setForm(f => {
    const acts_sections = [...f.acts_sections]; (acts_sections[i] as any)[k] = v; return { ...f, acts_sections };
  });
  const removeActSection = (i: number) => setForm(f => ({ ...f, acts_sections: f.acts_sections.filter((_, idx) => idx !== i) }));

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitted(true);
  };

  const checkConfidence = () => {
    const missing = REQUIRED_FIELDS
      .filter(rf => rf.step === step)
      .filter(rf => !(form[rf.field] as string)?.trim())
      .map(rf => rf.label);
    setBotConfidence({ missing });
    const total = REQUIRED_FIELDS.filter(rf => rf.step === step).length;
    const filled = total - missing.length;
    const pct = total > 0 ? Math.round((filled / total) * 100) : 100;
    setCaseBotMsg(
      pct === 100
        ? t(`Step ${step} looks complete! (${pct}% filled)`, `ಹಂತ ${step} ಪೂರ್ಣವಾಗಿದೆ! (${pct}% ಭರ್ತಿ)`)
        : t(`Step ${step}: ${pct}% filled. Missing: ${missing.join(', ')}`, `ಹಂತ ${step}: ${pct}% ಭರ್ತಿ. ಕಾಣೆಯಾಗಿದೆ: ${missing.join(', ')}`)
    );
  };

  const autoFillSimilar = () => {
    setForm(f => ({
      ...f,
      incident_location: 'Bengaluru South, Main Road',
      crime_category: 'FIR',
      gravity_offence: 'Non-Heinous',
      crime_major_head: 'Crimes Against Property',
      crime_minor_head: 'Theft',
    }));
    setCaseBotMsg(t('Auto-filled from similar case #104430006202500312 (Theft, Bengaluru South)', 'ಹೋಲುವ ಪ್ರಕರಣ #104430006202500312 (ಕಳ್ಳತನ, ಬೆಂಗಳೂರು ದಕ್ಷಿಣ) ನಿಂದ ಸ್ವಯಂ-ಭರ್ತಿ ಮಾಡಲಾಗಿದೆ'));
  };

  if (submitted) {
    return (
      <div>
        <div className="page-header">
          <h1>{t('Case Registration', 'ಪ್ರಕರಣ ನೋಂದಣಿ')}</h1>
        </div>
        <div className="card" style={{ textAlign: 'center', padding: 64 }}>
          <CheckCircle size={64} style={{ color: 'var(--success)', marginBottom: 16 }} />
          <h2 style={{ marginBottom: 8 }}>{t('FIR Registered Successfully', 'ಎಫ್‍ಐಆರ್ ಯಶಸ್ವಿಯಾಗಿ ನೋಂದಾಯಿಸಲಾಗಿದೆ')}</h2>
          <p style={{ fontSize: 24, fontWeight: 700, color: 'var(--primary)', marginBottom: 4, fontFamily: 'monospace' }}>{crimeNo}</p>
          <p className="text-muted" style={{ marginBottom: 32 }}>{t('Crime Number', 'ಅಪರಾಧ ಸಂಖ್ಯೆ')}</p>
          <div className="flex gap-4" style={{ justifyContent: 'center' }}>
            <button className="btn btn-primary" onClick={() => { setSubmitted(false); setForm(emptyForm()); setView('status'); }}>
              {t('View Case Status', 'ಪ್ರಕರಣ ಸ್ಥಿತಿ ವೀಕ್ಷಿಸಿ')}
            </button>
            <button className="btn btn-secondary" onClick={() => { setSubmitted(false); setForm(emptyForm()); setStep(1); }}>
              {t('Register Another', 'ಮತ್ತೊಂದು ನೋಂದಾಯಿಸಿ')}
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (view === 'status') {
    return (
      <div>
        <div className="page-header flex justify-between items-center">
          <div>
            <h1>{t('Case Status Dashboard', 'ಪ್ರಕರಣ ಸ್ಥಿತಿ ಡ್ಯಾಶ್‌ಬೋರ್ಡ್')}</h1>
            <p>{t('Crime No', 'ಅಪರಾಧ ಸಂಖ್ಯೆ')}: <strong>{crimeNo}</strong></p>
          </div>
          <button className="btn btn-secondary btn-sm" onClick={() => setView('register')}>
            {t('New Registration', 'ಹೊಸ ನೋಂದಣಿ')}
          </button>
        </div>

        <div className="grid-3" style={{ marginBottom: 24 }}>
          <div className="card">
            <div className="card-header">{t('Case Summary', 'ಪ್ರಕರಣ ಸಾರಾಂಶ')}</div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
              <div style={{ marginBottom: 4 }}><strong>{t('Crime No', 'ಅಪರಾಧ ಸಂಖ್ಯೆ')}:</strong> <span style={{ fontFamily: 'monospace' }}>{crimeNo}</span></div>
              <div style={{ marginBottom: 4 }}><strong>{t('Category', 'ವರ್ಗ')}:</strong> {form.crime_category || 'FIR'}</div>
              <div style={{ marginBottom: 4 }}><strong>{t('Registered', 'ನೋಂದಾಯಿಸಲಾಗಿದೆ')}:</strong> {new Date().toLocaleDateString('en-IN')}</div>
              <div style={{ marginBottom: 4 }}><strong>{t('SHO', 'ಎಸ್ಎಚ್ಒ')}:</strong> {user?.first_name || '—'}</div>
              <div><strong>{t('IO', 'ತನಿಖಾಧಿಕಾರಿ')}:</strong> {t('To be assigned', 'ನಿಯೋಜಿಸಬೇಕಿದೆ')}</div>
            </div>
          </div>
          <div className="card">
            <div className="card-header">{t('Complainant', 'ದೂರುದಾರ')}</div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
              <div style={{ marginBottom: 4 }}><strong>{t('Name', 'ಹೆಸರು')}:</strong> {form.complainant_name || '—'}</div>
              <div style={{ marginBottom: 4 }}><strong>{t('Contact', 'ಸಂಪರ್ಕ')}:</strong> {form.complainant_contact || '—'}</div>
              <div><strong>{t('Occupation', 'ಉದ್ಯೋಗ')}:</strong> {form.complainant_occupation || '—'}</div>
            </div>
          </div>
          <div className="card">
            <div className="card-header">{t('Victims', 'ಬಲಿಪಶುಗಳು')}</div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
              <div style={{ marginBottom: 4 }}><strong>{t('Count', 'ಸಂಖ್ಯೆ')}:</strong> {form.victims.length}</div>
              {form.victims.slice(0, 3).map((v, i) => (
                <div key={i} style={{ fontSize: 12, color: 'var(--text-muted)' }}>• {v.name || t('Unnamed', 'ಹೆಸರಿಲ್ಲ')} ({v.age})</div>
              ))}
              {form.victims.length > 3 && <div className="text-xs text-muted">+{form.victims.length - 3} {t('more', 'ಹೆಚ್ಚು')}</div>}
            </div>
          </div>
        </div>

        <div className="grid-3" style={{ marginBottom: 24 }}>
          <div className="card">
            <div className="card-header">{t('Accused', 'ಆರೋಪಿಗಳು')}</div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
              <div style={{ marginBottom: 4 }}><strong>{t('Count', 'ಸಂಖ್ಯೆ')}:</strong> {form.accuseds.length}</div>
              {form.accuseds.map((a, i) => (
                <div key={i} style={{ fontSize: 12, color: 'var(--text-muted)' }}>• {a.sorting_id}: {a.name || t('Unnamed', 'ಹೆಸರಿಲ್ಲ')}</div>
              ))}
            </div>
          </div>
          <div className="card">
            <div className="card-header">{t('Legal Sections', 'ಕಾನೂನು ಸೆಕ್ಷನ್‌ಗಳು')}</div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
              {form.acts_sections.length === 0 && <span className="text-muted">{t('None added', 'ಯಾವುದನ್ನೂ ಸೇರಿಸಲಾಗಿಲ್ಲ')}</span>}
              {form.acts_sections.map((as, i) => (
                <div key={i} style={{ marginBottom: 4, position: 'relative' }}>
                  <span className="badge badge-info" style={{ fontSize: 11 }}>
                    {as.section || as.act || t('Pending', 'ಬಾಕಿ')}
                  </span>
                  {definitions[as.section] && (
                    <span style={{ fontSize: 11, color: 'var(--text-muted)', display: 'block', marginLeft: 4 }}>
                      {definitions[as.section]}
                    </span>
                  )}
                </div>
              ))}
            </div>
          </div>
          <div className="card">
            <div className="card-header">{t('Location', 'ಸ್ಥಳ')}</div>
            <div style={{ fontSize: 13, color: 'var(--text-secondary)' }}>
              <div style={{ marginBottom: 4 }}>{form.incident_location || '—'}</div>
              {form.lat && form.lng && (
                <span className="text-xs text-muted">{form.lat}, {form.lng}</span>
              )}
            </div>
          </div>
        </div>

        <div className="card">
          <div className="card-header">{t('Actions', 'ಕ್ರಿಯೆಗಳು')}</div>
          <div className="flex gap-3" style={{ flexWrap: 'wrap' }}>
            <button className="btn btn-primary btn-sm">{t('Edit Case', 'ಪ್ರಕರಣ ಸಂಪಾದಿಸಿ')}</button>
            <button className="btn btn-secondary btn-sm" onClick={addVictim}>{t('Add Victim', 'ಬಲಿಪಶು ಸೇರಿಸಿ')}</button>
            <button className="btn btn-secondary btn-sm" onClick={addAccused}>{t('Add Accused', 'ಆರೋಪಿ ಸೇರಿಸಿ')}</button>
            <button className="btn btn-secondary btn-sm" onClick={() => window.location.hash = '/workspace'}>{t('Record Arrest', 'ಬಂಧನ ದಾಖಲಿಸಿ')}</button>
            <button className="btn btn-secondary btn-sm">{t('View Chargesheet', 'ಪ್ರಸ್ತಾವನೆ ವೀಕ್ಷಿಸಿ')}</button>
            <button className="btn btn-secondary btn-sm">{t('Generate Report', 'ವರದಿ ರಚಿಸಿ')}</button>
          </div>
        </div>
      </div>
    );
  }

  const formContent = (
    <form onSubmit={handleSubmit}>
      {step === 1 && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-header"><h3>{t('Incident Details', 'ಘಟನೆಯ ವಿವರಗಳು')}</h3></div>
          <div className="grid-2">
            <div className="form-group">
              <label>{t('Incident From Date/Time', 'ಘಟನೆಯ ಆರಂಭ ದಿನಾಂಕ/ಸಮಯ')} *</label>
              <input className="input" type="datetime-local" value={form.incident_from} onChange={e => setForm(f => ({ ...f, incident_from: e.target.value }))} required />
            </div>
            <div className="form-group">
              <label>{t('Incident To Date/Time', 'ಘಟನೆಯ ಅಂತ್ಯ ದಿನಾಂಕ/ಸಮಯ')}</label>
              <input className="input" type="datetime-local" value={form.incident_to} onChange={e => setForm(f => ({ ...f, incident_to: e.target.value }))} />
            </div>
          </div>
          <div className="form-group">
            <label>{t('Incident Location', 'ಘಟನೆಯ ಸ್ಥಳ')} *</label>
            <div style={{ display: 'flex', gap: 8 }}>
              <input className="input" placeholder={t('Enter location description', 'ಸ್ಥಳ ವಿವರಣೆಯನ್ನು ನಮೂದಿಸಿ')} value={form.incident_location} onChange={e => setForm(f => ({ ...f, incident_location: e.target.value }))} required style={{ flex: 1 }} />
              <button type="button" className="btn btn-ghost btn-icon" onClick={() => setShowMapPicker(!showMapPicker)} title={t('Open map picker', 'ನಕ್ಷೆ ಪಿಕರ್ ತೆರೆಯಿರಿ')}><MapPin size={18} /></button>
            </div>
          </div>
          {showMapPicker && (
            <div className="grid-2" style={{ marginBottom: 12 }}>
              <div className="form-group">
                <label>{t('Latitude', 'ಅಕ್ಷಾಂಶ')}</label>
                <input className="input" type="number" step="0.0001" placeholder="12.9716" value={form.lat} onChange={e => setForm(f => ({ ...f, lat: e.target.value }))} />
              </div>
              <div className="form-group">
                <label>{t('Longitude', 'ರೇಖಾಂಶ')}</label>
                <input className="input" type="number" step="0.0001" placeholder="77.5946" value={form.lng} onChange={e => setForm(f => ({ ...f, lng: e.target.value }))} />
              </div>
            </div>
          )}
          <div className="form-group">
            <label>{t('Brief Facts', 'ಸಂಕ್ಷಿಪ್ತ ಸಂಗತಿಗಳು')} * <span className="text-xs text-muted">({wordCount} / 500-5000 {t('words', 'ಪದಗಳು')})</span></label>
            <textarea className="input" style={{ minHeight: 150, resize: 'vertical' }} value={form.brief_facts} onChange={e => setForm(f => ({ ...f, brief_facts: e.target.value }))} required />
            {wordCount > 0 && wordCount < 500 && <p className="text-xs" style={{ color: 'var(--warning)', marginTop: 4 }}>{t('Minimum 500 words required', 'ಕನಿಷ್ಠ 500 ಪದಗಳ ಅಗತ್ಯವಿದೆ')}</p>}
          </div>
          <div className="flex gap-4" style={{ justifyContent: 'flex-end', marginTop: 16 }}>
            <button type="button" className="btn btn-primary" onClick={() => setStep(2)}>{t('Next: Complainant', 'ಮುಂದೆ: ದೂರುದಾರ')}</button>
          </div>
        </div>
      )}

      {step === 2 && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-header"><h3>{t('Complainant Information', 'ದೂರುದಾರರ ಮಾಹಿತಿ')}</h3></div>
          <div className="grid-2">
            <div className="form-group">
              <label>{t('Full Name', 'ಸಂಪೂರ್ಣ ಹೆಸರು')} *</label>
              <input className="input" value={form.complainant_name} onChange={e => setForm(f => ({ ...f, complainant_name: e.target.value }))} required />
            </div>
            <div className="form-group">
              <label>{t('Age', 'ವಯಸ್ಸು')} *</label>
              <input className="input" type="number" min={1} max={150} value={form.complainant_age} onChange={e => setForm(f => ({ ...f, complainant_age: e.target.value }))} required />
            </div>
          </div>
          <div className="grid-3">
            <div className="form-group">
              <label>{t('Gender', 'ಲಿಂಗ')}</label>
              <select className="input" value={form.complainant_gender} onChange={e => setForm(f => ({ ...f, complainant_gender: e.target.value }))}>
                <option value="m">{t('Male', 'ಪುರುಷ')}</option>
                <option value="f">{t('Female', 'ಮಹಿಳೆ')}</option>
                <option value="t">{t('Transgender', 'ತೃತೀಯ ಲಿಂಗಿ')}</option>
              </select>
            </div>
            <div className="form-group">
              <label>{t('Occupation', 'ಉದ್ಯೋಗ')}</label>
              <select className="input" value={form.complainant_occupation} onChange={e => setForm(f => ({ ...f, complainant_occupation: e.target.value }))}>
                <option value="">-- {t('Select', 'ಆಯ್ಕೆಮಾಡಿ')} --</option>
                {occupations.map(o => <option key={o} value={o}>{o}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>{t('Religion', 'ಧರ್ಮ')}</label>
              <select className="input" value={form.complainant_religion} onChange={e => setForm(f => ({ ...f, complainant_religion: e.target.value }))}>
                <option value="">-- {t('Select', 'ಆಯ್ಕೆಮಾಡಿ')} --</option>
                {religions.map(r => <option key={r} value={r}>{r}</option>)}
              </select>
            </div>
          </div>
          <div className="grid-3">
            <div className="form-group">
              <label>{t('Caste', 'ಜಾತಿ')}</label>
              <select className="input" value={form.complainant_caste} onChange={e => setForm(f => ({ ...f, complainant_caste: e.target.value }))}>
                <option value="">-- {t('Select', 'ಆಯ್ಕೆಮಾಡಿ')} --</option>
                {castes.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>{t('Contact Number', 'ದೂರವಾಣಿ ಸಂಖ್ಯೆ')}</label>
              <input className="input" type="tel" value={form.complainant_contact} onChange={e => setForm(f => ({ ...f, complainant_contact: e.target.value }))} />
            </div>
            <div className="form-group">
              <label>{t('Email', 'ಇಮೇಲ್')}</label>
              <input className="input" type="email" value={form.complainant_email} onChange={e => setForm(f => ({ ...f, complainant_email: e.target.value }))} />
            </div>
          </div>
          <div className="flex gap-4" style={{ justifyContent: 'space-between', marginTop: 16 }}>
            <button type="button" className="btn btn-secondary" onClick={() => setStep(1)}>{t('Back', 'ಹಿಂದೆ')}</button>
            <button type="button" className="btn btn-primary" onClick={() => setStep(3)}>{t('Next: Victims', 'ಮುಂದೆ: ಬಲಿಪಶುಗಳು')}</button>
          </div>
        </div>
      )}

      {step === 3 && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-header flex justify-between items-center">
            <h3>{t('Victim(s)', 'ಬಲಿಪಶು(ಗಳು)')}</h3>
            <button type="button" className="btn btn-secondary btn-sm" onClick={addVictim}><Plus size={16} /> {t('Add Victim', 'ಬಲಿಪಶು ಸೇರಿಸಿ')}</button>
          </div>
          {form.victims.length === 0 && <p className="text-muted text-sm">{t('No victims added.', 'ಯಾವುದೇ ಬಲಿಪಶುಗಳನ್ನು ಸೇರಿಸಲಾಗಿಲ್ಲ.')}</p>}
          {form.victims.map((v, i) => (
            <div key={i} style={{ position: 'relative', padding: 16, marginBottom: 12, border: '1px solid var(--border)', borderRadius: 8 }}>
              <button type="button" className="btn btn-ghost btn-icon" style={{ position: 'absolute', top: 8, right: 8, color: 'var(--danger)' }} onClick={() => removeVictim(i)}><Trash2 size={16} /></button>
              <div className="grid-3">
                <div className="form-group">
                  <label>{t('Name', 'ಹೆಸರು')}</label>
                  <input className="input" value={v.name} onChange={e => updVictim(i, 'name', e.target.value)} />
                </div>
                <div className="form-group">
                  <label>{t('Age', 'ವಯಸ್ಸು')}</label>
                  <input className="input" type="number" value={v.age} onChange={e => updVictim(i, 'age', e.target.value)} />
                </div>
                <div className="form-group">
                  <label>{t('Gender', 'ಲಿಂಗ')}</label>
                  <select className="input" value={v.gender} onChange={e => updVictim(i, 'gender', e.target.value)}>
                    <option value="m">{t('Male', 'ಪುರುಷ')}</option>
                    <option value="f">{t('Female', 'ಮಹಿಳೆ')}</option>
                    <option value="t">{t('Transgender', 'ತೃತೀಯ ಲಿಂಗಿ')}</option>
                  </select>
                </div>
              </div>
              <label className="flex items-center gap-2" style={{ cursor: 'pointer', fontSize: 13, marginTop: 8 }}>
                <input type="checkbox" checked={v.isPolice} onChange={e => updVictim(i, 'isPolice', e.target.checked)} />
                {t('Victim is Police Officer', 'ಬಲಿಪಶು ಪೊಲೀಸ್ ಅಧಿಕಾರಿ')}
              </label>
            </div>
          ))}
          <div className="flex gap-4" style={{ justifyContent: 'space-between', marginTop: 16 }}>
            <button type="button" className="btn btn-secondary" onClick={() => setStep(2)}>{t('Back', 'ಹಿಂದೆ')}</button>
            <button type="button" className="btn btn-primary" onClick={() => setStep(4)}>{t('Next: Accused', 'ಮುಂದೆ: ಆರೋಪಿಗಳು')}</button>
          </div>
        </div>
      )}

      {step === 4 && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-header flex justify-between items-center">
            <h3>{t('Accused(s)', 'ಆರೋಪಿ(ಗಳು)')}</h3>
            <button type="button" className="btn btn-secondary btn-sm" onClick={addAccused}><Plus size={16} /> {t('Add Accused', 'ಆರೋಪಿ ಸೇರಿಸಿ')}</button>
          </div>
          {form.accuseds.length === 0 && <p className="text-muted text-sm">{t('No accused added.', 'ಯಾವುದೇ ಆರೋಪಿಗಳನ್ನು ಸೇರಿಸಲಾಗಿಲ್ಲ.')}</p>}
          {form.accuseds.map((a, i) => (
            <div key={i} style={{ position: 'relative', padding: 16, marginBottom: 12, border: '1px solid var(--border)', borderRadius: 8 }}>
              <button type="button" className="btn btn-ghost btn-icon" style={{ position: 'absolute', top: 8, right: 8, color: 'var(--danger)' }} onClick={() => removeAccused(i)}><Trash2 size={16} /></button>
              <div className="grid-3">
                <div className="form-group">
                  <label>{t('Sorting ID', 'ವಿಂಗಡಣೆ ಐಡಿ')}</label>
                  <input className="input" value={a.sorting_id} disabled />
                </div>
                <div className="form-group">
                  <label>{t('Name', 'ಹೆಸರು')}</label>
                  <input className="input" value={a.name} onChange={e => updAccused(i, 'name', e.target.value)} />
                </div>
                <div className="form-group">
                  <label>{t('Age', 'ವಯಸ್ಸು')}</label>
                  <input className="input" type="number" value={a.age} onChange={e => updAccused(i, 'age', e.target.value)} />
                </div>
              </div>
              <div className="form-group" style={{ marginTop: 8 }}>
                <label>{t('Gender', 'ಲಿಂಗ')}</label>
                <select className="input" value={a.gender} onChange={e => updAccused(i, 'gender', e.target.value)}>
                  <option value="m">{t('Male', 'ಪುರುಷ')}</option>
                  <option value="f">{t('Female', 'ಮಹಿಳೆ')}</option>
                  <option value="t">{t('Transgender', 'ತೃತೀಯ ಲಿಂಗಿ')}</option>
                </select>
              </div>
            </div>
          ))}
          <div className="flex gap-4" style={{ justifyContent: 'space-between', marginTop: 16 }}>
            <button type="button" className="btn btn-secondary" onClick={() => setStep(3)}>{t('Back', 'ಹಿಂದೆ')}</button>
            <button type="button" className="btn btn-primary" onClick={() => setStep(5)}>{t('Next: Legal Classification', 'ಮುಂದೆ: ಕಾನೂನು ವರ್ಗೀಕರಣ')}</button>
          </div>
        </div>
      )}

      {step === 5 && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-header"><h3>{t('Legal Classification', 'ಕಾನೂನು ವರ್ಗೀಕರಣ')}</h3></div>
          <div className="grid-3">
            <div className="form-group">
              <label>{t('Crime Category', 'ಅಪರಾಧ ವರ್ಗ')} *</label>
              <select className="input" value={form.crime_category} onChange={e => setForm(f => ({ ...f, crime_category: e.target.value }))} required>
                <option value="">-- {t('Select', 'ಆಯ್ಕೆಮಾಡಿ')} --</option>
                {crimeCategories.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>{t('Gravity Offence', 'ಗುರುತ್ವ ಅಪರಾಧ')} *</label>
              <select className="input" value={form.gravity_offence} onChange={e => setForm(f => ({ ...f, gravity_offence: e.target.value }))} required>
                <option value="">-- {t('Select', 'ಆಯ್ಕೆಮಾಡಿ')} --</option>
                {gravityOffences.map(g => <option key={g} value={g}>{g}</option>)}
              </select>
            </div>
            <div className="form-group">
              <label>{t('Crime Major Head', 'ಪ್ರಮುಖ ಅಪರಾಧ ಶೀರ್ಷಿಕೆ')}</label>
              <select className="input" value={form.crime_major_head} onChange={e => setForm(f => ({ ...f, crime_major_head: e.target.value, crime_minor_head: '' }))}>
                <option value="">-- {t('Select', 'ಆಯ್ಕೆಮಾಡಿ')} --</option>
                {majorHeads.map(h => <option key={h} value={h}>{h}</option>)}
              </select>
            </div>
          </div>
          <div className="form-group">
            <label>{t('Crime Minor Head', 'ಉಪ ಅಪರಾಧ ಶೀರ್ಷಿಕೆ')}</label>
            <select className="input" value={form.crime_minor_head} onChange={e => setForm(f => ({ ...f, crime_minor_head: e.target.value }))} disabled={!form.crime_major_head}>
              <option value="">-- {t('Select', 'ಆಯ್ಕೆಮಾಡಿ')} --</option>
              {form.crime_major_head && minorHeads[form.crime_major_head]?.map(h => <option key={h} value={h}>{h}</option>)}
            </select>
          </div>
          <div style={{ marginTop: 24 }}>
            <div className="card-header flex justify-between items-center">
              <h4>{t('Acts & Sections', 'ಕಾಯಿದೆಗಳು ಮತ್ತು ಸೆಕ್ಷನ್‌ಗಳು')}</h4>
              <button type="button" className="btn btn-secondary btn-sm" onClick={addActSection}><Plus size={16} /> {t('Add Section', 'ಸೆಕ್ಷನ್ ಸೇರಿಸಿ')}</button>
            </div>
            {form.acts_sections.length === 0 && <p className="text-muted text-sm">{t('No sections added.', 'ಯಾವುದೇ ಸೆಕ್ಷನ್‌ಗಳನ್ನು ಸೇರಿಸಲಾಗಿಲ್ಲ.')}</p>}
            {form.acts_sections.map((as, i) => (
              <div key={i} style={{ position: 'relative', padding: 16, marginBottom: 12, border: '1px solid var(--border)', borderRadius: 8 }}>
                <button type="button" className="btn btn-ghost btn-icon" style={{ position: 'absolute', top: 8, right: 8, color: 'var(--danger)' }} onClick={() => removeActSection(i)}><Trash2 size={16} /></button>
                <div className="grid-2">
                  <div className="form-group">
                    <label>{t('Act', 'ಕಾಯಿದೆ')}</label>
                    <select className="input" value={as.act} onChange={e => updActSection(i, 'act', e.target.value)}>
                      <option value="">-- {t('Select', 'ಆಯ್ಕೆಮಾಡಿ')} --</option>
                      {acts.map(a => <option key={a} value={a}>{a}</option>)}
                    </select>
                  </div>
                  <div className="form-group">
                    <label>{t('Section', 'ಸೆಕ್ಷನ್')}</label>
                    <select className="input" value={as.section} onChange={e => updActSection(i, 'section', e.target.value)} disabled={!as.act}>
                      <option value="">-- {t('Select', 'ಆಯ್ಕೆಮಾಡಿ')} --</option>
                      {as.act && sections[as.act]?.map(s => <option key={s} value={s}>{s}</option>)}
                    </select>
                  </div>
                </div>
                {definitions[as.section] && (
                  <p className="text-xs" style={{ color: 'var(--text-muted)', marginTop: 4 }}>{definitions[as.section]}</p>
                )}
              </div>
            ))}
          </div>
          <div className="flex gap-4" style={{ justifyContent: 'space-between', marginTop: 16 }}>
            <button type="button" className="btn btn-secondary" onClick={() => setStep(4)}>{t('Back', 'ಹಿಂದೆ')}</button>
            <button type="button" className="btn btn-primary" onClick={() => setStep(6)}>{t('Next: Submit', 'ಮುಂದೆ: ಸಲ್ಲಿಸಿ')}</button>
          </div>
        </div>
      )}

      {step === 6 && (
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-header"><h3>{t('Approval & Submit', 'ಅನುಮೋದನೆ ಮತ್ತು ಸಲ್ಲಿಕೆ')}</h3></div>
          <div className="grid-2">
            <div className="form-group">
              <label>{t('Registered By', 'ನೋಂದಾಯಿಸಿದವರು')}</label>
              <input className="input" value={`${user?.first_name} (${user?.role_name})`} disabled />
            </div>
            <div className="form-group">
              <label>{t('Police Station (Unit ID)', 'ಪೊಲೀಸ್ ಠಾಣೆ')}</label>
              <input className="input" value={String(user?.unit_id || 1)} disabled />
            </div>
          </div>
          <div className="form-group">
            <label>{t('Date of Registration', 'ನೋಂದಣಿ ದಿನಾಂಕ')}</label>
            <input className="input" value={new Date().toLocaleDateString('en-IN', { year: 'numeric', month: 'long', day: 'numeric' })} disabled />
          </div>
          <div className="form-group">
            <label>{t('Crime No (auto-generated)', 'ಅಪರಾಧ ಸಂಖ್ಯೆ (ಸ್ವಯಂ-ರಚಿತ)')}</label>
            <input className="input" value={crimeNo} disabled style={{ fontFamily: 'monospace' }} />
          </div>
          <div className="flex gap-4" style={{ justifyContent: 'space-between', marginTop: 24 }}>
            <button type="button" className="btn btn-secondary" onClick={() => setStep(5)}>{t('Back', 'ಹಿಂದೆ')}</button>
            <button type="submit" className="btn btn-primary"><Send size={16} /> {t('Submit & Generate FIR', 'ಸಲ್ಲಿಸಿ ಮತ್ತು ಎಫ್ಐಆರ್ ರಚಿಸಿ')}</button>
          </div>
        </div>
      )}
    </form>
  );

  return (
    <div style={{ display: 'flex', gap: 24 }}>
      <div style={{ flex: 1 }}>
        <div className="page-header">
          <h1>{t('Case Registration', 'ಪ್ರಕರಣ ನೋಂದಣಿ')}</h1>
          <p>{t('Register a new First Information Report', 'ಹೊಸ ಪ್ರಥಮ ಮಾಹಿತಿ ವರದಿಯನ್ನು ನೋಂದಾಯಿಸಿ')}</p>
        </div>

        <div className="tabs" style={{ marginBottom: 24 }}>
          {[1, 2, 3, 4, 5, 6].map(s => (
            <button key={s} className={`tab ${step === s ? 'active' : ''}`} onClick={() => setStep(s)}>
              {s === 1 ? t('Incident', 'ಘಟನೆ') : s === 2 ? t('Complainant', 'ದೂರುದಾರ') : s === 3 ? t('Victims', 'ಬಲಿಪಶುಗಳು') : s === 4 ? t('Accused', 'ಆರೋಪಿಗಳು') : s === 5 ? t('Legal', 'ಕಾನೂನು') : t('Submit', 'ಸಲ್ಲಿಸಿ')}
            </button>
          ))}
        </div>

        {formContent}
      </div>

      <div style={{ width: 320, flexShrink: 0 }}>
        <div className="card" style={{ position: 'sticky', top: 32 }}>
          <div className="card-header flex justify-between items-center">
            <span className="flex items-center gap-2"><Bot size={20} /> {t('CaseBot', 'ಕೇಸ್‌ಬಾಟ್')}</span>
            <button className="btn btn-ghost btn-icon" onClick={() => setShowCaseBot(!showCaseBot)}>
              {showCaseBot ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
            </button>
          </div>
          {showCaseBot && (
            <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
              <div style={{ marginBottom: 16, padding: 12, background: 'var(--bg-hover)', borderRadius: 8, fontSize: 13, minHeight: 40 }}>
                {caseBotMsg}
                {botConfidence && botConfidence.missing.length > 0 && (
                  <div style={{ marginTop: 8 }}>
                    <span className="badge badge-elevated" style={{ fontSize: 11 }}>
                      <AlertTriangle size={12} /> {t('Missing fields', 'ಕಾಣೆಯಾದ ಕ್ಷೇತ್ರಗಳು')}: {botConfidence.missing.length}
                    </span>
                  </div>
                )}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <button className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }} onClick={checkConfidence}>
                  <AlertTriangle size={14} /> {t('Confidence Checker', 'ವಿಶ್ವಾಸ ಪರಿಶೀಲಕ')}
                </button>
                <button className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }} onClick={autoFillSimilar}>
                  {t('Auto-fill similar case', 'ಹೋಲುವ ಪ್ರಕರಣ ಸ್ವಯಂ-ಭರ್ತಿ')}
                </button>
                <button className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }} onClick={() => {
                  const secs = form.acts_sections.map(as => as.section || as.act).filter(Boolean);
                  setCaseBotMsg(secs.length ? t('Review sections:', 'ಸೆಕ್ಷನ್‌ಗಳನ್ನು ಪರಿಶೀಲಿಸಿ:') + ' ' + secs.join(', ') : t('No sections selected yet.', 'ಇನ್ನೂ ಯಾವುದೇ ಸೆಕ್ಷನ್‌ಗಳನ್ನು ಆಯ್ಕೆ ಮಾಡಲಾಗಿಲ್ಲ.'));
                }}>
                  {t('Review sections', 'ಸೆಕ್ಷನ್‌ಗಳನ್ನು ಪರಿಶೀಲಿಸಿ')}
                </button>
                <button className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }} onClick={() => setCaseBotMsg(t('FAQ: How to file FIR in Kannada? Toggle language to ಕನ್ನಡ in top-right. All field labels will be in Kannada.', 'FAQ: ಕನ್ನಡದಲ್ಲಿ ಎಫ್ಐಆರ್ ದಾಖಲಿಸುವುದು ಹೇಗೆ? ಮೇಲಿನ ಬಲಭಾಗದಲ್ಲಿ ಭಾಷೆಯನ್ನು ಕನ್ನಡಕ್ಕೆ ಟಾಗಲ್ ಮಾಡಿ. ಎಲ್ಲಾ ಕ್ಷೇತ್ರ ಲೇಬಲ್‌ಗಳು ಕನ್ನಡದಲ್ಲಿರುತ್ತವೆ.'))}>
                  <HelpCircle size={14} /> {t('Help', 'ಸಹಾಯ')}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
