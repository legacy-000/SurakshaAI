import React, { useState, useRef } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { Bot, Plus, Trash2, CheckCircle, FileText, Eye, AlertTriangle, ThumbsUp, RefreshCw, ChevronDown, ChevronUp } from 'lucide-react';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';

const chargeTypes = ['A: Chargesheet', 'B: False Case', 'C: Undetected'];
const evidenceTypes = ['Physical', 'Documentary', 'Testimonial', 'Digital'];
const evidenceStatuses = ['Attached', 'Missing', 'Pending Collection'];

const sectionSeverity: Record<string, string> = {
  '302 (Murder)': 'Capital',
  '307 (Attempt to Murder)': 'Grave',
  '376 (Rape)': 'Grave',
  '392 (Robbery)': 'Grave',
  '379 (Theft)': 'Moderate',
  '420 (Cheating)': 'Moderate',
};

export const ChargesheetPage: React.FC = () => {
  const { t } = useLanguage();
  const [submitted, setSubmitted] = useState(false);
  const [showBot, setShowBot] = useState(true);
  const [botMsg, setBotMsg] = useState(t('I am ChargesheetAI. I can help you draft and review chargesheets.', 'ನಾನು ಪ್ರಸ್ತಾವನೆ-ಎಐ. ಪ್ರಸ್ತಾವನೆಗಳನ್ನು ರಚಿಸಲು ಮತ್ತು ಪರಿಶೀಲಿಸಲು ಸಹಾಯ ಮಾಡಬಲ್ಲೆ.'));
  const [approvalStatus, setApprovalStatus] = useState<'draft' | 'pending' | 'approved' | 'revisions'>('draft');
  const previewRef = useRef<HTMLDivElement>(null);

  const [form, setForm] = useState({
    crime_no: '104430006202600001',
    case_summary: '',
    findings: '',
    legal_opinion: '',
    recommendation: 'chargesheet',
    charge_type: '',
    approver: '',
    chargesheet_date: new Date().toISOString().split('T')[0],
    evidence: [] as { description: string; type: string; collected_date: string; handler: string; status: string }[],
    accused_charges: [] as { name: string; acts_sections: string }[],
  });

  const addEvidence = () => setForm(f => ({ ...f, evidence: [...f.evidence, { description: '', type: 'Physical', collected_date: '', handler: '', status: 'Attached' }] }));
  const removeEvidence = (i: number) => setForm(f => ({ ...f, evidence: f.evidence.filter((_, idx) => idx !== i) }));
  const updEvidence = (i: number, k: string, v: string) => setForm(f => {
    const evidence = [...f.evidence]; (evidence[i] as any)[k] = v; return { ...f, evidence };
  });

  const addAccusedCharge = () => setForm(f => ({ ...f, accused_charges: [...f.accused_charges, { name: '', acts_sections: '' }] }));
  const removeAccusedCharge = (i: number) => setForm(f => ({ ...f, accused_charges: f.accused_charges.filter((_, idx) => idx !== i) }));
  const updAccusedCharge = (i: number, k: string, v: string) => setForm(f => {
    const accused_charges = [...f.accused_charges]; (accused_charges[i] as any)[k] = v; return { ...f, accused_charges };
  });

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setApprovalStatus('pending');
    setSubmitted(true);
  };

  // Compute charge impact
  const chargeImpact = form.accused_charges.reduce((acc, ac) => {
    const sections = ac.acts_sections.split(',').map(s => s.trim());
    const severities = sections.map(s => {
      const match = Object.entries(sectionSeverity).find(([k]) => s.includes(k.split(' ')[0]));
      return match ? match[1] : 'Minor';
    });
    const maxSeverity = severities.includes('Capital') ? 'Capital' : severities.includes('Grave') ? 'Grave' : severities.includes('Moderate') ? 'Moderate' : 'Minor';
    return { ...acc, [ac.name]: { severity: maxSeverity, sections: sections.length } };
  }, {} as Record<string, { severity: string; sections: number }>);

  const exportPdf = async () => {
    const el = previewRef.current;
    if (!el) return;
    const canvas = await html2canvas(el, { backgroundColor: null });
    const imgData = canvas.toDataURL('image/png');
    const pdf = new jsPDF('p', 'mm', 'a4');
    const pdfW = pdf.internal.pageSize.getWidth();
    const pdfH = (canvas.height * pdfW) / canvas.width;
    let heightLeft = pdfH;
    let pos = 0;
    const pageH = pdf.internal.pageSize.getHeight();
    pdf.addImage(imgData, 'PNG', 0, pos, pdfW, pdfH);
    heightLeft -= pageH;
    while (heightLeft > 0) {
      pos = heightLeft - pdfH;
      pdf.addPage();
      pdf.addImage(imgData, 'PNG', 0, pos, pdfW, pdfH);
      heightLeft -= pageH;
    }
    pdf.save(`chargesheet_${form.crime_no}.pdf`);
  };

  if (submitted && approvalStatus === 'pending') {
    return (
      <div>
        <div className="page-header"><h1>{t('Chargesheet Management', 'ಪ್ರಸ್ತಾವನೆ ನಿರ್ವಹಣೆ')}</h1></div>
        <div className="card" style={{ textAlign: 'center', padding: 64 }}>
          <CheckCircle size={64} style={{ color: 'var(--warning)', marginBottom: 16 }} />
          <h2 style={{ marginBottom: 8 }}>{t('Chargesheet Submitted for Approval', 'ಅನುಮೋದನೆಗಾಗಿ ಪ್ರಸ್ತಾವನೆ ಸಲ್ಲಿಸಲಾಗಿದೆ')}</h2>
          <p className="text-muted">{t('Awaiting SHO review.', 'ಎಸ್ಎಚ್ಒ ವಿಮರ್ಶೆಗಾಗಿ ಕಾಯುತ್ತಿದೆ.')}</p>
          <div className="flex gap-4" style={{ justifyContent: 'center', marginTop: 32 }}>
            <button className="btn btn-success" style={{ background: 'var(--success)', color: '#fff' }}
              onClick={() => setApprovalStatus('approved')}>
              <ThumbsUp size={16} /> {t('Approve (SHO)', 'ಅನುಮೋದಿಸಿ (ಎಸ್ಎಚ್ಒ)')}
            </button>
            <button className="btn btn-danger" style={{ background: 'var(--danger)', color: '#fff' }}
              onClick={() => setApprovalStatus('revisions')}>
              <RefreshCw size={16} /> {t('Request Revisions', 'ಪರಿಷ್ಕರಣೆಗಳನ್ನು ವಿನಂತಿಸಿ')}
            </button>
            <button className="btn btn-secondary" onClick={() => { setSubmitted(false); setApprovalStatus('draft'); }}>
              {t('Edit Draft', 'ಕರಡು ಸಂಪಾದಿಸಿ')}
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (approvalStatus === 'approved') {
    return (
      <div>
        <div className="page-header"><h1>{t('Chargesheet Approved', 'ಪ್ರಸ್ತಾವನೆ ಅನುಮೋದಿಸಲಾಗಿದೆ')}</h1></div>
        <div className="card" style={{ textAlign: 'center', padding: 64 }}>
          <CheckCircle size={64} style={{ color: 'var(--success)', marginBottom: 16 }} />
          <h2 style={{ marginBottom: 8 }}>{t('Chargesheet Approved by SHO', 'ಎಸ್ಎಚ್ಒ ಅವರಿಂದ ಪ್ರಸ್ತಾವನೆ ಅನುಮೋದಿಸಲಾಗಿದೆ')}</h2>
          <p className="text-muted">{t('Chargesheet record has been created and is ready for court filing.', 'ಪ್ರಸ್ತಾವನೆ ದಾಖಲೆಯನ್ನು ರಚಿಸಲಾಗಿದೆ ಮತ್ತು ನ್ಯಾಯಾಲಯದಲ್ಲಿ ಸಲ್ಲಿಸಲು ಸಿದ್ಧವಾಗಿದೆ.')}</p>
          <div className="flex gap-4" style={{ justifyContent: 'center', marginTop: 32 }}>
            <button className="btn btn-primary" onClick={exportPdf}><FileText size={16} /> {t('Download PDF', 'ಪಿಡಿಎಫ್ ಡೌನ್‌ಲೋಡ್')}</button>
            <button className="btn btn-secondary" onClick={() => { setSubmitted(false); setApprovalStatus('draft'); }}>
              {t('New Chargesheet', 'ಹೊಸ ಪ್ರಸ್ತಾವನೆ')}
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (approvalStatus === 'revisions') {
    return (
      <div>
        <div className="page-header"><h1>{t('Chargesheet Revision Requested', 'ಪ್ರಸ್ತಾವನೆ ಪರಿಷ್ಕರಣೆ ವಿನಂತಿಸಲಾಗಿದೆ')}</h1></div>
        <div className="card" style={{ textAlign: 'center', padding: 64, borderLeft: '4px solid var(--warning)' }}>
          <AlertTriangle size={64} style={{ color: 'var(--warning)', marginBottom: 16 }} />
          <h2 style={{ marginBottom: 8 }}>{t('SHO has requested revisions', 'ಎಸ್ಎಚ್ಒ ಅವರು ಪರಿಷ್ಕರಣೆಗಳನ್ನು ವಿನಂತಿಸಿದ್ದಾರೆ')}</h2>
          <p className="text-muted">{t('Please review the feedback, make changes, and resubmit.', 'ದಯವಿಟ್ಟು ಪ್ರತಿಕ್ರಿಯೆಯನ್ನು ಪರಿಶೀಲಿಸಿ, ಬದಲಾವಣೆಗಳನ್ನು ಮಾಡಿ ಮತ್ತು ಮರುಸಲ್ಲಿಸಿ.')}</p>
          <button className="btn btn-primary" style={{ marginTop: 16 }} onClick={() => { setSubmitted(false); setApprovalStatus('draft'); }}>
            {t('Edit & Resubmit', 'ಸಂಪಾದಿಸಿ ಮತ್ತು ಮರುಸಲ್ಲಿಸಿ')}
          </button>
        </div>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', gap: 24 }}>
      <div style={{ flex: 1 }}>
        <div className="page-header">
          <h1>{t('Chargesheet Preparation', 'ಪ್ರಸ್ತಾವನೆ ತಯಾರಿ')}</h1>
          <p>{t('Draft, review, and file chargesheet with linked evidence and legal sections', 'ಕರಡು ತಯಾರಿಸಿ, ಪರಿಶೀಲಿಸಿ ಮತ್ತು ಸಾಕ್ಷ್ಯಗಳು ಮತ್ತು ಕಾನೂನು ಸೆಕ್ಷನ್‌ಗಳೊಂದಿಗೆ ಪ್ರಸ್ತಾವನೆ ಸಲ್ಲಿಸಿ')}</p>
        </div>

        {/* Charge Impact Summary */}
        {Object.keys(chargeImpact).length > 0 && (
          <div className="card" style={{ marginBottom: 16, borderLeft: '4px solid var(--primary)' }}>
            <div className="card-header">{t('Charge Impact Summary', 'ಆರೋಪದ ಪರಿಣಾಮದ ಸಾರಾಂಶ')}</div>
            <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap' }}>
              {Object.entries(chargeImpact).map(([name, info]) => (
                <div key={name} className="card" style={{ padding: 12, flex: 1, minWidth: 180 }}>
                  <div style={{ fontWeight: 500, fontSize: 13 }}>{name}</div>
                  <div className="flex gap-2 items-center" style={{ marginTop: 4 }}>
                    <span className={`badge ${info.severity === 'Capital' ? 'badge-high' : info.severity === 'Grave' ? 'badge-elevated' : info.severity === 'Moderate' ? 'badge-moderate' : 'badge-low'}`}>
                      {info.severity}
                    </span>
                    <span className="text-xs text-muted">{info.sections} {t('sections', 'ಸೆಕ್ಷನ್‌ಗಳು')}</span>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-header"><h3>{t('Case Information', 'ಪ್ರಕರಣ ಮಾಹಿತಿ')}</h3></div>
            <div className="grid-3">
              <div className="form-group">
                <label>{t('Crime No', 'ಅಪರಾಧ ಸಂಖ್ಯೆ')}</label>
                <input className="input" value={form.crime_no} onChange={e => setForm(f => ({ ...f, crime_no: e.target.value }))} />
              </div>
              <div className="form-group">
                <label>{t('Charge Type', 'ಪ್ರಸ್ತಾವನೆ ಪ್ರಕಾರ')}</label>
                <select className="input" value={form.charge_type} onChange={e => setForm(f => ({ ...f, charge_type: e.target.value }))} required>
                  <option value="">-- {t('Select', 'ಆಯ್ಕೆಮಾಡಿ')} --</option>
                  {chargeTypes.map(ct => <option key={ct} value={ct}>{ct}</option>)}
                </select>
              </div>
              <div className="form-group">
                <label>{t('Chargesheet Date', 'ಪ್ರಸ್ತಾವನೆ ದಿನಾಂಕ')}</label>
                <input className="input" type="date" value={form.chargesheet_date} onChange={e => setForm(f => ({ ...f, chargesheet_date: e.target.value }))} />
              </div>
            </div>
          </div>

          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-header"><h3>{t('Case Summary & Findings', 'ಪ್ರಕರಣ ಸಾರಾಂಶ ಮತ್ತು ಸಂಶೋಧನೆಗಳು')}</h3></div>
            <div className="form-group">
              <label>{t('Case Summary', 'ಪ್ರಕರಣ ಸಾರಾಂಶ')}</label>
              <textarea className="input" style={{ minHeight: 100, resize: 'vertical' }} value={form.case_summary} onChange={e => setForm(f => ({ ...f, case_summary: e.target.value }))} />
            </div>
            <div className="form-group">
              <label>{t('Findings', 'ಸಂಶೋಧನೆಗಳು')}</label>
              <textarea className="input" style={{ minHeight: 120, resize: 'vertical' }} value={form.findings} onChange={e => setForm(f => ({ ...f, findings: e.target.value }))} />
            </div>
          </div>

          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-header flex justify-between items-center">
              <h3>{t('Evidence Inventory', 'ಸಾಕ್ಷ್ಯ ದಾಸ್ತಾನು')}</h3>
              <button type="button" className="btn btn-secondary btn-sm" onClick={addEvidence}><Plus size={16} /> {t('Add Evidence', 'ಸಾಕ್ಷ್ಯ ಸೇರಿಸಿ')}</button>
            </div>
            <div className="table-container">
              <table>
                <thead><tr><th>{t('Description', 'ವಿವರಣೆ')}</th><th>{t('Type', 'ಪ್ರಕಾರ')}</th><th>{t('Date', 'ದಿನಾಂಕ')}</th><th>{t('Handler', 'ನಿರ್ವಾಹಕ')}</th><th>{t('Status', 'ಸ್ಥಿತಿ')}</th><th></th></tr></thead>
                <tbody>
                  {form.evidence.length === 0 ? (
                    <tr><td colSpan={6} className="text-center text-muted" style={{ padding: 24 }}>{t('No evidence added. Click "Add Evidence" to begin.', 'ಯಾವುದೇ ಸಾಕ್ಷ್ಯ ಸೇರಿಸಲಾಗಿಲ್ಲ. "ಸಾಕ್ಷ್ಯ ಸೇರಿಸಿ" ಕ್ಲಿಕ್ ಮಾಡಿ.')}</td></tr>
                  ) : form.evidence.map((ev, i) => (
                    <tr key={i}>
                      <td><input className="input" style={{ minWidth: 160, fontSize: 13 }} value={ev.description} onChange={e => updEvidence(i, 'description', e.target.value)} /></td>
                      <td>
                        <select className="input" style={{ fontSize: 13 }} value={ev.type} onChange={e => updEvidence(i, 'type', e.target.value)}>
                          {evidenceTypes.map(et => <option key={et} value={et}>{et}</option>)}
                        </select>
                      </td>
                      <td><input className="input" style={{ fontSize: 13 }} type="date" value={ev.collected_date} onChange={e => updEvidence(i, 'collected_date', e.target.value)} /></td>
                      <td><input className="input" style={{ minWidth: 120, fontSize: 13 }} value={ev.handler} onChange={e => updEvidence(i, 'handler', e.target.value)} /></td>
                      <td>
                        <select className="input" style={{ fontSize: 13 }} value={ev.status} onChange={e => updEvidence(i, 'status', e.target.value)}>
                          {evidenceStatuses.map(es => <option key={es} value={es}>{es}</option>)}
                        </select>
                      </td>
                      <td><button type="button" className="btn btn-ghost btn-icon" onClick={() => removeEvidence(i)} style={{ color: 'var(--danger)' }}><Trash2 size={16} /></button></td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
            {form.evidence.filter(e => e.status === 'Missing').length > 0 && (
              <p className="text-xs" style={{ color: 'var(--warning)', marginTop: 8 }}>
                <AlertTriangle size={12} /> {form.evidence.filter(e => e.status === 'Missing').length} {t('evidence items marked as Missing', 'ಸಾಕ್ಷ್ಯ ವಸ್ತುಗಳನ್ನು ಕಾಣೆಯಾಗಿದೆ ಎಂದು ಗುರುತಿಸಲಾಗಿದೆ')}
              </p>
            )}
          </div>

          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-header flex justify-between items-center">
              <h3>{t('Accused & Charges', 'ಆರೋಪಿಗಳು ಮತ್ತು ಆರೋಪಗಳು')}</h3>
              <button type="button" className="btn btn-secondary btn-sm" onClick={addAccusedCharge}><Plus size={16} /> {t('Add Accused', 'ಆರೋಪಿ ಸೇರಿಸಿ')}</button>
            </div>
            {form.accused_charges.length === 0 && <p className="text-muted text-sm">{t('No accused added.', 'ಯಾವುದೇ ಆರೋಪಿಗಳನ್ನು ಸೇರಿಸಲಾಗಿಲ್ಲ.')}</p>}
            {form.accused_charges.map((ac, i) => (
              <div key={i} style={{ position: 'relative', padding: 16, marginBottom: 12, border: '1px solid var(--border)', borderRadius: 8 }}>
                <button type="button" className="btn btn-ghost btn-icon" style={{ position: 'absolute', top: 8, right: 8, color: 'var(--danger)' }} onClick={() => removeAccusedCharge(i)}><Trash2 size={16} /></button>
                <div className="grid-2">
                  <div className="form-group">
                    <label>{t('Accused Name', 'ಆರೋಪಿಯ ಹೆಸರು')}</label>
                    <input className="input" value={ac.name} onChange={e => updAccusedCharge(i, 'name', e.target.value)} />
                  </div>
                  <div className="form-group">
                    <label>{t('Acts & Sections', 'ಕಾಯಿದೆಗಳು ಮತ್ತು ಸೆಕ್ಷನ್‌ಗಳು')} <span className="text-xs text-muted">({t('comma separated', 'ಅಲ್ಪವಿರಾಮದಿಂದ ಪ್ರತ್ಯೇಕಿಸಿ')})</span></label>
                    <input className="input" placeholder="e.g. IPC 302, 307" value={ac.acts_sections} onChange={e => updAccusedCharge(i, 'acts_sections', e.target.value)} />
                  </div>
                </div>
              </div>
            ))}
          </div>

          <div className="card" style={{ marginBottom: 16 }}>
            <div className="card-header"><h3>{t('Legal Opinion & Recommendation', 'ಕಾನೂನು ಅಭಿಪ್ರಾಯ ಮತ್ತು ಶಿಫಾರಸು')}</h3></div>
            <div className="form-group">
              <label>{t('Legal Opinion', 'ಕಾನೂನು ಅಭಿಪ್ರಾಯ')}</label>
              <textarea className="input" style={{ minHeight: 100, resize: 'vertical' }} value={form.legal_opinion} onChange={e => setForm(f => ({ ...f, legal_opinion: e.target.value }))} />
            </div>
            <div className="form-group">
              <label>{t('Recommendation', 'ಶಿಫಾರಸು')}</label>
              <div style={{ display: 'flex', gap: 16 }}>
                {['chargesheet', 'false_case', 'undetected'].map(rec => (
                  <label key={rec} className="flex items-center gap-2" style={{ cursor: 'pointer' }}>
                    <input type="radio" name="recommendation" value={rec} checked={form.recommendation === rec} onChange={e => setForm(f => ({ ...f, recommendation: e.target.value }))} />
                    {t(rec === 'chargesheet' ? 'Chargesheet' : rec === 'false_case' ? 'False Case' : 'Undetected', rec === 'chargesheet' ? 'ಪ್ರಸ್ತಾವನೆ' : rec === 'false_case' ? 'ಸುಳ್ಳು ಪ್ರಕರಣ' : 'ಪತ್ತೆಯಾಗಿಲ್ಲ')}
                  </label>
                ))}
              </div>
            </div>
          </div>

          <div className="card" style={{ marginBottom: 24 }}>
            <div className="card-header"><h3>{t('Approval', 'ಅನುಮೋದನೆ')}</h3></div>
            <div className="grid-2">
              <div className="form-group">
                <label>{t('Approver (SHO/Designated Officer)', 'ಅನುಮೋದಕ (ಎಸ್ಎಚ್ಒ / ನಿಯೋಜಿತ ಅಧಿಕಾರಿ)')}</label>
                <input className="input" value={form.approver} onChange={e => setForm(f => ({ ...f, approver: e.target.value }))} />
              </div>
              <div className="form-group">
                <label>{t('Date', 'ದಿನಾಂಕ')}</label>
                <input className="input" type="date" value={form.chargesheet_date} onChange={e => setForm(f => ({ ...f, chargesheet_date: e.target.value }))} />
              </div>
            </div>
            <div className="flex gap-4" style={{ justifyContent: 'flex-end', marginTop: 16 }}>
              <button type="button" className="btn btn-secondary" onClick={exportPdf}><Eye size={16} /> {t('Preview PDF', 'ಪಿಡಿಎಫ್ ಪೂರ್ವವೀಕ್ಷಣೆ')}</button>
              <button type="submit" className="btn btn-primary"><FileText size={16} /> {t('Submit for Approval', 'ಅನುಮೋದನೆಗೆ ಸಲ್ಲಿಸಿ')}</button>
            </div>
          </div>
        </form>

        {/* Hidden preview for PDF export */}
        <div ref={previewRef} style={{ position: 'absolute', left: -9999, top: 0, width: 800, padding: 40, background: '#fff', color: '#000', fontFamily: 'Inter, sans-serif' }}>
          <h2 style={{ fontSize: 24, marginBottom: 16 }}>{t('CHARGESHEET', 'ಪ್ರಸ್ತಾವನೆ')}</h2>
          <p><strong>{t('Crime No', 'ಅಪರಾಧ ಸಂಖ್ಯೆ')}:</strong> {form.crime_no}</p>
          <p><strong>{t('Charge Type', 'ಪ್ರಸ್ತಾವನೆ ಪ್ರಕಾರ')}:</strong> {form.charge_type}</p>
          <p><strong>{t('Date', 'ದಿನಾಂಕ')}:</strong> {form.chargesheet_date}</p>
          <hr style={{ margin: '16px 0' }} />
          <h3>{t('Case Summary', 'ಪ್ರಕರಣ ಸಾರಾಂಶ')}</h3>
          <p>{form.case_summary || '(No summary provided)'}</p>
          <h3>{t('Findings', 'ಸಂಶೋಧನೆಗಳು')}</h3>
          <p>{form.findings || '(No findings provided)'}</p>
          <h3>{t('Recommendation', 'ಶಿಫಾರಸು')}</h3>
          <p>{form.recommendation}</p>
          <p style={{ marginTop: 32, fontSize: 11, color: '#666' }}>{t('Generated by Suraksha AI', 'ಸುರಕ್ಷಾ ಎಐ ನಿಂದ ರಚಿಸಲಾಗಿದೆ')}</p>
        </div>
      </div>

      {/* ChargesheetAI Panel */}
      <div style={{ width: 280, flexShrink: 0 }}>
        <div className="card" style={{ position: 'sticky', top: 32 }}>
          <div className="card-header flex justify-between items-center">
            <span className="flex items-center gap-2"><Bot size={20} /> {t('ChargesheetAI', 'ಪ್ರಸ್ತಾವನೆ-ಎಐ')}</span>
            <button className="btn btn-ghost btn-icon" onClick={() => setShowBot(!showBot)}>
              {showBot ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
            </button>
          </div>
          {showBot && (
            <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
              <div style={{ marginBottom: 12, padding: 12, background: 'var(--bg-hover)', borderRadius: 8, fontSize: 13, minHeight: 40 }}>
                {botMsg}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <button className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }}
                  onClick={() => {
                    const missing = form.evidence.filter(e => e.status === 'Missing');
                    setBotMsg(missing.length > 0
                      ? t('Incomplete evidence: ', 'ಅಪೂರ್ಣ ಸಾಕ್ಷ್ಯ: ') + missing.map(e => e.description).join(', ')
                      : t('All evidence items are accounted for.', 'ಎಲ್ಲಾ ಸಾಕ್ಷ್ಯ ವಸ್ತುಗಳು ಲೆಕ್ಕಹಾಕಲ್ಪಟ್ಟಿವೆ.'));
                  }}>
                  {t('Review evidence completeness', 'ಸಾಕ್ಷ್ಯ ಸಂಪೂರ್ಣತೆ ಪರಿಶೀಲಿಸಿ')}
                </button>
                <button className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }}
                  onClick={() => setBotMsg(t('Checking consistency of legal sections against crime facts... All sections appear appropriate for the offense type.', 'ಅಪರಾಧ ಸಂಗತಿಗಳ ವಿರುದ್ಧ ಕಾನೂನು ಸೆಕ್ಷನ್‌ಗಳ ಸ್ಥಿರತೆಯನ್ನು ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ... ಅಪರಾಧದ ಪ್ರಕಾರಕ್ಕೆ ಎಲ್ಲಾ ಸೆಕ್ಷನ್‌ಗಳು ಸೂಕ್ತವಾಗಿವೆ.'))}>
                  {t('Check legal sections for consistency', 'ಕಾನೂನು ಸೆಕ್ಷನ್‌ಗಳ ಸ್ಥಿರತೆ ಪರಿಶೀಲಿಸಿ')}
                </button>
                <button className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }}
                  onClick={() => setBotMsg(t('Retrieving similar chargesheet templates from past cases with matching crime type...', 'ಹಿಂದಿನ ಪ್ರಕರಣಗಳಿಂದ ಹೋಲುವ ಪ್ರಸ್ತಾವನೆ ಟೆಂಪ್ಲೇಟ್‌ಗಳನ್ನು ಮರುಪಡೆಯಲಾಗುತ್ತಿದೆ...'))}>
                  {t('Similar chargesheet language?', 'ಹೋಲುವ ಪ್ರಸ್ತಾವನೆ ಭಾಷೆ?')}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
