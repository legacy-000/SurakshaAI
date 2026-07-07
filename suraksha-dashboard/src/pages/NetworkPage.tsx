import React, { useState, useRef, useEffect } from 'react';
import { Search, Network as LucideNetwork, Users, AlertCircle } from 'lucide-react';
import { Network as VisNetwork } from 'vis-network';
import { api } from '../services/api';

let DataSetCtor: any = null;
async function getDataSet() {
  if (!DataSetCtor) {
    const mod: any = await import('vis-data');
    DataSetCtor = mod.DataSet || mod.default?.DataSet;
  }
  return DataSetCtor;
}

export const NetworkPage: React.FC = () => {
  const [search, setSearch] = useState('');
  const [loading, setLoading] = useState(false);
  const [graphData, setGraphData] = useState<{ nodes: any[]; edges: any[] } | null>(null);
  const [error, setError] = useState('');
  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<any>(null);

  useEffect(() => {
    if (!graphData || !containerRef.current) return;

    let destroyed = false;

    (async () => {
      const DS = await getDataSet();
      if (destroyed || !containerRef.current) return;

      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }

      const nodes = new DS(graphData.nodes.map((n: any) => ({
        id: n.id, label: `${n.label}\n${n.cases} cases`,
        title: `Cases: ${n.cases}\nRisk: ${n.risk_tier || 'Unknown'}`,
        color: n.risk_tier === 'HIGH' ? '#EF4444' : n.risk_tier === 'ELEVATED' ? '#F59E0B' : n.risk_tier === 'MODERATE' ? '#3B82F6' : '#22C55E',
        size: 20 + n.cases * 3,
        borderWidth: 2,
        font: { color: 'var(--text-primary)', size: 12 },
      })));

      const edges = new DS(graphData.edges.map((e: any) => ({
        from: e.source, to: e.target,
        width: e.weight,
        title: `Shared cases: ${e.shared_cases.join(', ')}`,
        color: { color: 'rgba(255,255,255,0.2)', hover: 'var(--primary)' },
        smooth: { type: 'continuous' },
      })));

      networkRef.current = new VisNetwork(containerRef.current, { nodes, edges }, {
        physics: { solver: 'forceAtlas2Based', forceAtlas2Based: { gravitationalConstant: -40, centralGravity: 0.005, springLength: 150 } },
        interaction: { hover: true, tooltipDelay: 100 },
        edges: { smooth: true },
      });
    })();

    return () => {
      destroyed = true;
      if (networkRef.current) {
        networkRef.current.destroy();
        networkRef.current = null;
      }
    };
  }, [graphData]);

  const handleSearch = async () => {
    if (!search.trim()) return;
    setLoading(true);
    setError('');
    try {
      const data = await api.getNetwork(search);
      setGraphData(data);
    } catch {
      setError('No results found. Try a different name.');
    }
    setLoading(false);
  };

  return (
    <div>
      <div className="page-header flex justify-between items-center">
        <div>
          <h1>Criminal Network</h1>
          <p>Visualize relationships between accused individuals</p>
        </div>
        <div className="flex gap-2">
          <button className="btn btn-secondary btn-sm"><Users size={16} /> Detect Communities</button>
        </div>
      </div>

      <div className="flex gap-4 mb-4 items-center">
        <div className="input-group" style={{ flex: 1, maxWidth: 400 }}>
          <Search className="input-icon" size={18} />
          <input className="input" placeholder="Search accused name..." value={search}
            onChange={e => setSearch(e.target.value)} onKeyDown={e => e.key === 'Enter' && handleSearch()} />
        </div>
        <button className="btn btn-primary" onClick={handleSearch} disabled={loading}>
          <LucideNetwork size={16} /> {loading ? 'Searching...' : 'Search'}
        </button>
      </div>

      {error && <div className="card" style={{ color: 'var(--danger)', marginBottom: 16, padding: 16 }}>{error}</div>}

      {!graphData && !loading && (
        <div className="card" style={{ textAlign: 'center', padding: 80 }}>
          <LucideNetwork size={48} style={{ color: 'var(--text-muted)', marginBottom: 16 }} />
          <h3 style={{ color: 'var(--text-secondary)', marginBottom: 8 }}>Search for an accused person</h3>
          <p style={{ color: 'var(--text-muted)', fontSize: 14 }}>Enter a name to see their criminal network graph</p>
        </div>
      )}

      {loading && <div className="skeleton" style={{ width: '100%', height: 600, borderRadius: 'var(--radius-card)' }} />}

      {graphData && (
        <div className="grid-2">
          <div className="network-container" ref={containerRef} />
          <div>
            <div className="card" style={{ marginBottom: 16 }}>
              <div className="card-header">Network Summary</div>
              <div style={{ display: 'flex', gap: 24 }}>
                <div><div style={{ fontSize: 28, fontWeight: 700 }}>{graphData.nodes.length}</div><div className="text-muted text-sm">Nodes</div></div>
                <div><div style={{ fontSize: 28, fontWeight: 700 }}>{graphData.edges.length}</div><div className="text-muted text-sm">Connections</div></div>
              </div>
            </div>
            <div className="card" style={{ marginBottom: 16 }}>
              <div className="card-header">Node Legend</div>
              {[
                { color: '#22C55E', label: 'LOW risk' },
                { color: '#3B82F6', label: 'MODERATE risk' },
                { color: '#F59E0B', label: 'ELEVATED risk' },
                { color: '#EF4444', label: 'HIGH risk' },
              ].map(leg => (
                <div key={leg.label} className="flex gap-2 items-center" style={{ marginBottom: 8 }}>
                  <div style={{ width: 12, height: 12, borderRadius: '50%', background: leg.color }} />
                  <span style={{ fontSize: 13, color: 'var(--text-secondary)' }}>{leg.label}</span>
                </div>
              ))}
            </div>
            <div className="card">
              <div className="card-header flex gap-2 items-center">
                <AlertCircle size={16} color="var(--warning)" />
                Entity Resolution Note
              </div>
              <p style={{ fontSize: 13, color: 'var(--text-muted)' }}>
                Names matched with probable_match confidence. Officer verification required.
                Communities are labeled as Candidate — not confirmed organized crime groups.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
