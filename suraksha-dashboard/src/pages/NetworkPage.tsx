import React, { useState, useRef, useEffect, useCallback } from 'react';
import { Search, Network as LucideNetwork, Bot, ChevronDown, ChevronUp, X, Info, Loader2, Send, ExternalLink, Target, Plus, Trash2 } from 'lucide-react';
import { Network as VisNetwork } from 'vis-network';
import { api } from '../services/api';
import { useLanguage } from '../context/LanguageContext';
import type { GraphNode, GraphEdge } from '../types';
// ponytail: vis-data v8 CJS fallback — named export not typed in declarations
const { DataSet } = require('vis-data');

const tireColors: Record<string, string> = {
  LOW: '#22C55E', MODERATE: '#3B82F6', ELEVATED: '#F59E0B', HIGH: '#EF4444',
};
const crimeColors: Record<string, string> = {
  Theft: '#3B82F6', Robbery: '#F59E0B', Burglary: '#8B5CF6',
  Assault: '#EF4444', 'Cyber Crime': '#06B6D4', Cheating: '#EC4899',
};

function computeMetrics(nodes: GraphNode[], edges: GraphEdge[]) {
  const N = nodes.length;
  if (N === 0) return { density: 0, largestClusterSize: 0, centralFigures: [] as string[], bridges: [] as string[] };
  const maxEdges = (N * (N - 1)) / 2;
  const density = maxEdges > 0 ? parseFloat((edges.length / maxEdges).toFixed(2)) : 0;
  const adj: Record<string, Set<string>> = {};
  nodes.forEach(n => { adj[n.id] = new Set(); });
  edges.forEach(e => {
    if (adj[e.source]) adj[e.source].add(e.target);
    if (adj[e.target]) adj[e.target].add(e.source);
  });
  const degree = Object.entries(adj).map(([id, s]) => ({ id, degree: s.size, label: nodes.find(n => n.id === id)?.label || id }));
  degree.sort((a, b) => b.degree - a.degree);
  const centralFigures = degree.slice(0, 3).map(d => d.label);
  const bridges = degree.filter(d => d.degree === 1).slice(0, 2).map(d => d.label);
  let largestClusterSize = 0;
  const visited = new Set<string>();
  for (const n of nodes) {
    if (visited.has(n.id)) continue;
    const queue = [n.id];
    let size = 0;
    visited.add(n.id);
    while (queue.length) {
      const cur = queue.pop()!;
      size++;
      for (const nb of Array.from(adj[cur] || [])) {
        if (!visited.has(nb)) { visited.add(nb); queue.push(nb); }
      }
    }
    largestClusterSize = Math.max(largestClusterSize, size);
  }
  return { density, largestClusterSize, centralFigures, bridges };
}

function getConnectedCaseIds(edges: GraphEdge[], nodeId: string): number[] {
  const set = new Set<number>();
  for (const e of edges) {
    if (e.source === nodeId) e.shared_cases.forEach(c => set.add(c));
    if (e.target === nodeId) e.shared_cases.forEach(c => set.add(c));
  }
  return Array.from(set);
}

function getAdjacentAccused(edges: GraphEdge[], nodeId: string, nodes: GraphNode[]): GraphNode[] {
  const connected = new Set<string>();
  for (const e of edges) {
    if (e.source === nodeId && nodes.find(n => n.id === e.target)?.node_type === 'accused') connected.add(e.target);
    if (e.target === nodeId && nodes.find(n => n.id === e.source)?.node_type === 'accused') connected.add(e.source);
  }
  return nodes.filter(n => connected.has(n.id));
}

function getAdjacentCases(edges: GraphEdge[], nodeId: string, nodes: GraphNode[]): GraphNode[] {
  const connected = new Set<string>();
  for (const e of edges) {
    if (e.source === nodeId && nodes.find(n => n.id === e.target)?.node_type === 'case') connected.add(e.target);
    if (e.target === nodeId && nodes.find(n => n.id === e.source)?.node_type === 'case') connected.add(e.source);
  }
  return nodes.filter(n => connected.has(n.id));
}

export const NetworkPage: React.FC = () => {
  const { t } = useLanguage();
  const [search, setSearch] = useState('');
  const [searchMode, setSearchMode] = useState<'person' | 'case'>('person');
  const [loading, setLoading] = useState(false);
  const [graphData, setGraphData] = useState<{ nodes: GraphNode[]; edges: GraphEdge[] } | null>(null);
  const [error, setError] = useState('');
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [showAi, setShowAi] = useState(true);
  const [aiMsg, setAiMsg] = useState('');
  const [aiLoading, setAiLoading] = useState(false);
  const [aiHistory, setAiHistory] = useState<{ role: string; text: string }[]>([]);
  const [aiInput, setAiInput] = useState('');
  const [layoutMode, setLayoutMode] = useState('force-directed');
  const [showLegend, setShowLegend] = useState(true);
  const [metrics, setMetrics] = useState({ density: 0, largestClusterSize: 0, centralFigures: [] as string[], bridges: [] as string[] });
  const [networkConvs, setNetworkConvs] = useState<any[]>([]);
  const [activeConvId, setActiveConvId] = useState<string>('');

  const containerRef = useRef<HTMLDivElement>(null);
  const networkRef = useRef<any>(null);
  const aiEndRef = useRef<HTMLDivElement>(null);

  const aiNodes = graphData?.nodes || [];
  const aiEdges = graphData?.edges || [];

  useEffect(() => { aiEndRef.current?.scrollIntoView({ behavior: 'smooth' }); }, [aiHistory, aiMsg]);

  useEffect(() => {
    api.networkListConversations().then((convs: any[]) => {
      setNetworkConvs(convs || []);
      if (convs && convs.length > 0) {
        const latest = convs[0];
        setActiveConvId(latest.conversation_id);
        api.networkGetConversation(latest.conversation_id).then(conv => {
          if (conv && conv.messages) {
            setAiHistory(conv.messages.map((m: any) => ({ role: m.role, text: m.content_text })));
          }
        });
      }
    }).catch(() => {});
  }, []);

  useEffect(() => {
    if (!graphData || !containerRef.current) return;
    try {
      if (networkRef.current) { networkRef.current.destroy(); networkRef.current = null; }

      const nodes = new DataSet(graphData.nodes.map((n: GraphNode) => {
        const isAccused = n.node_type === 'accused';
        return {
          id: n.id,
          label: n.label,
          title: isAccused
            ? `Name: ${n.label}\nCases: ${n.cases}\nRisk: ${n.risk_tier || 'Unknown'}\nCrime: ${n.crime_type || 'Unknown'}`
            : `Case #${n.label.replace('Case #', '')}\nCrime: ${n.crime_type || 'Unknown'}\nAccused: ${n.cases}`,
          color: isAccused ? (tireColors[n.risk_tier || 'LOW'] || '#6C63FF') : (crimeColors[n.crime_type || ''] || '#6C63FF'),
          value: Math.max(n.cases * 4, 5),
          shape: isAccused ? 'dot' : 'square',
          size: isAccused ? Math.min(n.cases * 5 + 10, 50) : Math.min(n.cases * 8 + 20, 60),
          borderWidth: isAccused && n.risk_tier === 'HIGH' ? 3 : 2,
        };
      }));

      const edges = new DataSet(graphData.edges.map((e: GraphEdge) => {
        const isCaseCase = e.edge_type === 'case_case' || (graphData.nodes.find(n => n.id === e.source)?.node_type === 'case' && graphData.nodes.find(n => n.id === e.target)?.node_type === 'case');
        return {
          id: e.id, from: e.source, to: e.target,
          width: Math.min(e.weight * 2, 8),
          title: e.connection_basis || `${e.weight} shared case(s)`,
          color: { color: isCaseCase ? 'rgba(255,255,255,0.15)' : 'rgba(255,255,255,0.25)', hover: 'var(--primary)', highlight: 'var(--primary)' },
          label: isCaseCase ? (e.connection_basis || '') : '',
          font: { size: 10, color: 'var(--text-secondary)', strokeWidth: 2, strokeColor: 'var(--bg-primary)' },
          dashes: isCaseCase,
          smooth: { enabled: true, type: 'continuous', roundness: 0.3 },
        };
      }));

      const opts: any = {
        nodes: { font: { color: 'var(--text-primary)', size: 12 }, borderWidth: 2 },
        edges: { font: { align: 'middle' } },
        layout: layoutMode === 'hierarchical' ? { hierarchical: { direction: 'UD', sortMethod: 'directed' } } : {},
        physics: layoutMode === 'hierarchical'
          ? { solver: 'hierarchicalRepulsion', hierarchicalRepulsion: { nodeDistance: 120 } }
          : { solver: 'forceAtlas2Based', forceAtlas2Based: { gravitationalConstant: -40, centralGravity: 0.005, springLength: 120, springConstant: 0.08 } },
        interaction: { hover: true, tooltipDelay: 200 },
      };
      const container = containerRef.current;
      const visNetwork = new VisNetwork(container, { nodes, edges }, opts);

      // Store original colors for highlight reset
      const originalColors: Record<string, string> = {};
      nodes.forEach((n: any) => { originalColors[n.id] = n.color; });

      visNetwork.on('click', (params: any) => {
        if (params.nodes.length > 0) {
          const clickedId = params.nodes[0];
          const node = graphData.nodes.find((n: GraphNode) => n.id === clickedId);
          if (node) {
            setSelectedNode(node);
            const isAcc = node.node_type === 'accused';
            setAiMsg(isAcc
              ? `${node.label}: ${node.cases} cases, ${node.risk_tier} risk, ${node.crime_type || 'Unknown'} crime.`
              : `${node.label}: ${node.crime_type || 'Unknown'}, ${node.cases} accused.`);
            // Dim non-connected nodes via DataSet update
            const connected = new Set([clickedId]);
            graphData.edges.forEach(e => {
              if (e.source === clickedId) connected.add(e.target);
              if (e.target === clickedId) connected.add(e.source);
            });
            const updates: any[] = [];
            nodes.forEach((n: any) => {
              if (connected.has(n.id)) {
                updates.push({ id: n.id, color: originalColors[n.id], opacity: 1 });
              } else {
                updates.push({ id: n.id, color: originalColors[n.id], opacity: 0.2 });
              }
            });
            nodes.update(updates);
            edges.forEach((e: any) => { e.hidden = false; });
          }
        } else {
          setSelectedNode(null);
          const updates: any[] = [];
          nodes.forEach((n: any) => { updates.push({ id: n.id, color: originalColors[n.id], opacity: 1 }); });
          nodes.update(updates);
        }
      });

      networkRef.current = visNetwork;
    } catch (e) { console.error('Graph init error:', e); }
    return () => { if (networkRef.current) { networkRef.current.destroy(); networkRef.current = null; } };
  }, [graphData, layoutMode, t]);

  const handleSearch = useCallback(async () => {
    if (!search.trim()) return;
    setLoading(true); setError(''); setSelectedNode(null);
    setAiMsg(t('Loading network...', 'ನೆಟ್‌ವರ್ಕ್ ಲೋಡ್ ಆಗುತ್ತಿದೆ...'));
    try {
      const data = await api.getNetwork(search, searchMode);
      if (data.error) { setError(data.error); setLoading(false); return; }
      setGraphData(data);
      setMetrics(computeMetrics(data.nodes, data.edges));
      setAiMsg(t('Network loaded. Click a node to inspect, or ask me a question.', 'ನೆಟ್‌ವರ್ಕ್ ಲೋಡ್ ಆಗಿದೆ. ನೋಡ್ ಕ್ಲಿಕ್ ಮಾಡಿ ಅಥವಾ ಪ್ರಶ್ನೆ ಕೇಳಿ.'));
    } catch {
      setError(t('Failed to load network.', 'ನೆಟ್‌ವರ್ಕ್ ಲೋಡ್ ಮಾಡಲು ವಿಫಲವಾಗಿದೆ.'));
      setAiMsg(t('Error loading network.', 'ನೆಟ್‌ವರ್ಕ್ ಲೋಡ್ ಮಾಡುವಲ್ಲಿ ದೋಷ.'));
    }
    setLoading(false);
  }, [search, searchMode, t]);

  const handleAiQuery = useCallback(async (overrideMsg?: string) => {
    const q = overrideMsg ?? aiInput;
    if (!q.trim()) return;
    setAiInput('');
    const userMsg = { role: 'user', text: q } as const;
    setAiHistory(prev => [...prev, userMsg]);
    setAiLoading(true);
    const g = graphData ?? { nodes: [], edges: [] };
    try {
      const res = await api.networkAiQuery(q, g.nodes, g.edges, activeConvId);
      if (res.conversation_id) setActiveConvId(res.conversation_id);
      if (res.messages) {
        setAiHistory(res.messages.map((m: any) => ({ role: m.role, text: m.content_text })));
      }
      setAiMsg(res.answer || res.summary || 'No analysis available.');
      api.networkListConversations().then(convs => setNetworkConvs(convs || [])).catch(() => {});
    } catch {
      const fallback = generateLocalAnswer(q, g);
      setAiHistory(prev => [...prev, { role: 'ai', text: fallback }]);
      setAiMsg(fallback);
    }
    setAiLoading(false);
  }, [aiInput, graphData, activeConvId]);

  const generateLocalAnswer = (question: string, data: { nodes: GraphNode[]; edges: GraphEdge[] }): string => {
    const q = question.toLowerCase();
    const { nodes, edges } = data;
    const accused = nodes.filter(n => n.node_type === 'accused');
    const cases = nodes.filter(n => n.node_type === 'case');
    const highRisk = accused.filter(n => n.risk_tier === 'HIGH' || n.risk_tier === 'ELEVATED');
    const degree: Record<string, number> = {};
    edges.forEach(e => { degree[e.source] = (degree[e.source] || 0) + 1; degree[e.target] = (degree[e.target] || 0) + 1; });
    const topCentral = Object.entries(degree).sort((a, b) => b[1] - a[1]).slice(0, 3)
      .map(([id]) => nodes.find(n => n.id === id)?.label || id);

    if ((q.includes('case') && q.includes('101')) || q.includes('what cases') || q.includes('connected to') || (q.includes('which') && q.includes('case'))) {
      const nameMatch = accused.find(n => n.label.toLowerCase().includes(q.replace('which cases is ', '').replace('what cases is ', '').replace('?', '').trim()));
      if (nameMatch) {
        const caseEdges = edges.filter(e => e.source === nameMatch.id || e.target === nameMatch.id);
        const caseIds = new Set<number>();
        caseEdges.forEach(e => e.shared_cases.forEach(c => caseIds.add(c)));
        const caseNodes = cases.filter(c => Array.from(caseIds).some(id => c.label.includes(String(id))));
        return `${nameMatch.label} is linked to ${caseNodes.length} case(s): ${caseNodes.map(c => `${c.label} (${c.crime_type})`).join(', ') || 'none'}.`;
      }
    }
    if (q.includes('who is') || q.includes('accused in') || q.includes('who are')) {
      const caseMatch = cases.find(n => q.includes(n.label.toLowerCase().replace(' ', '')));
      if (caseMatch) {
        const connected = getAdjacentAccused(edges, caseMatch.id, nodes);
        return `${caseMatch.label} (${caseMatch.crime_type}) — ${connected.length} accused: ${connected.map(n => n.label).join(', ') || 'none'}.`;
      }
    }
    if (q.includes('how are') && (q.includes('linked') || q.includes('connected') || q.includes('related'))) {
      const caseCaseEdges = edges.filter(e => e.edge_type === 'case_case');
      if (caseCaseEdges.length === 0) return 'No case-to-case connections in this network.';
      return caseCaseEdges.slice(0, 6).map(e => {
        const src = nodes.find(n => n.id === e.source)?.label;
        const tgt = nodes.find(n => n.id === e.target)?.label;
        return `${src} ↔ ${tgt}: ${e.connection_basis}`;
      }).join('\n');
    }
    if (q.includes('highest priority') || q.includes('most dangerous') || q.includes('risk')) {
      if (highRisk.length) return `High-priority accused: ${highRisk.map(n => `${n.label} (${n.risk_tier}, ${n.cases} cases)`).join('; ')}.`;
      return 'No high-risk accused in this network.';
    }
    if (q.includes('central') || q.includes('hub') || q.includes('key')) {
      return `Most central: ${topCentral.join(', ')}. They bridge the most connections.`;
    }
    if (q.includes('crime') || q.includes('type')) {
      const types = Array.from(new Set(nodes.map(n => n.crime_type).filter(Boolean)));
      return `Crime types: ${types.join(', ')}.`;
    }
    return `Network: ${cases.length} cases, ${accused.length} accused, ${edges.length} connections. ${highRisk.length ? `High-risk: ${highRisk.length}. ` : ''}Central: ${topCentral.join(', ')}.`;
  };

  const expandFromPerson = (name: string) => {
    setSearch(name);
    setSearchMode('person');
    setTimeout(() => handleSearch(), 0);
  };

  const switchConversation = useCallback(async (convId: string) => {
    setActiveConvId(convId);
    setAiLoading(true);
    try {
      const conv = await api.networkGetConversation(convId);
      if (conv && conv.messages) {
        setAiHistory(conv.messages.map((m: any) => ({ role: m.role, text: m.content_text })));
      }
    } catch { setAiHistory([]); }
    setAiLoading(false);
  }, []);

  const handleNewConversation = useCallback(async () => {
    try {
      const conv = await api.networkCreateConversation();
      if (conv && conv.conversation_id) {
        setActiveConvId(conv.conversation_id);
        setAiHistory([]);
        setAiMsg('');
        const convs = await api.networkListConversations();
        setNetworkConvs(convs || []);
      }
    } catch {}
  }, []);

  const handleDeleteConversation = useCallback(async (convId: string, e: React.MouseEvent) => {
    e.stopPropagation();
    try {
      await api.networkDeleteConversation(convId);
      const convs = await api.networkListConversations();
      setNetworkConvs(convs || []);
      if (activeConvId === convId) {
        if (convs && convs.length > 0) {
          switchConversation(convs[0].conversation_id);
        } else {
          setActiveConvId('');
          setAiHistory([]);
          setAiMsg('');
        }
      }
    } catch {}
  }, [activeConvId, switchConversation]);

  const quickQuestions = [
    { label: t('Who is highest priority?', 'ಅತ್ಯಧಿಕ ಆದ್ಯತೆ ಯಾರು?'), msg: 'Who is the highest priority?' },
    { label: t('How are cases linked?', 'ಪ್ರಕರಣಗಳು ಹೇಗೆ ಲಿಂಕ್ ಆಗಿವೆ?'), msg: 'How are cases linked?' },
    { label: t('Key central figures?', 'ಪ್ರಮುಖ ಕೇಂದ್ರ ವ್ಯಕ್ತಿಗಳು?'), msg: 'Who are the key central figures?' },
    { label: t('Crime types?', 'ಅಪರಾಧ ಪ್ರಕಾರಗಳು?'), msg: 'What crime types are in this network?' },
  ];

  return (
    <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
      <div style={{ flex: '1 1 400px', minWidth: 0 }}>
        <div className="page-header">
          <h1>{t('Network Intelligence', 'ನೆಟ್‌ವರ್ಕ್ ಇಂಟೆಲಿಜೆನ್ಸ್')}</h1>
          <p>{t('Bipartite graph: cases (squares) and accused (circles)', 'ದ್ವಿಪಕ್ಷೀಯ ಗ್ರಾಫ್: ಪ್ರಕರಣಗಳು (ಚೌಕಗಳು) ಮತ್ತು ಆರೋಪಿಗಳು (ವೃತ್ತಗಳು)')}</p>
        </div>

        <div className="card" style={{ marginBottom: 16 }}>
          <div style={{ display: 'flex', gap: 12 }}>
            <div className="input-group" style={{ flex: 1 }}>
              <Search className="input-icon" size={18} />
              <input className="input"
                placeholder={searchMode === 'case' ? t('Search by case number...', 'ಪ್ರಕರಣ ಸಂಖ್ಯೆಯಿಂದ ಹುಡುಕಿ...') : t('Search by accused name...', 'ಆರೋಪಿಯ ಹೆಸರಿನಿಂದ ಹುಡುಕಿ...')}
                value={search} onChange={e => setSearch(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleSearch()} />
            </div>
            <div style={{ display: 'flex', gap: 4, alignItems: 'center', flexShrink: 0 }}>
              <button className={`btn btn-sm ${searchMode === 'person' ? 'btn-primary' : 'btn-ghost'}`}
                onClick={() => setSearchMode('person')}>{t('Person', 'ವ್ಯಕ್ತಿ')}</button>
              <button className={`btn btn-sm ${searchMode === 'case' ? 'btn-primary' : 'btn-ghost'}`}
                onClick={() => setSearchMode('case')}>{t('Case', 'ಪ್ರಕರಣ')}</button>
            </div>
            <button className="btn btn-primary" onClick={handleSearch} disabled={loading}>{t('Analyze', 'ವಿಶ್ಲೇಷಿಸಿ')}</button>
          </div>
        </div>

        <div className="card" style={{ marginBottom: 16, padding: 12 }}>
          <div className="flex gap-3" style={{ flexWrap: 'wrap', alignItems: 'center' }}>
            <span className="text-xs text-muted">{t('Layout', 'ವಿನ್ಯಾಸ')}:</span>
            <select className="input" style={{ width: 'auto', fontSize: 12, padding: '4px 8px' }} value={layoutMode} onChange={e => setLayoutMode(e.target.value)}>
              <option value="force-directed">{t('Force-directed', 'ಬಲ-ನಿರ್ದೇಶಿತ')}</option>
              <option value="hierarchical">{t('Hierarchical', 'ಶ್ರೇಣೀಬದ್ಧ')}</option>
            </select>
            <button className="btn btn-ghost btn-sm" onClick={() => networkRef.current?.fit()}>{t('Reset View', 'ವೀಕ್ಷಣೆ ಮರುಹೊಂದಿಸಿ')}</button>
            <button className="btn btn-ghost btn-sm" onClick={() => setShowLegend(!showLegend)}>
              <Info size={14} /> {t('Legend', 'ದಂತಕಥೆ')}
            </button>
          </div>
          {showLegend && (
            <div style={{ marginTop: 8, display: 'flex', gap: 16, flexWrap: 'wrap', fontSize: 12, color: 'var(--text-secondary)' }}>
              <span><strong>{t('Nodes', 'ನೋಡ್‌ಗಳು')}:</strong></span>
              <span>■ {t('Case (square)', 'ಪ್ರಕರಣ (ಚೌಕ)')}</span>
              <span>● {t('Accused (circle)', 'ಆರೋಪಿ (ವೃತ್ತ)')}</span>
              <span style={{ borderLeft: '2px solid var(--text-secondary)', paddingLeft: 8 }}><strong>{t('Accused risk', 'ಆರೋಪಿ ಅಪಾಯ')}:</strong></span>
              <span><span style={{ color: '#EF4444' }}>●</span> HIGH</span>
              <span><span style={{ color: '#F59E0B' }}>●</span> ELEVATED</span>
              <span><span style={{ color: '#3B82F6' }}>●</span> MODERATE</span>
              <span><span style={{ color: '#22C55E' }}>●</span> LOW</span>
              <span style={{ borderLeft: '2px solid var(--text-secondary)', paddingLeft: 8 }}><strong>{t('Case by crime', 'ಪ್ರಕರಣ-ಅಪರಾಧ')}:</strong></span>
              {Object.entries(crimeColors).map(([crime, color]) => (
                <span key={crime}><span style={{ color }}>■</span> {crime}</span>
              ))}
              <span style={{ borderLeft: '2px solid var(--text-secondary)', paddingLeft: 8 }}><strong>{t('Edges', 'ಅಂಚುಗಳು')}:</strong></span>
              <span>─ {t('accused in case', 'ಆರೋಪಿ-ಪ್ರಕರಣ')}</span>
              <span>- - - {t('shared accused (case→case)', 'ಹಂಚಿಕೆಯ ಆರೋಪಿ (ಪ್ರಕರಣ→ಪ್ರಕರಣ)')}</span>
            </div>
          )}
        </div>

        {loading && <div className="skeleton" style={{ width: '100%', height: 400, borderRadius: 12 }} />}
        {error && <div className="card" style={{ borderLeft: '4px solid var(--danger)' }}><p style={{ color: 'var(--danger)' }}>{error}</p></div>}

        {graphData && (
          <div className="grid-2" style={{ marginBottom: 24 }}>
            <div className="card" style={{ gridColumn: '1 / -1' }}>
              <div ref={containerRef} className="network-container" style={{ height: 500, background: 'var(--bg-secondary)', borderRadius: 8 }} />
            </div>
          </div>
        )}

        {graphData && (
          <>
            <div className="card">
              <div className="card-header flex items-center gap-2"><LucideNetwork size={16} /> {t('Network Metrics', 'ನೆಟ್‌ವರ್ಕ್ ಮೆಟ್ರಿಕ್‌ಗಳು')}</div>
              <div className="grid-4" style={{ gap: 16 }}>
                <div className="card" style={{ padding: 16, textAlign: 'center' }}>
                  <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--primary)' }}>{metrics.density}</div>
                  <div className="text-xs text-muted">{t('Network Density', 'ನೆಟ್‌ವರ್ಕ್ ಸಾಂದ್ರತೆ')}</div>
                </div>
                <div className="card" style={{ padding: 16, textAlign: 'center' }}>
                  <div style={{ fontSize: 24, fontWeight: 700, color: 'var(--warning)' }}>{metrics.largestClusterSize}</div>
                  <div className="text-xs text-muted">{t('Largest Cluster (nodes)', 'ದೊಡ್ಡ ಸಮೂಹ (ನೋಡ್‌ಗಳು)')}</div>
                </div>
                <div className="card" style={{ padding: 16, textAlign: 'center' }}>
                  <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--danger)' }}>{metrics.centralFigures.join(', ') || 'N/A'}</div>
                  <div className="text-xs text-muted">{t('Central Figures', 'ಕೇಂದ್ರ ವ್ಯಕ್ತಿಗಳು')}</div>
                </div>
                <div className="card" style={{ padding: 16, textAlign: 'center' }}>
                  <div style={{ fontSize: 14, fontWeight: 600, color: 'var(--blue)' }}>{metrics.bridges.join(', ') || 'N/A'}</div>
                  <div className="text-xs text-muted">{t('Bridges', 'ಸೇತುವೆಗಳು')}</div>
                </div>
              </div>
            </div>

            {selectedNode && selectedNode.node_type === 'accused' && (
              <div className="card" style={{ marginTop: 16 }}>
                <div className="card-header flex justify-between items-center">
                  <h3><span className="flex items-center gap-2"><span style={{ display: 'inline-block', width: 12, height: 12, borderRadius: '50%', background: tireColors[selectedNode.risk_tier || 'LOW'] }} /> {selectedNode.label}</span></h3>
                  <div className="flex gap-2">
                    <button className="btn btn-primary btn-sm" onClick={() => expandFromPerson(selectedNode.label)}>
                      <Target size={14} /> {t('Expand Network', 'ನೆಟ್‌ವರ್ಕ್ ವಿಸ್ತರಿಸಿ')}
                    </button>
                    <button className="btn btn-ghost btn-icon" onClick={() => setSelectedNode(null)}><X size={18} /></button>
                  </div>
                </div>
                <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
                  <div style={{ flex: 1, minWidth: 200 }}>
                    <div className="text-sm"><strong>{t('Name', 'ಹೆಸರು')}:</strong> {selectedNode.label}</div>
                    <div className="text-sm"><strong>{t('Risk Tier', 'ಅಪಾಯದ ಮಟ್ಟ')}:</strong> <span className={`badge ${(selectedNode.risk_tier || '').toLowerCase() === 'high' ? 'badge-high' : (selectedNode.risk_tier || '').toLowerCase() === 'elevated' ? 'badge-elevated' : (selectedNode.risk_tier || '').toLowerCase() === 'moderate' ? 'badge-moderate' : 'badge-low'}`}>{selectedNode.risk_tier || 'Unknown'}</span></div>
                    <div className="text-sm"><strong>{t('Total Cases', 'ಒಟ್ಟು ಪ್ರಕರಣಗಳು')}:</strong> {selectedNode.cases}</div>
                    <div className="text-sm"><strong>{t('Primary Crime', 'ಪ್ರಾಥಮಿಕ ಅಪರಾಧ')}:</strong> {selectedNode.crime_type || 'Unknown'}</div>
                  </div>
                  <div style={{ flex: 2, minWidth: 200 }}>
                    <div className="text-sm"><strong>{t('Connected Cases', 'ಸಂಪರ್ಕಿತ ಪ್ರಕರಣಗಳು')}:</strong></div>
                    <ul style={{ margin: '4px 0 0', paddingLeft: 20, fontSize: 13 }}>
                      {(() => {
                        const caseIds = getConnectedCaseIds(aiEdges, selectedNode.id);
                        const caseNodes = aiNodes.filter(n => n.node_type === 'case' && caseIds.some(c => n.label.includes(String(c))));
                        return caseNodes.length > 0
                          ? caseNodes.map(cn => <li key={cn.id}><button className="btn btn-ghost btn-sm" style={{ padding: '2px 4px', fontSize: 13 }} onClick={() => setSelectedNode(cn)}>{cn.label} — {cn.crime_type}</button></li>)
                          : [<li key="none" style={{ color: 'var(--text-secondary)' }}>No cases found</li>];
                      })()}
                    </ul>
                    <div style={{ marginTop: 8, display: 'flex', gap: 8 }}>
                      <button className="btn btn-secondary btn-sm" onClick={() => window.location.hash = `/offender?name=${encodeURIComponent(selectedNode.label)}`}>
                        <ExternalLink size={14} /> {t('View Dossier', 'ಡಾಸಿಯರ್ ವೀಕ್ಷಿಸಿ')}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {selectedNode && selectedNode.node_type === 'case' && (
              <div className="card" style={{ marginTop: 16 }}>
                <div className="card-header flex justify-between items-center">
                  <h3><span className="flex items-center gap-2"><span style={{ display: 'inline-block', width: 12, height: 12, background: crimeColors[selectedNode.crime_type || ''] || '#6C63FF' }} /> {selectedNode.label}</span></h3>
                  <button className="btn btn-ghost btn-icon" onClick={() => setSelectedNode(null)}><X size={18} /></button>
                </div>
                <div style={{ display: 'flex', gap: 24, flexWrap: 'wrap' }}>
                  <div style={{ flex: 1, minWidth: 200 }}>
                    <div className="text-sm"><strong>{t('Case', 'ಪ್ರಕರಣ')}:</strong> {selectedNode.label}</div>
                    <div className="text-sm"><strong>{t('Crime Type', 'ಅಪರಾಧ ಪ್ರಕಾರ')}:</strong> {selectedNode.crime_type || 'Unknown'}</div>
                    <div className="text-sm"><strong>{t('Accused Count', 'ಆರೋಪಿಗಳ ಸಂಖ್ಯೆ')}:</strong> {selectedNode.cases}</div>
                  </div>
                  <div style={{ flex: 2, minWidth: 200 }}>
                    <div className="text-sm"><strong>{t('Accused in this case', 'ಈ ಪ್ರಕರಣದ ಆರೋಪಿಗಳು')}:</strong></div>
                    <ul style={{ margin: '4px 0 0', paddingLeft: 20, fontSize: 13 }}>
                      {(() => {
                        const connected = getAdjacentAccused(aiEdges, selectedNode.id, aiNodes);
                        return connected.length > 0
                          ? connected.map(n => <li key={n.id}><button className="btn btn-ghost btn-sm" style={{ padding: '2px 4px', fontSize: 13 }} onClick={() => setSelectedNode(n)}>{n.label} <span className="badge badge-low" style={{ fontSize: 10 }}>{n.risk_tier}</span></button></li>)
                          : [<li key="none" style={{ color: 'var(--text-secondary)' }}>No accused</li>];
                      })()}
                    </ul>
                  </div>
                </div>
                <div style={{ marginTop: 8 }}>
                  <button className="btn btn-ghost btn-sm" onClick={() => {
                    const caseEdges = aiEdges.filter(e => e.source === selectedNode.id || e.target === selectedNode.id);
                    const sharedCases = getAdjacentCases(aiEdges, selectedNode.id, aiNodes);
                    const connections = sharedCases.map(sc => {
                      const ce = aiEdges.find(e => (e.source === selectedNode.id && e.target === sc.id) || (e.target === selectedNode.id && e.source === sc.id));
                      return `${sc.label}: ${ce?.connection_basis || 'shared accused'}`;
                    }).join('\n') || 'none';
                    setAiHistory(prev => [...prev, { role: 'user', text: `Show connections for ${selectedNode.label}` }, { role: 'ai', text: `${selectedNode.label} has ${caseEdges.length} edge(s). Shared accused with: ${connections}.` }]);
                    setAiMsg(`Connections for ${selectedNode.label} loaded.`);
                  }}>
                    {t('Analyze connections', 'ಸಂಪರ್ಕಗಳನ್ನು ವಿಶ್ಲೇಷಿಸಿ')}
                  </button>
                </div>
              </div>
            )}
          </>
        )}
      </div>

      <div style={{ width: 300, minWidth: 260, flexShrink: 0, display: 'flex', flexDirection: 'column', gap: 12 }}>
        <div className="card" style={{ position: 'sticky', top: 32, height: 'calc(100vh - 100px)', display: 'flex', flexDirection: 'column' }}>
          <div className="card-header flex justify-between items-center" style={{ flexShrink: 0 }}>
            <span className="flex items-center gap-2"><Bot size={20} /> {t('NetworkAI', 'ನೆಟ್‌ವರ್ಕ್-ಎಐ')}</span>
            <button className="btn btn-ghost btn-icon" onClick={() => setShowAi(!showAi)}>
              {showAi ? <ChevronDown size={18} /> : <ChevronUp size={18} />}
            </button>
          </div>
          {showAi && (
            <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden', minHeight: 0 }}>
              <div style={{ flexShrink: 0, padding: '0 0 6px', borderBottom: '1px solid var(--border)', marginBottom: 4 }}>
                <div style={{ display: 'flex', gap: 4, alignItems: 'center', marginBottom: 4 }}>
                  <select className="input" style={{ flex: 1, fontSize: 12, padding: '4px 6px' }}
                    value={activeConvId} onChange={e => e.target.value && switchConversation(e.target.value)}>
                    {networkConvs.length === 0 && <option value="">{t('No conversations', 'ಯಾವುದೇ ಸಂವಾದಗಳಿಲ್ಲ')}</option>}
                    {networkConvs.map(conv => (
                      <option key={conv.conversation_id} value={conv.conversation_id}>
                        {conv.title?.substring(0, 40) || 'Network Chat'} ({conv.message_count})
                      </option>
                    ))}
                  </select>
                  <button className="btn btn-ghost btn-sm" style={{ padding: '4px 6px' }}
                    onClick={handleNewConversation} title={t('New Chat', 'ಹೊಸ ಸಂವಾದ')}>
                    <Plus size={14} />
                  </button>
                  {activeConvId && (
                    <button className="btn btn-ghost btn-sm" style={{ padding: '4px 6px', color: 'var(--danger)' }}
                      onClick={e => handleDeleteConversation(activeConvId, e)} title={t('Delete', 'ಅಳಿಸಿ')}>
                      <Trash2 size={14} />
                    </button>
                  )}
                </div>
              </div>
              <div style={{ flex: 1, overflowY: 'auto', padding: '8px 0', display: 'flex', flexDirection: 'column', gap: 8, minHeight: 0 }}>
                {aiHistory.length === 0 && (
                  <div style={{ padding: 12, background: 'var(--bg-hover)', borderRadius: 8, fontSize: 13, color: 'var(--text-secondary)' }}>
                    {aiMsg || t('I am NetworkAI. Search for a person to begin, then click nodes or ask questions.', 'ನಾನು ನೆಟ್‌ವರ್ಕ್-ಎಐ. ವ್ಯಕ್ತಿಯನ್ನು ಹುಡುಕಿ, ನಂತರ ನೋಡ್ ಕ್ಲಿಕ್ ಮಾಡಿ ಅಥವಾ ಪ್ರಶ್ನೆ ಕೇಳಿ.')}
                  </div>
                )}
                {aiHistory.map((h, i) => (
                  <div key={i} style={{ padding: '6px 12', background: h.role === 'user' ? 'var(--bg-secondary)' : 'var(--bg-hover)', borderRadius: 8, fontSize: 13, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                    {h.role === 'user' && <span style={{ fontWeight: 600, fontSize: 11, color: 'var(--primary)', display: 'block', marginBottom: 2 }}>You</span>}
                    {h.text}
                  </div>
                ))}
                {aiLoading && <div style={{ padding: 12, fontSize: 13, color: 'var(--text-secondary)' }}><Loader2 size={14} className="animate-spin" /> Analyzing...</div>}
                <div ref={aiEndRef} />
              </div>

              <div style={{ flexShrink: 0, borderTop: '1px solid var(--border)', padding: '6px 0' }}>
                {!graphData && (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 4, padding: '0 0 6px' }}>
                    {quickQuestions.map((q, i) => (
                      <button key={i} className="btn btn-ghost btn-sm" style={{ justifyContent: 'flex-start', fontSize: 12, padding: '4px 8px' }}
                        onClick={() => handleAiQuery(q.msg)}>
                        {q.label}
                      </button>
                    ))}
                  </div>
                )}
                <div style={{ display: 'flex', gap: 6, padding: '0 4px' }}>
                  <input className="input" style={{ flex: 1, fontSize: 13, padding: '6px 8px', minWidth: 0 }}
                    placeholder={graphData ? t('Ask about network...', 'ನೆಟ್‌ವರ್ಕ್ ಬಗ್ಗೆ ಕೇಳಿ...') : t('Type a question...', 'ಪ್ರಶ್ನೆಯನ್ನು ಟೈಪ್ ಮಾಡಿ...')}
                    value={aiInput} onChange={e => setAiInput(e.target.value)}
                    onKeyDown={e => e.key === 'Enter' && handleAiQuery()} />
                  <button className="btn btn-primary btn-sm" onClick={() => handleAiQuery()} disabled={aiLoading || !aiInput.trim()}>
                    <Send size={16} />
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};