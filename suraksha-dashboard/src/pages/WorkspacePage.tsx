import React, { useRef } from 'react';
import { Clock, Link, Lightbulb, Save, FileText } from 'lucide-react';
import html2canvas from 'html2canvas';
import jsPDF from 'jspdf';

const timeline = [
  { date: '2024-01-15', event: 'FIR registered at City Police Station', type: 'registration' },
  { date: '2024-01-18', event: 'Primary accused arrested', type: 'arrest' },
  { date: '2024-03-20', event: 'Chargesheet filed (Type A)', type: 'chargesheet' },
];

const similarCases = [
  { id: 102, crime: 'CN202400102', type: 'Theft', similarity: '0.89', district: 'Bangalore', status: 'Under Investigation' },
  { id: 204, crime: 'CN202400204', type: 'Robbery', similarity: '0.76', district: 'Mysuru', status: 'Charge Sheeted' },
];

export const WorkspacePage: React.FC = () => {
  const wsRef = useRef<HTMLDivElement>(null);

  const exportPdf = async () => {
    if (!wsRef.current) return;
    const canvas = await html2canvas(wsRef.current, { backgroundColor: null });
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
    pdf.save('suraksha-workspace-export.pdf');
  };

  return (
    <div ref={wsRef}>
      <div className="page-header flex justify-between items-center">
        <div>
          <h1>Investigation Workspace</h1>
          <p>Case analysis and decision support — Case #101</p>
        </div>
        <div className="flex gap-2">
          <button className="btn btn-secondary btn-sm"><Save size={16} /> Save</button>
          <button className="btn btn-primary btn-sm" onClick={exportPdf}><FileText size={16} /> Export PDF</button>
        </div>
      </div>

      <div className="grid-2">
        <div className="card">
          <div className="card-header flex items-center gap-2"><Clock size={16} /> Investigation Timeline</div>
          {timeline.map((t, i) => (
            <div key={i} style={{ display: 'flex', gap: 16, padding: '12px 0', borderBottom: '1px solid var(--border)' }}>
              <div style={{ width: 80, fontSize: 12, color: 'var(--text-muted)', flexShrink: 0 }}>{t.date}</div>
              <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>{t.event}</div>
            </div>
          ))}
        </div>

        <div className="card">
          <div className="card-header flex items-center gap-2"><Link size={16} /> Similar Cases</div>
          <div className="table-container">
            <table>
              <thead><tr><th>Crime No</th><th>Type</th><th>Similarity</th><th>Status</th></tr></thead>
              <tbody>
                {similarCases.map(c => (
                  <tr key={c.id}>
                    <td style={{ fontFamily: 'monospace', fontSize: 12 }}>{c.crime}</td>
                    <td>{c.type}</td>
                    <td><span className="badge badge-info">{c.similarity}</span></td>
                    <td><span className="badge badge-moderate">{c.status}</span></td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <div className="card mt-6">
        <div className="card-header flex items-center gap-2"><Lightbulb size={16} /> Investigative Leads</div>
        <div className="flex gap-4">
          <div className="card" style={{ flex: 1, borderLeft: '4px solid var(--primary)' }}>
            <div className="flex justify-between items-center">
              <div>
                <div style={{ fontWeight: 600, fontSize: 14 }}>Co-Accused Link</div>
                <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>Co-accused appears in 3 other cases</div>
              </div>
              <span className="badge badge-info">Confidence: 0.78</span>
            </div>
          </div>
          <div className="card" style={{ flex: 1, borderLeft: '4px solid var(--blue)' }}>
            <div className="flex justify-between items-center">
              <div>
                <div style={{ fontWeight: 600, fontSize: 14 }}>Location Pattern</div>
                <div style={{ fontSize: 13, color: 'var(--text-muted)', marginTop: 4 }}>Within 500m of 2 prior incidents</div>
              </div>
              <span className="badge badge-info">Confidence: 0.65</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};
