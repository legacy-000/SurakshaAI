import React, { useState, useRef, useEffect } from 'react';
import { Search, Network as LucideNetwork, Bot, ChevronDown, ChevronUp, X } from 'lucide-react';
import { Network as VisNetwork } from 'vis-network';
import { api } from '../services/api';
import { useLanguage } from '../context/LanguageContext';

let DataSetCtor: any = null;
async function getDataSet() {
  if (!DataSetCtor) {
    const mod: any = await import('vis-data');
    DataSetCtor = mod.DataSet || mod.default?.DataSet;
  }
  return DataSetCtor;
}

const mockMetrics = {
  density: 0.42,
  largestClusterSize: 6,
  centralFigures: ['Ravi Kumar', 'Suresh P', 'Rajesh K'],
  bridges: ['Manoj R', 'Venkatesh G'],
};

const tireColors: Record<string, string> = {
  LOW: '#22C55E', MODERATE: '#3B82F6', ELEVATED: '#F59E0B', HIGH: '#EF4444',
};

export const NetworkPage: React.FC = () => {
  const { t } = useLanguage();
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [graphData, setGraphData] = useState<{ nodes: any[]; edges: any[] } | null>(null);
  const [error, setError] = useState('');
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [showAi, setShowAi] = useState(true);
  const [aiMsg, setAiMsg] = useState(t('I am NetworkAI. Select a node or ask about connections.', 'ನಾನು ನೆಟ್‌ವರ್ಕ್-ಎಐ. ನೋಡ್ ಆಯ್ಕೆಮಾಡಿ ಅಥವಾ ಸಂಪರ್ಕಗಳ ಬಗ್ಗೆ ಕೇಳಿ.'));
  const [layout, setLayout] = useState('force-directed');
  const [nodeSizeBy, setNodeSizeBy] = useState('centrality');
  const [nodeColorBy] = useState('risk_tier');

  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<any>(null);

  useEffect(() => {
    if (!graphData || !containerRef.current) return;
    let destroyed = false;
    (async () => {
      const DS = await getDataSet();
      if (destroyed || !containerRef.current) return;
      if (networkRef.current) { networkRef.current.destroy(); networkRef.current = null; }

      const nodes = new DS(graphData.nodes.map((n: any) => ({
        id: n.id, label: `${n.label}\n${n.cases} cases`,
        title: `Cases: ${n.cases}\nRisk: ${n.risk_tier || 'Unknown'}`,
        color: tireColors[n.risk_tier] || '#6C63FF',
        value: nodeSizeBy === 'centrality' ? Math.min(n.cases * 5, 60) : n.cases * 3,
        shape: 'dot', size: Math.min(n.cases * 5, 60),
      })));
      const edges = new DS(graphData.edges.map((e: any) => ({
        id: e.id, from: e.source, to: e.target,
        width: Math.min(e.weight * 2, 10),
        title: `${e.weight} shared case(s)`,
        color: { color: 'rgba(255,255,255,0.2)', hover: 'var(--primary)', highlight: 'var(--primary)' },
      })));

      const container = containerRef.current;
      const visNetwork = new VisNetwork(container, { nodes, edges }, {
        nodes: { font: { color: 'var(--text-primary)', size: 12 }, borderWidth: 2 },
        edges: { smooth: { enabled: true, type: 'continuous', roundness: 0.5 } },
        physics: { solver: layout === 'hierarchical' ? 'hierarchicalRepulsion' : 'forceAtlas2Based', forceAtlas2Based: { gravitationalConstant: -40, centralGravity: 0.005, springLength: 120, springConstant: 0.08 }, hierarchicalRepulsion: { nodeDistance: 120 } },
        interaction: { hover: true, tooltipDelay: 200 },
        layout: layout === 'hierarchical' ? { hierarchical: { direction: 'UD', sortMethod: 'directed' } } : undefined,
      });

      visNetwork.on('click', (params: any) => {
        if (params.nodes.length > 0) {
          const nodeId = params.nodes[0];
          const node = graphData.nodes.find((n: any) => n.id === nodeId);
          if (node) {
            setSelectedNode(node);
            setAiMsg(`${node.label}: ${node.cases} ${t('cases', 'ಪ್ರಕರಣಗಳು')}, ${t('risk tier', 'ಅಪಾಯದ ಮಟ್ಟ')}: ${node.risk_tier}`);
          }
        }
      });

      networkRef.current = visNetwork;
    })();
    return () => { destroyed = true; };
  }, [graphData, layout, nodeSizeBy, nodeColorBy, t]);

  const handleSearch = async () => {
    if (!search.trim()) return;
    setLoading(true); setError(''); setSelectedNode(null);
    try {
      const data = await api.getNetwork(search);
      setGraphData(data);
    } catch {
      setError(t('Failed to load network.', 'ನೆಟ್‌ವರ್ಕ್ ಲೋಡ್ ಮಾಡಲು ವಿಫಲವಾಗಿದೆ.'));
    }
    setLoading(false);
  };

  return (
    <div style={{ display: 'flex', gap: 24 }}>
      <div style={{ flex: 1 }}>
        <div className="page-header">
          <h1>{t('Network Intelligence', 'ನೆಟ್‌ವರ್ಕ್ ಇಂಟೆಲಿಜೆನ್ಸ್')}</h1>
          <p>{t('Criminal network analysis and relationship mapping', 'ಅಪರಾಧಿ ಜಾಲ ವಿಶ್ಲೇಷಣೆ ಮತ್ತು ಸಂಬಂಧ ಮ್ಯಾಪಿಂಗ್')}</p>
        </div>

        {/* Search Bar */}
        <div className="card" style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', gap: 12 }}>
            <div className="input-group" style={{ flex: 1 }}>
              <Search className="input-icon" size={18} />
              <input className="input" placeholder={t('Search by accused name...', 'ಆರೋಪಿಯ ಹೆಸರಿನಿಂದ ಹುಡುಕಿ...')}
                value={search} onChange={e => setSearch(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSearch()} />
            </div>
            <button className="btn btn-primary" onClick={handleSearch} disabled={loading}>{t('Analyze', 'ವಿಶ್ಲೇಷಿಸಿ')}</button>
          </div>
        </div>

        {/* Graph Controls */}
        <div className="card" style={{ marginBottom: 16, padding: 12 }}>
          <div className="flex gap-3" style={{ flexWrap: 'wrap', alignItems: 'center' }}>
            <span className="text-xs text-muted">{t('Layout', 'ವಿನ್ಯಾಸ')}:</span>
            <select className="input" style={{ width: 'auto', fontSize: 12, padding: '4px 8px' }} value={layout} onChange={e => setLayout(e.target.value)}>
              <option value="force-directed">{t('Force-directed', 'ಬಲ-ನಿರ್ದೇಶಿತ')}</option>
              <option value="hierarchical">{t('Hierarchical', 'ಶ್ರೇಣೀಬದ್ಧ')}</option>
            </select>
            <span className="text-xs text-muted">{t('Node size by', 'ನೋಡ್ ಗಾತ್ರ')}:</span>
            <select className="input" style={{ width: 'auto', fontSize: 12, padding: '4px 8px' }} value={nodeSizeBy} onChange={e => setNodeSizeBy(e.target.value)}>
              <option value="centrality">{t('Centrality', 'ಕೇಂದ್ರೀಯತೆ')}</option>
              <option value="cases">{t('Cases', 'ಪ್ರಕರಣಗಳು')}</option>
            </select>
            <button className="btn btn-ghost btn-sm" onClick={() => networkRef.current?.fit()}>{t('Reset View', 'ವೀಕ್ಷಣೆ ಮರುಹೊಂದಿಸಿ')}</button>
          </div>
        </div>

        {loading && <div className="skeleton" style={{ width: '100%', height: 400, borderRadius: 12 }} />}
        {error && <div className="card" style={{ borderLeft: '4px solid var(--danger)' }}><p style={{ color: 'var(--danger)' }}>{error}</p></div>}

        {graphData && (
          <div className="grid-2" style={{ marginBottom: 24 }}>
            {/* Network Graph */}
            <div className="card" style={{ gridColumn: '1 / -1' }}>
              <div ref={containerRef} className="network-container" style={{ height: 500 }} />
            </div>
          </div>
        )}

        {/* Network Metrics */}
        {graphData && (
          <div className="card">
            <div className="card-header flex items-center gap-2"><LucideNetwork size={16} /> {t('Network Metrics', 'ನೆಟ್‌ವರ್ಕ್ ಮೆಟ್ರಿಕ್‌ಗಳು')}</div>
            <div className="grid-4" style={{ gap: 16 }}>
              <div className="card" style={{ padding: 16, textAlign: 'center' }}>
                <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--primary)' }}>{mockMetrics.density}</div>
                <div className="text-xs text-muted">{t('Network Density', 'ನೆಟ್‌ವರ್ಕ್ ಸಾಂದ್ರತೆ')}</div>
              </div>
              <div className="card" style={{ padding: 16, textAlign: 'center' }}>
                <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--warning)' }}>{mockMetrics.largestClusterSize}</div>
                <div className="text-xs text-muted">{t('Largest Cluster (nodes)', 'ದೊಡ್ಡ ಸಮೂಹ (ನೋಡ್‌ಗಳು)')}</div>
              </div>
              <div className="card" style={{ padding: 16, textAlign: 'center' }}>
                <div style={{ fontSize: 18, fontWeight: 600, color: 'var(--danger)' }}>{mockMetrics.centralFigures.join(', ')}</div>
                <div className="text-xs text-muted">{t('Central Figures', 'ಕೇಂದ್ರ ವ್ಯಕ್ತಿಗಳು')}</div>
              </div>
              <div className="card" style={{ padding: 16, textAlign: 'center' }}>
                <div style={{ fontSize: 18, fontWeight: 600, color: 'var(--blue)' }}>{mockMetrics.bridges.join(', ')}</div>
                <div className="text-xs text-muted">{t('Bridges', 'ಸೇತುವೆಗಳು')}</div>
              </div>
            </div>
          </div>
        )}

        {/* Node Details */}
        {selectedNode && (
          <div className="card" style={{ marginTop: 16 }}>
            <div className="card-header flex justify-between items-center">
              <h3>{t('Node Details', 'ನೋಡ್ ವಿವರಗಳು')}: {selectedNode.label}</h3>
              <button className="btn btn-ghost btn-icon" onClick={() => setSelectedNode(null)}><X size={18} /></button>
            </div>
            <div className="grid-2">
              <div>
                <div className="text-sm"><strong>{t('Name', 'ಹೆಸರು')}:</strong> {selectedNode.label}</div>
                <div className="text-sm"><strong>{t('Cases', 'ಪ್ರಕರಣಗಳು')}:</strong> {selectedNode.cases}</div>
                <div className="text-sm"><strong>{t('Risk Tier', 'ಅಪಾಯದ ಮಟ್ಟ')}:</strong> <span className={`badge ${(selectedNode.risk_tier || '').toLowerCase() === 'high' ? 'badge-high' : (selectedNode.risk_tier || '').toLowerCase() === 'elevated' ? 'badge-elevated' : (selectedNode.risk_tier || '').toLowerCase() === 'moderate' ? 'badge-moderate' : 'badge-low'}`}>{selectedNode.risk_tier || 'Unknown'}</span></div>
              </div>
              <div>
                <button className="btn btn-secondary btn-sm" style={{ marginRight: 8 }} onClick={() => window.location.hash = `/offender?name=${encodeURIComponent(selectedNode.label)}`}>
                  {t('View Dossier', 'ಡಾಸಿಯರ್ ವೀಕ್ಷಿಸಿ')}
                </button>
                <button className="btn btn-ghost btn-sm" onClick={() => setAiMsg(t('Building expanded network for', 'ವಿಸ್ತೃತ ನೆಟ್‌ವರ್ಕ್ ನಿರ್ಮಿಸಲಾಗುತ್ತಿದೆ') + ' ' + selectedNode.label)}>
                  {t('Expand Network', 'ನೆಟ್‌ವರ್ಕ್ ವಿಸ್ತರಿಸಿ')}
                </button>
              </div>
            </div>
          </div>
        )}
      </div>

      {/* NetworkAI Panel */}
      <div style={{ width: 280, flexShrink: 0 }}>
        <div className="card" style={{ position: 'sticky', top: 32 }}>
          <div className="card-header flex justify-between items-center">
            <span className="flex items-center gap-2"><Bot size={20} /> {t('NetworkAI', 'ನೆಟ್‌ವರ್ಕ್-ಎಐ')}</span>
            <button className="btn btn-ghost btn-icon" onClick={() => setShowAi(!showAi)}>
              {showAi ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
            </button>
          </div>
          {showAi && (
            <div style={{ fontSize: 14, color: 'var(--text-secondary)' }}>
              <div style={{ marginBottom: 12, padding: 12, background: 'var(--bg-hover)', borderRadius: 8, fontSize: 13, minHeight: 40 }}>
                {aiMsg}
              </div>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                <button className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }}
                  onClick={() => setAiMsg(t('Network density 0.42 indicates moderate connectivity. 3 distinct communities identified. Ravi Kumar is the most central figure, appearing in 80% of shortest paths.', 'ನೆಟ್‌ವರ್ಕ್ ಸಾಂದ್ರತೆ 0.42 ಮಧ್ಯಮ ಸಂಪರ್ಕವನ್ನು ಸೂಚಿಸುತ್ತದೆ. 3 ವಿಭಿನ್ನ ಸಮುದಾಯಗಳನ್ನು ಗುರುತಿಸಲಾಗಿದೆ. ರವಿ ಕುಮಾರ್ ಅತ್ಯಂತ ಕೇಂದ್ರ ವ್ಯಕ್ತಿ, 80% ಕಿರು ಮಾರ್ಗಗಳಲ್ಲಿ ಕಾಣಿಸಿಕೊಂಡಿದ್ದಾರೆ.'))}>
                  {t('Network interpretation?', 'ನೆಟ್‌ವರ್ಕ್ ವ್ಯಾಖ್ಯಾನ?')}
                </button>
                <button className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }}
                  onClick={() => setAiMsg(t('Highest priority person: Ravi Kumar (ELEVATED risk, 8 cases, central to network). Recommend prioritizing investigation and monitoring.', 'ಅತ್ಯಧಿಕ ಆದ್ಯತೆಯ ವ್ಯಕ್ತಿ: ರವಿ ಕುಮಾರ್ (ಏರಿಕೆ ಅಪಾಯ, 8 ಪ್ರಕರಣಗಳು, ನೆಟ್‌ವರ್ಕ್‌ನಲ್ಲಿ ಕೇಂದ್ರ). ತನಿಖೆ ಮತ್ತು ಮೇಲ್ವಿಚಾರಣೆಗೆ ಆದ್ಯತೆ ನೀಡಲು ಶಿಫಾರಸು.'))}>
                  {t('Highest priority?', 'ಅತ್ಯಧಿಕ ಆದ್ಯತೆ?')}
                </button>
                <button className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start' }}
                  onClick={() => setAiMsg(t('3 new connections in last 30 days. Emerging link between Ravi Kumar and Rajesh K through case #CN202400204.', 'ಕಳೆದ 30 ದಿನಗಳಲ್ಲಿ 3 ಹೊಸ ಸಂಪರ್ಕಗಳು. ಪ್ರಕರಣ #CN202400204 ಮೂಲಕ ರವಿ ಕುಮಾರ್ ಮತ್ತು ರಾಜೇಶ್ ಕೆ ನಡುವೆ ಹೊಸ ಸಂಪರ್ಕ ಹೊರಹೊಮ್ಮಿದೆ.'))}>
                  {t('Emerging connections?', 'ಹೊಸ ಸಂಪರ್ಕಗಳು?')}
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
