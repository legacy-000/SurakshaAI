import React, { useState } from 'react';
import { useLanguage } from '../context/LanguageContext';
import { Bot, ChevronDown, ChevronUp, Search, TrendingUp, MapPin, Users } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';

const mockCases = [
  { crime_no: '104430006202600001', complainant: 'Ravi Kumar', accused_count: 2, head: 'Theft', location: 'Bengaluru South', date: '2026-03-15', snippet: 'Motorcycle theft from Whitefield, accused used duplicate key...' },
  { crime_no: '104430006202600015', complainant: 'Priya Sharma', accused_count: 1, head: 'Robbery', location: 'Mysuru', date: '2026-04-02', snippet: 'Armed robbery at jewelry store, suspects fled on motorcycle...' },
  { crime_no: '104430006202600042', complainant: 'Anil Kumar', accused_count: 3, head: 'Assault', location: 'Hubballi', date: '2026-05-10', snippet: 'Group assault near bus stand, weapons used...' },
  { crime_no: '104430006202500312', complainant: 'Sunil D', accused_count: 1, head: 'Cheating', location: 'Belagavi', date: '2025-11-20', snippet: 'Property fraud through forged documents...' },
  { crime_no: '104430006202600088', complainant: 'Meena Rao', accused_count: 4, head: 'Cyber Crime', location: 'Bengaluru Urban', date: '2026-06-01', snippet: 'Phishing attack on banking customers, 12 victims...' },
];

const mockSimilarResults = [
  { crime_no: '104430006202400112', similarity: 87, fact_sim: 82, category_match: true, location_prox: 0.3, temporal_prox: 2, head: 'Theft', status: 'Chargesheeted', snippet: 'Motorcycle theft with duplicate key modus operandi matches...' },
  { crime_no: '104430006202400205', similarity: 72, fact_sim: 68, category_match: true, location_prox: 0.8, temporal_prox: 5, head: 'Theft', status: 'Under Investigation', snippet: 'Two-wheeler theft from parking lot, similar time window...' },
  { crime_no: '104430006202300445', similarity: 65, fact_sim: 71, category_match: false, location_prox: 1.2, temporal_prox: 14, head: 'Robbery', status: 'Closed', snippet: 'Vehicle theft involving same area and similar suspect description...' },
  { crime_no: '104430006202500098', similarity: 58, fact_sim: 55, category_match: true, location_prox: 2.5, temporal_prox: 8, head: 'Theft', status: 'Under Investigation', snippet: 'Burglary in adjacent area, different modus operandi...' },
  { crime_no: '104430006202400331', similarity: 45, fact_sim: 42, category_match: true, location_prox: 5.0, temporal_prox: 18, head: 'Theft', status: 'Charge Sheeted', snippet: 'Different theft method but same crime category...' },
];

const monthlyPatternData = [
  { month: 'Aug', cases: 12 }, { month: 'Sep', cases: 18 }, { month: 'Oct', cases: 24 },
  { month: 'Nov', cases: 20 }, { month: 'Dec', cases: 28 }, { month: 'Jan', cases: 22 },
  { month: 'Feb', cases: 30 }, { month: 'Mar', cases: 26 }, { month: 'Apr', cases: 34 },
  { month: 'May', cases: 28 }, { month: 'Jun', cases: 36 }, { month: 'Jul', cases: 42 },
];

export const SimilarityPage: React.FC = () => {
  const { t } = useLanguage();
  const [selectedCase, setSelectedCase] = useState<string>('');
  const [showResults, setShowResults] = useState(false);
  const [similarityThreshold, setSimilarityThreshold] = useState(50);
  const [patternBotMsg, setPatternBotMsg] = useState(t('I am PatternBot. Select a case to find similar patterns.', 'ನಾನು ಪ್ಯಾಟರ್ನ್-ಬಾಟ್. ಮಾದರಿಗಳನ್ನು ಹುಡುಕಲು ಪ್ರಕರಣವನ್ನು ಆಯ್ಕೆಮಾಡಿ.'));
  const [showBot, setShowBot] = useState(true);

  const handleAnalyze = () => {
    if (!selectedCase) return;
    setShowResults(true);
    setPatternBotMsg(t('Analyzing case...', 'ಪ್ರಕರಣ ವಿಶ್ಲೇಷಿಸಲಾಗುತ್ತಿದೆ...') + ' ' + selectedCase);
  };

  const selectedCaseData = mockCases.find(c => c.crime_no === selectedCase);
  const filteredResults = mockSimilarResults.filter(r => r.similarity >= similarityThreshold);

  return (
    <div style={{ display: 'flex', gap: 24 }}>
      <div style={{ flex: 1 }}>
        <div className="page-header">
          <h1>{t('Case Similarity & Pattern Detection', 'ಪ್ರಕರಣ ಹೋಲಿಕೆ ಮತ್ತು ಮಾದರಿ ಪತ್ತೆ')}</h1>
          <p>{t('Identify similar cases and detect recurring crime patterns', 'ಒಂದೇ ರೀತಿಯ ಪ್ರಕರಣಗಳನ್ನು ಗುರುತಿಸಿ ಮತ್ತು ಪುನರಾವರ್ತಿತ ಅಪರಾಧ ಮಾದರಿಗಳನ್ನು ಪತ್ತೆ ಮಾಡಿ')}</p>
        </div>

        {/* Input Section */}
        <div className="card" style={{ marginBottom: 24 }}>
          <div className="card-header">{t('Select Case to Analyze', 'ವಿಶ್ಲೇಷಿಸಲು ಪ್ರಕರಣ ಆಯ್ಕೆಮಾಡಿ')}</div>
          <div style={{ display: 'flex', gap: 12 }}>
            <select className="input" value={selectedCase} onChange={e => setSelectedCase(e.target.value)} style={{ flex: 1 }}>
              <option value="">-- {t('Select a case by Crime No', 'ಅಪರಾಧ ಸಂಖ್ಯೆಯಿಂದ ಪ್ರಕರಣ ಆಯ್ಕೆಮಾಡಿ')} --</option>
              {mockCases.map(c => (
                <option key={c.crime_no} value={c.crime_no}>{c.crime_no} — {c.head} ({c.location})</option>
              ))}
            </select>
            <button className="btn btn-primary" onClick={handleAnalyze} disabled={!selectedCase}>
              <Search size={16} /> {t('Find Similar Cases', 'ಹೋಲುವ ಪ್ರಕರಣಗಳನ್ನು ಹುಡುಕಿ')}
            </button>
          </div>
          {selectedCaseData && (
            <div className="card" style={{ marginTop: 16, padding: 16 }}>
              <div className="flex justify-between items-center">
                <div>
                  <span style={{ fontFamily: 'monospace', fontWeight: 600 }}>{selectedCaseData.crime_no}</span>
                  <span className="badge badge-info" style={{ marginLeft: 8 }}>{selectedCaseData.head}</span>
                </div>
                <span className="text-xs text-muted">{selectedCaseData.location} · {selectedCaseData.date}</span>
              </div>
              <p className="text-sm text-muted" style={{ marginTop: 8 }}>{selectedCaseData.snippet}</p>
              <div className="text-xs text-muted">{t('Complainant', 'ದೂರುದಾರ')}: {selectedCaseData.complainant} · {selectedCaseData.accused_count} {t('accused', 'ಆರೋಪಿಗಳು')}</div>
            </div>
          )}
        </div>

        {showResults && (
          <>
            {/* Similarity Threshold Slider */}
            <div className="card" style={{ marginBottom: 16, padding: 16 }}>
              <div className="flex justify-between items-center">
                <span style={{ fontSize: 14, fontWeight: 500 }}>{t('Similarity Threshold', 'ಹೋಲಿಕೆ ಮಿತಿ')}: {similarityThreshold}%</span>
                <span className="text-xs text-muted">{filteredResults.length} {t('results', 'ಫಲಿತಾಂಶಗಳು')}</span>
              </div>
              <input type="range" min={0} max={100} value={similarityThreshold} onChange={e => setSimilarityThreshold(parseInt(e.target.value))}
                style={{ width: '100%', marginTop: 8 }} />
            </div>

            <div className="grid-2" style={{ marginBottom: 24 }}>
              {/* Similar Cases */}
              <div>
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>{t('Similar Cases', 'ಹೋಲುವ ಪ್ರಕರಣಗಳು')}</h3>
                {filteredResults.map((r, i) => (
                  <div key={i} className="card" style={{ marginBottom: 12, cursor: 'pointer' }}
                    onClick={() => setPatternBotMsg(`${r.crime_no} — ${r.similarity}% ${t('similar', 'ಹೋಲಿಕೆ')}. ${r.snippet}`)}>
                    <div className="flex justify-between items-center" style={{ marginBottom: 6 }}>
                      <span style={{ fontFamily: 'monospace', fontSize: 13 }}>{r.crime_no}</span>
                      <span className="badge badge-info" style={{ fontSize: 12 }}>{r.similarity}%</span>
                    </div>
                    <div className="flex gap-2" style={{ marginBottom: 4 }}>
                      <span className={`badge ${r.status === 'Chargesheeted' ? 'badge-low' : r.status === 'Under Investigation' ? 'badge-elevated' : 'badge-moderate'}`} style={{ fontSize: 10 }}>
                        {r.status}
                      </span>
                      {r.category_match && <span className="badge badge-info" style={{ fontSize: 10 }}>{t('Same category', 'ಒಂದೇ ವರ್ಗ')}</span>}
                    </div>
                    <p className="text-xs text-muted">{r.snippet}</p>
                    <div className="text-xs text-muted" style={{ marginTop: 4 }}>
                      {t('Facts', 'ಸಂಗತಿಗಳು')}: {r.fact_sim}% · {t('Location', 'ಸ್ಥಳ')}: {r.location_prox}km · {t('Time', 'ಸಮಯ')}: {r.temporal_prox}mo
                    </div>
                  </div>
                ))}
                {filteredResults.length === 0 && (
                  <p className="text-muted text-sm">{t('No cases meet the threshold. Try lowering it.', 'ಯಾವುದೇ ಪ್ರಕರಣಗಳು ಮಿತಿಯನ್ನು ಪೂರೈಸುವುದಿಲ್ಲ. ಮಿತಿಯನ್ನು ಕಡಿಮೆ ಮಾಡಿ.')}</p>
                )}
              </div>

              {/* Pattern Detection */}
              <div>
                <h3 style={{ fontSize: 16, fontWeight: 600, marginBottom: 12 }}>{t('Pattern Detection', 'ಮಾದರಿ ಪತ್ತೆ')}</h3>

                <div className="card" style={{ marginBottom: 12 }}>
                  <div className="card-header flex items-center gap-2" style={{ fontSize: 14 }}><TrendingUp size={14} /> {t('Temporal Pattern', 'ಕಾಲಿಕ ಮಾದರಿ')}</div>
                  <ResponsiveContainer width="100%" height={160}>
                    <BarChart data={monthlyPatternData}>
                      <XAxis dataKey="month" fontSize={10} stroke="var(--text-muted)" />
                      <YAxis fontSize={10} stroke="var(--text-muted)" />
                      <Tooltip contentStyle={{ background: 'var(--bg-card)', border: '1px solid var(--border)', borderRadius: 8, fontSize: 12 }} />
                      <Bar dataKey="cases" fill="var(--primary)" radius={[4, 4, 0, 0]} />
                    </BarChart>
                  </ResponsiveContainer>
                  <p className="text-xs text-muted" style={{ marginTop: 8 }}>
                    {t('Trend: Increasing — cases up 250% YoY', 'ಪ್ರವೃತ್ತಿ: ಹೆಚ್ಚಳ — ಪ್ರಕರಣಗಳು ವರ್ಷದಿಂದ ವರ್ಷಕ್ಕೆ 250% ಹೆಚ್ಚಳ')}
                  </p>
                </div>

                <div className="card" style={{ marginBottom: 12 }}>
                  <div className="card-header flex items-center gap-2" style={{ fontSize: 14 }}><MapPin size={14} /> {t('Geographic Clustering', 'ಭೌಗೋಳಿಕ ಸಮೂಹ')}</div>
                  <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                    {t('Hotspot areas identified: Whitefield (12 cases), Koramangala (8 cases), Indiranagar (6 cases)', 'ಹಾಟ್‌ಸ್ಪಾಟ್ ಪ್ರದೇಶಗಳು ಗುರುತಿಸಲಾಗಿದೆ: ವೈಟ್‌ಫೀಲ್ಡ್ (12), ಕೋರಮಂಗಲ (8), ಇಂದಿರಾನಗರ (6)')}
                  </p>
                  <button className="btn btn-ghost btn-sm" style={{ marginTop: 8 }} onClick={() => setPatternBotMsg(t('GeoBot analysis recommended for detailed hotspot mapping.', 'ವಿವರವಾದ ಹಾಟ್‌ಸ್ಪಾಟ್ ಮ್ಯಾಪಿಂಗ್ಗಾಗಿ ಜಿಯೋಬಾಟ್ ವಿಶ್ಲೇಷಣೆ ಶಿಫಾರಸು.'))}>
                    {t('View in Geospatial', 'ಭೌಗೋಳಿಕದಲ್ಲಿ ವೀಕ್ಷಿಸಿ')}
                  </button>
                </div>

                <div className="card" style={{ marginBottom: 12 }}>
                  <div className="card-header flex items-center gap-2" style={{ fontSize: 14 }}><Users size={14} /> {t('Offender Recurrence', 'ಅಪರಾಧಿ ಪುನರಾವರ್ತನೆ')}</div>
                  <p className="text-sm" style={{ color: 'var(--text-secondary)' }}>
                    {t('3 repeat offenders identified in this case cluster. Highest: Ravi Kumar (8 cases, 3 districts).', 'ಈ ಪ್ರಕರಣ ಸಮೂಹದಲ್ಲಿ 3 ಪುನರಾವರ್ತಿತ ಅಪರಾಧಿಗಳು ಗುರುತಿಸಲಾಗಿದೆ. ಅತಿ ಹೆಚ್ಚು: ರವಿ ಕುಮಾರ್ (8 ಪ್ರಕರಣಗಳು, 3 ಜಿಲ್ಲೆಗಳು).')}
                  </p>
                  <button className="btn btn-ghost btn-sm" style={{ marginTop: 8 }} onClick={() => window.location.hash = '/offender'}>
                    {t('View Offender Pool', 'ಅಪರಾಧಿ ಪೂಲ್ ವೀಕ್ಷಿಸಿ')}
                  </button>
                </div>
              </div>
            </div>
          </>
        )}
      </div>

      {/* PatternBot AI Panel */}
      <div style={{ width: 280, flexShrink: 0 }}>
        <div className="card" style={{ position: 'sticky', top: 32 }}>
          <div className="card-header flex justify-between items-center">
            <span className="flex items-center gap-2"><Bot size={20} /> {t('PatternBot', 'ಪ್ಯಾಟರ್ನ್-ಬಾಟ್')}</span>
            <button className="btn btn-ghost btn-icon" onClick={() => setShowBot(!showBot)}>
              {showBot ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
            </button>
          </div>
          {showBot && (
            <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
              <div style={{ marginBottom: 12, padding: 12, background: 'var(--bg-hover)', borderRadius: 8, fontSize: 13, minHeight: 40 }}>
                {patternBotMsg}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <button className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }}
                  onClick={() => setPatternBotMsg(t('Analysis: Cases share similar modus operandi (duplicate key theft) and geographic area (Whitefield). 3 cases within 500m radius. Pattern suggests same offender or group.', 'ವಿಶ್ಲೇಷಣೆ: ಪ್ರಕರಣಗಳು ಒಂದೇ ರೀತಿಯ ಕಾರ್ಯವಿಧಾನವನ್ನು (ನಕಲಿ ಕೀ ಕಳ್ಳತನ) ಮತ್ತು ಭೌಗೋಳಿಕ ಪ್ರದೇಶವನ್ನು (ವೈಟ್‌ಫೀಲ್ಡ್) ಹಂಚಿಕೊಳ್ಳುತ್ತವೆ. 500 ಮೀ ತ್ರಿಜ್ಯದಲ್ಲಿ 3 ಪ್ರಕರಣಗಳು. ಒಂದೇ ಅಪರಾಧಿ ಅಥವಾ ಗುಂಪನ್ನು ಸೂಚಿಸುತ್ತದೆ.'))}>
                  {t('Is this a series?', 'ಇದು ಸರಣಿಯೇ?')}
                </button>
                <button className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }}
                  onClick={() => setPatternBotMsg(t('Recommended leads: (1) Check CCTV from Whitefield junction for suspect vehicle, (2) Cross-reference with known offenders in area, (3) Alert surrounding stations about modus operandi.', 'ಶಿಫಾರಸು ಮಾಡಿದ ಸುಳಿವುಗಳು: (1) ವೈಟ್‌ಫೀಲ್ಡ್ ಜಂಕ್ಷನ್ನ ಸಿಸಿಟಿವಿ ಪರಿಶೀಲಿಸಿ, (2) ಪ್ರದೇಶದ ತಿಳಿದಿರುವ ಅಪರಾಧಿಗಳೊಂದಿಗೆ ಕ್ರಾಸ್-ರೆಫರೆನ್ಸ್ ಮಾಡಿ, (3) ಸುತ್ತಮುತ್ತಲಿನ ಠಾಣೆಗಳಿಗೆ ಎಚ್ಚರಿಕೆ ನೀಡಿ.'))}>
                  {t('Recommend leads', 'ಸುಳಿವುಗಳನ್ನು ಶಿಫಾರಸು ಮಾಡಿ')}
                </button>
                <button className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }}
                  onClick={() => setPatternBotMsg(t('Forecast: Based on current pattern and rate of escalation, expect 3-5 more cases in this series over next 30 days if preventive action not taken.', 'ಮುನ್ಸೂಚನೆ: ಪ್ರಸ್ತುತ ಮಾದರಿ ಮತ್ತು ಏರಿಕೆಯ ದರದ ಆಧಾರದ ಮೇಲೆ, ತಡೆಗಟ್ಟುವ ಕ್ರಮ ಕೈಗೊಳ್ಳದಿದ್ದರೆ ಮುಂದಿನ 30 ದಿನಗಳಲ್ಲಿ ಈ ಸರಣಿಯಲ್ಲಿ 3-5 ಹೆಚ್ಚಿನ ಪ್ರಕರಣಗಳನ್ನು ನಿರೀಕ್ಷಿಸಿ.'))}>
                  {t('Forecast next incident', 'ಮುಂದಿನ ಘಟನೆಯ ಮುನ್ಸೂಚನೆ')}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
