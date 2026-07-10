import React, { useState } from 'react';
import { Search, AlertTriangle } from 'lucide-react';
import { OffenderProfile } from '../types';
import { api } from '../services/api';

const tierColors: Record<string, { color: string; bg: string }> = {
  LOW: { color: '#22C55E', bg: 'rgba(34,197,94,0.15)' },
  MODERATE: { color: '#3B82F6', bg: 'rgba(59,130,246,0.15)' },
  ELEVATED: { color: '#F59E0B', bg: 'rgba(245,158,11,0.15)' },
  HIGH: { color: '#EF4444', bg: 'rgba(239,68,68,0.15)' },
};

export const OffenderPage: React.FC = () => {
  const [search, setSearch] = useState('');
  const [profile, setProfile] = useState<OffenderProfile | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async () => {
    if (!search.trim()) return;
    setLoading(true);
    setError('');
    try {
      const data = await api.getOffenderProfile(search);
      setProfile(data);
    } catch {
      setError('No accused found matching that name.');
    }
    setLoading(false);
  };

  return (
    <div>
      <div className="page-header">
        <h1>Offender Profile</h1>
        <p>Investigation Priority Scoring & Case History</p>
      </div>

      <div className="flex gap-4 items-center mb-4">
        <div className="input-group" style={{ flex: 1, maxWidth: 400 }}>
          <Search className="input-icon" size={18} />
          <input className="input" placeholder="Search accused name..." value={search}
            onChange={e => setSearch(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleSearch()} />
        </div>
        <button className="btn btn-primary" onClick={handleSearch} disabled={loading}>
          {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {error && <div className="card" style={{ color: 'var(--danger)', marginBottom: 16, padding: 16 }}>{error}</div>}

      {!profile && !loading && (
        <div className="card" style={{ textAlign: 'center', padding: 80 }}>
          <Search size={48} style={{ color: 'var(--text-muted)', marginBottom: 16 }} />
          <h3 style={{ color: 'var(--text-secondary)', marginBottom: 8 }}>Search for an accused person</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>Enter a name to view their priority score and case history</p>
        </div>
      )}

      {loading && (
        <div className="grid-2">
          <div className="skeleton" style={{ height: 300, borderRadius: 'var(--radius-card)' }} />
          <div className="skeleton" style={{ height: 400, borderRadius: 'var(--radius-card)' }} />
        </div>
      )}

      {profile && (
        <>
          <div className="grid-2">
            {/* Score Card */}
            <div className="card">
              <div className="score-display">
                <div className="score-number" style={{ color: tierColors[profile.risk_tier]?.color || 'var(--text-primary)' }}>
                  {profile.total_score.toFixed(2)}
                </div>
                <div className="score-tier" style={{ color: tierColors[profile.risk_tier]?.color || 'var(--text-primary)' }}>
                  {profile.risk_tier}
                </div>
                <div className="score-label">Investigation Priority Score v1.0.0 — {profile.entity_name}</div>
              </div>

              <div style={{ marginTop: 24 }}>
                {profile.features.map((feat, i) => (
                  <div key={i} className="feature-row">
                    <div className="feature-info">
                      <div className="feature-name">{feat.name}</div>
                      <div className="feature-raw">{feat.raw_value}</div>
                    </div>
                    <div className="feature-bar-container">
                      <div className="progress-bar">
                        <div className="progress-fill" style={{ width: `${feat.normalized_value * 100}%` }} />
                      </div>
                      <div className="feature-weight">Weight: {(feat.weight * 100).toFixed(0)}%</div>
                    </div>
                    <div className="feature-contribution" style={{ color: 'var(--primary)' }}>
                      +{feat.contribution.toFixed(1)}
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Case History */}
            <div>
              <div className="card" style={{ marginBottom: 16 }}>
                <div className="card-header">Linked Cases ({profile.linked_cases.length})</div>
                <div className="table-container">
                  <table>
                    <thead>
                      <tr>
                        <th>Crime No</th>
                        <th>Type</th>
                        <th>Year</th>
                        <th>Status</th>
                      </tr>
                    </thead>
                    <tbody>
                      {profile.linked_cases.map(c => (
                        <tr key={c.case_id}>
                          <td style={{ fontFamily: 'monospace', fontSize: 12 }}>{c.crime_no}</td>
                          <td>{c.crime_type}</td>
                          <td>{c.year}</td>
                          <td><span className={`badge ${c.status === 'Under Investigation' ? 'badge-elevated' : c.status === 'Charge Sheeted' ? 'badge-info' : c.status === 'Closed' ? 'badge-low' : 'badge-moderate'}`}>{c.status}</span></td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </div>
            </div>
          </div>

          {/* Disclaimer */}
          <div className="card" style={{ borderLeft: '4px solid var(--warning)' }}>
            <div className="flex gap-3">
              <AlertTriangle size={20} color="var(--warning)" style={{ flexShrink: 0 }} />
              <div>
                <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>Important Notice</div>
                <p style={{ fontSize: 13, color: 'var(--text-muted)', lineHeight: 1.6 }}>
                  {profile.disclaimer}
                  <br />This score is an analytical tool for investigation prioritization. It does not indicate guilt, dangerousness, or likelihood of future crime. Decisions must incorporate officer judgment and legal procedures.
                </p>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
};
