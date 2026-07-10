import React from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, MessageSquare, GitBranch, BarChart3, TrendingUp, Bell, ArrowRight, Code2, Mail } from 'lucide-react';

const features = [
  { icon: MessageSquare, title: 'AI Chat Interface', desc: 'Conversational crime intelligence in English & Kannada with NL2SQL, voice support, and evidence-backed answers.' },
  { icon: GitBranch, title: 'Criminal Network Graph', desc: 'Visualize relationships between accused individuals with entity resolution, community detection, and risk scoring.' },
  { icon: BarChart3, title: 'Crime Analytics', desc: 'DBSCAN hotspot detection, trend analysis, and sociological crime pattern identification across Karnataka.' },
  { icon: TrendingUp, title: 'Prophet Forecasting', desc: '30-day crime forecasts with confidence intervals, seasonal pattern detection, and automated alerts.' },
  { icon: Shield, title: 'Priority Scoring', desc: 'Multi-feature offender prioritization (v1.0.0) with deterministic hashing for reproducible risk assessment.' },
  { icon: Bell, title: 'Smart Alerts', desc: 'Rule-based alert engine for surge detection, recidivism monitoring, and threshold breaches.' },
];

export const LandingPage: React.FC = () => {
  const navigate = useNavigate();

  return (
    <div style={{ minHeight: '100vh', background: 'var(--bg-primary)' }}>
      <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '20px 48px', borderBottom: '1px solid var(--border)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <Shield size={28} color="var(--primary)" />
          <span style={{ fontSize: 20, fontWeight: 700, color: 'var(--primary)' }}>Suraksha AI</span>
        </div>
        <div style={{ display: 'flex', gap: 12 }}>
          <button className="btn btn-ghost" onClick={() => navigate('/login')}>Sign In</button>
          <button className="btn btn-primary" onClick={() => navigate('/login')}>Get Started <ArrowRight size={16} /></button>
        </div>
      </header>

      <section style={{ textAlign: 'center', padding: '100px 48px 80px', maxWidth: 800, margin: '0 auto' }}>
        <Shield size={64} color="var(--primary)" style={{ marginBottom: 24 }} />
        <h1 style={{ fontSize: 48, fontWeight: 800, marginBottom: 16, color: 'var(--text-primary)' }}>
          Intelligent Crime Analytics<br />for Karnataka Police
        </h1>
        <p style={{ fontSize: 18, color: 'var(--text-muted)', marginBottom: 40, lineHeight: 1.7 }}>
          Suraksha AI is a full-stack conversational crime analytics platform built for KSP Datathon 2026.
          Powered by Zoho Catalyst, it combines NL2SQL chat, network graphs, hotspot detection,
          Prophet forecasting, and offender scoring into one unified dashboard.
        </p>
        <div style={{ display: 'flex', gap: 16, justifyContent: 'center' }}>
          <button className="btn btn-primary" style={{ padding: '14px 32px', fontSize: 16 }} onClick={() => navigate('/login')}>
            Launch Dashboard <ArrowRight size={18} />
          </button>
          <button className="btn btn-secondary" style={{ padding: '14px 32px', fontSize: 16 }} onClick={() => navigate('/login')}>
            View Demo
          </button>
        </div>
      </section>

      <section style={{ padding: '60px 48px', maxWidth: 1200, margin: '0 auto' }}>
        <h2 style={{ textAlign: 'center', fontSize: 32, fontWeight: 700, marginBottom: 48, color: 'var(--text-primary)' }}>Key Features</h2>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 24 }}>
          {features.map(f => {
            const Icon = f.icon;
            return (
              <div key={f.title} className="card" style={{ padding: 32 }}>
                <Icon size={32} color="var(--primary)" style={{ marginBottom: 16 }} />
                <h3 style={{ fontSize: 18, fontWeight: 600, marginBottom: 8, color: 'var(--text-primary)' }}>{f.title}</h3>
                <p style={{ fontSize: 14, color: 'var(--text-muted)', lineHeight: 1.6 }}>{f.desc}</p>
              </div>
            );
          })}
        </div>
      </section>

      <footer style={{ textAlign: 'center', padding: '40px 48px', borderTop: '1px solid var(--border)', color: 'var(--text-muted)', fontSize: 13 }}>
        <div style={{ display: 'flex', justifyContent: 'center', gap: 16, marginBottom: 12 }}>
          <Code2 size={18} /><Mail size={18} />
        </div>
        <p>Suraksha AI — KSP Datathon 2026 | Built on Zoho Catalyst</p>
      </footer>
    </div>
  );
};
