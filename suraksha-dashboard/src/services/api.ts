import { LoginResponse, ChatMessage, OffenderProfile, TrendDataPoint, HotspotCluster, GraphNode, GraphEdge, PriorityScore, ForecastDataPoint } from '../types';

const MOCK_TOKEN = 'mock_jwt_INV001_1';

const delay = (ms: number) => new Promise(r => setTimeout(r, ms));

const users: Record<string, LoginResponse> = {
  INV001: { token: MOCK_TOKEN, user: { user_id: 'INV001', kgid: 'INV001', first_name: 'Ravi Kumar', role_id: 1, role_name: 'Investigator', unit_id: 1, district_id: 1 } },
  ANL001: { token: MOCK_TOKEN, user: { user_id: 'ANL001', kgid: 'ANL001', first_name: 'Priya Sharma', role_id: 2, role_name: 'Analyst', district_id: 18 } },
  SUP001: { token: MOCK_TOKEN, user: { user_id: 'SUP001', kgid: 'SUP001', first_name: 'Amit Singh', role_id: 3, role_name: 'Supervisor', unit_id: 1, district_id: 1 } },
  POL001: { token: MOCK_TOKEN, user: { user_id: 'POL001', kgid: 'POL001', first_name: 'Dr. Meena Rao', role_id: 4, role_name: 'Policymaker', district_id: 18 } },
  ADM001: { token: MOCK_TOKEN, user: { user_id: 'ADM001', kgid: 'ADM001', first_name: 'Vikram P', role_id: 5, role_name: 'System Administrator' } },
};

const districts = [
  'Bengaluru Urban', 'Bengaluru Rural', 'Mysuru', 'Hubballi-Dharwad', 'Mangaluru',
  'Belagavi', 'Kalaburagi', 'Shivamogga', 'Tumakuru', 'Davangere',
];

const crimeTypes = ['Theft', 'Robbery', 'Assault', 'Burglary', 'Cheating', 'Kidnapping', 'Murder', 'Rioting', 'Cyber Crime', 'Drug Offense'];

const accusedNames = [
  'Ravi Kumar', 'Suresh P', 'Rajesh K', 'Manoj R', 'Venkatesh G',
  'Prakash M', 'Kumar S', 'Anil K', 'Sunil D', 'Gopal R',
  'Mahesh N', 'Dinesh B', 'Satish H', 'Vinod T', 'Harish M',
];

function seededRandom(seed: number): number {
  const x = Math.sin(seed) * 10000;
  return x - Math.floor(x);
}

export const api = {
  async login(kgid: string, _password: string): Promise<LoginResponse> {
    await delay(500);
    if (users[kgid]) return users[kgid];
    throw new Error('Invalid credentials');
  },

  async chatQuery(message: string, conversationId?: string): Promise<ChatMessage> {
    await delay(800);
    const lowercase = message.toLowerCase();

    let response: { text: string; kn: string; sql?: string; chart?: string; followups: string[]; evidence?: { label: string; count: number; table: string }[] };

    if (lowercase.includes('theft') || lowercase.includes('steal')) {
      response = {
        text: 'Found 2,847 theft cases in Bangalore for the current year. This represents a 12.4% increase compared to the same period last year. The areas most affected are Whitefield (312 cases), Koramangala (289 cases), and Indiranagar (245 cases).',
        kn: 'ಪ್ರಸಕ್ತ ವರ್ಷದಲ್ಲಿ ಬೆಂಗಳೂರಿನಲ್ಲಿ 2,847 ಕಳ್ಳತನ ಪ್ರಕರಣಗಳು ಪತ್ತೆಯಾಗಿವೆ. ಹಿಂದಿನ ವರ್ಷಕ್ಕೆ ಹೋಲಿಸಿದರೆ ಇದು ಶೇಕಡ 12.4 ರಷ್ಟು ಹೆಚ್ಚಳವಾಗಿದೆ.',
        sql: "SELECT COUNT(*) FROM CaseMaster cm JOIN Unit u ON cm.PoliceStationID = u.UnitID JOIN District d ON u.DistrictID = d.DistrictID WHERE d.DistrictName LIKE '%Bangalore%' AND YEAR(cm.CrimeRegisteredDate) = YEAR(CURRENT_DATE) AND cm.CrimeMinorHeadID IN (SELECT CrimeSubHeadID FROM CrimeSubHead WHERE CrimeHeadName LIKE '%Theft%')",
        chart: 'bar_chart',
        followups: ['Which police station has the most?', 'Show on map', 'Compare with last year'],
        evidence: [{ label: 'CaseMaster records', count: 2847, table: 'CaseMaster' }],
      };
    } else if (lowercase.includes('murder') || lowercase.includes('homicide') || lowercase.includes('death')) {
      response = {
        text: '42 murder cases have been registered in Bangalore Urban district this year. Of these, 28 (66.7%) have been solved. The clearance rate is above the national average of 62%.',
        kn: 'ಈ ವರ್ಷ ಬೆಂಗಳೂರು ನಗರ ಜಿಲ್ಲೆಯಲ್ಲಿ 42 ನರಹತ್ಯೆ ಪ್ರಕರಣಗಳು ದಾಖಲಾಗಿವೆ. ಇವುಗಳಲ್ಲಿ 28 (66.7%) ಪ್ರಕರಣಗಳನ್ನು ಭೇದಿಸಲಾಗಿದೆ.',
        chart: 'trend_chart',
        followups: ['Show by month', 'Compare with last year', 'Which weapon type is common?'],
        evidence: [{ label: 'CaseMaster records', count: 42, table: 'CaseMaster' }],
      };
    } else if (lowercase.includes('traffic')) {
      response = {
        text: 'Traffic violations in Bangalore have increased by 8.3% this year. A total of 45,231 challans were issued. The highest number of violations are for signal jumping (12,847) and wrong-side driving (8,234).',
        kn: 'ಬೆಂಗಳೂರಿನಲ್ಲಿ ಸಂಚಾರ ಉಲ್ಲಂಘನೆಗಳು ಶೇಕಡ 8.3 ರಷ್ಟು ಹೆಚ್ಚಾಗಿವೆ. ಒಟ್ಟು 45,231 ಚಾಲನ್‌ಗಳನ್ನು ನೀಡಲಾಗಿದೆ.',
        followups: ['Show top 5 violation spots', 'Monthly trend', 'Revenue collected'],
        evidence: [{ label: 'TrafficViolation records', count: 45231, table: 'TrafficViolation' }],
      };
    } else if (lowercase.includes('cyber')) {
      response = {
        text: '2,134 cyber crime cases were reported in Karnataka this year. The most common types are phishing (834), online fraud (612), and identity theft (388). Bengaluru Urban accounts for 58% of all cases.',
        kn: 'ಈ ವರ್ಷ ಕರ್ನಾಟಕದಲ್ಲಿ 2,134 ಸೈಬರ್ ಅಪರಾಧ ಪ್ರಕರಣಗಳು ವರದಿಯಾಗಿವೆ. ಸಾಮಾನ್ಯ ವಿಧಗಳೆಂದರೆ ಫಿಶಿಂಗ್ (834), ಆನ್‌ಲೈನ್ ವಂಚನೆ (612) ಮತ್ತು ಗುರುತಿನ ಕಳ್ಳತನ (388).',
        chart: 'pie_chart',
        followups: ['Show by district', 'Top cyber crime hotspots', 'Recovery rate'],
        evidence: [{ label: 'CyberCrime records', count: 2134, table: 'CyberCrime' }],
      };
    } else if (lowercase.includes('history') || lowercase.includes('cases') || lowercase.includes('status')) {
      response = {
        text: 'There are 156 active cases currently under investigation. Case clearance rate is 71.2%. Average investigation time is 45 days for non-cognizable and 72 days for cognizable offenses.',
        kn: 'ಪ್ರಸ್ತುತ 156 ಸಕ್ರಿಯ ಪ್ರಕರಣಗಳು ತನಿಖೆಯಲ್ಲಿವೆ. ಪ್ರಕರಣ ಭೇದನ ದರ ಶೇಕಡ 71.2 ರಷ್ಟಿದೆ.',
        followups: ['Show pending cases', 'Show by officer', 'Overdue cases'],
        evidence: [{ label: 'CaseMaster records', count: 156, table: 'CaseMaster' }],
      };
    } else if (lowercase.includes('forecast') || lowercase.includes('predict') || lowercase.includes('future')) {
      response = {
        text: 'Based on Prophet time-series forecasting, theft cases in Bangalore are projected to reach 3,200-3,500 in the next quarter — a 12-18% increase. Crime rates are expected to peak during October-December (festive season).',
        kn: 'ಪ್ರವಾದಿ ಸಮಯ-ಸರಣಿ ಮುನ್ಸೂಚನೆಯ ಆಧಾರದ ಮೇಲೆ, ಮುಂದಿನ ತ್ರೈಮಾಸಿಕದಲ್ಲಿ ಬೆಂಗಳೂರಿನಲ್ಲಿ ಕಳ್ಳತನ ಪ್ರಕರಣಗಳು 3,200-3,500 ತಲುಪುವ ನಿರೀಕ್ಷೆಯಿದೆ.',
        chart: 'forecast_chart',
        followups: ['Show by district', 'What is driving the increase?', 'Confidence intervals'],
        evidence: [{ label: 'Forecast model output', count: 1, table: 'ForecastResult' }],
      };
    } else if (lowercase.includes('hotspot') || lowercase.includes('area') || lowercase.includes('location')) {
      response = {
        text: 'DBSCAN analysis identified 8 high-crime hotspots in Bangalore. The highest density cluster is in KG Halli (23 theft cases, 0.8km radius). Other hotspots include Shivajinagar, City Market, and Majestic area.',
        kn: 'ಡಿಬಿಎಸ್ಸಿಎಎನ್ ವಿಶ್ಲೇಷಣೆಯು ಬೆಂಗಳೂರಿನಲ್ಲಿ 8 ಹೆಚ್ಚಿನ ಅಪರಾಧ ಹಾಟ್‌ಸ್ಪಾಟ್‌ಗಳನ್ನು ಗುರುತಿಸಿದೆ.',
        chart: 'map_view',
        followups: ['Show on map', 'Patrol recommendations', 'Time-based analysis'],
        evidence: [{ label: 'DBSCAN clusters', count: 8, table: 'HotspotCluster' }],
      };
    } else {
      response = {
        text: 'Here is a summary of current crime statistics across Karnataka:',
        kn: 'ಕರ್ನಾಟಕದಾದ್ಯಂತದ ಪ್ರಸ್ತುತ ಅಪರಾಧ ಅಂಕಿಅಂಶಗಳ ಸಾರಾಂಶ ಇಲ್ಲಿದೆ:',
        followups: ['Show theft cases in Bangalore', 'Show murder statistics', 'What about cyber crime?', 'Show hotspot areas', 'Predict future trends'],
        evidence: [{ label: 'Aggregated statistics', count: 1, table: 'Multiple sources' }],
      };
    }

    return {
      message_id: Math.random().toString(36).slice(2),
      message_type: 'ai_response',
      content_text: response.text,
      content_kannada: response.kn,
      sql_text: response.sql,
      chart_recommendation: response.chart,
      evidence_refs: response.evidence ? response.evidence.map(e => ({
        evidence_id: `ev_${Math.random().toString(36).slice(2, 8)}`,
        evidence_type: 'database_fact',
        source_table: e.table,
        source_record_count: e.count,
        display_label: `${e.count.toLocaleString()} records from ${e.table}`,
      })) : [],
      suggested_followups: response.followups,
      created_at: new Date().toISOString(),
    };
  },

  async getForecastData(category?: string, district?: string): Promise<ForecastDataPoint[]> {
    await delay(400);
    const cat = category || 'Theft';
    const dist = district || 'Bengaluru Urban';
    const seed = cat.length + dist.length;
    const data: ForecastDataPoint[] = [];
    for (let i = 1; i <= 30; i++) {
      const base = 20 + seededRandom(seed + i) * 30;
      const noise = (seededRandom(seed + i + 100) - 0.5) * 10;
      data.push({
        date: `Day ${i}`,
        predicted: Math.round((base + noise) * 10) / 10,
        upper: Math.round((base + noise + 8 + seededRandom(seed + i + 200) * 6) * 10) / 10,
        lower: Math.round((base + noise - 8 - seededRandom(seed + i + 300) * 6) * 10) / 10,
        actual: i <= 7 ? Math.round((base + seededRandom(seed + i + 400) * 20) * 10) / 10 : undefined,
        category: cat,
        district: dist,
      });
    }
    return data;
  },

  async getMultiForecast(): Promise<{ category: string; data: ForecastDataPoint[] }[]> {
    await delay(500);
    const categories = ['Theft', 'Robbery', 'Assault', 'Cyber Crime', 'Burglary'];
    const results = await Promise.all(
      categories.map(cat => this.getForecastData(cat, 'Bengaluru Urban').then(data => ({ category: cat, data })))
    );
    return results;
  },

  async getDistrictForecasts(): Promise<{ district: string; data: ForecastDataPoint[] }[]> {
    await delay(500);
    const topDistricts = ['Bengaluru Urban', 'Mysuru', 'Hubballi-Dharwad', 'Mangaluru', 'Belagavi'];
    const results = await Promise.all(
      topDistricts.map(dist => this.getForecastData('Theft', dist).then(data => ({ district: dist, data })))
    );
    return results;
  },

  async getOffenderProfile(name: string): Promise<OffenderProfile> {
    await delay(600);
    const score = this.getPriorityScore();
    return {
      entity_name: name,
      total_score: score.total_score,
      risk_tier: score.risk_tier,
      features: score.features,
      linked_cases: [
        { case_id: 101, crime_no: 'CN202400101', crime_type: 'Theft', year: 2024, status: 'Under Investigation' },
        { case_id: 201, crime_no: 'CN202400201', crime_type: 'Robbery', year: 2023, status: 'Charge Sheeted' },
        { case_id: 301, crime_no: 'CN202400301', crime_type: 'Assault', year: 2024, status: 'Under Investigation' },
        { case_id: 401, crime_no: 'CN202300401', crime_type: 'Burglary', year: 2023, status: 'Closed' },
        { case_id: 501, crime_no: 'CN202400501', crime_type: 'Cheating', year: 2024, status: 'Pending' },
        { case_id: 601, crime_no: 'CN202400601', crime_type: 'Kidnapping', year: 2024, status: 'Under Investigation' },
        { case_id: 701, crime_no: 'CN202300701', crime_type: 'Theft', year: 2023, status: 'Charge Sheeted' },
        { case_id: 801, crime_no: 'CN202400801', crime_type: 'Robbery', year: 2024, status: 'Under Investigation' },
      ],
      disclaimer: 'This score is an analytical tool for investigation prioritization. It does not indicate guilt, dangerousness, or likelihood of future crime.',
    };
  },

  getPriorityScore(): PriorityScore {
    return {
      total_score: 56.45,
      risk_tier: 'ELEVATED',
      score_version: '1.0.0',
      features: [
        { name: 'Case Frequency', raw_value: '12 cases / 3 years', normalized_value: 0.54, weight: 0.25, contribution: 13.5 },
        { name: 'Crime Type Diversity', raw_value: '4 types', normalized_value: 0.40, weight: 0.15, contribution: 6.0 },
        { name: 'Geographic Spread', raw_value: '3 districts', normalized_value: 0.60, weight: 0.15, contribution: 9.0 },
        { name: 'Recent Activity', raw_value: '3 cases in 90 days', normalized_value: 0.60, weight: 0.20, contribution: 12.0 },
        { name: 'Co-Accused Network', raw_value: '8 co-accused', normalized_value: 0.53, weight: 0.15, contribution: 8.0 },
        { name: 'Arrest Ratio', raw_value: '80% arrest rate', normalized_value: 0.80, weight: 0.10, contribution: 8.0 },
      ],
      disclaimer: 'This score is an analytical tool for investigation prioritization.',
    };
  },

  async getTrends(): Promise<TrendDataPoint[]> {
    await delay(400);
    const types = ['Theft', 'Robbery', 'Assault', 'Burglary', 'Cyber Crime'];
    return types.flatMap(type => [
      { period: '2024-01', count: Math.floor(180 + seededRandom(type.length + 1) * 200), pct_change: undefined, crime_type: type },
      { period: '2024-02', count: Math.floor(180 + seededRandom(type.length + 2) * 200), pct_change: 9.4, crime_type: type },
      { period: '2024-03', count: Math.floor(180 + seededRandom(type.length + 3) * 200), pct_change: 12.9, crime_type: type },
      { period: '2024-04', count: Math.floor(180 + seededRandom(type.length + 4) * 200), pct_change: 8.0, crime_type: type },
      { period: '2024-05', count: Math.floor(180 + seededRandom(type.length + 5) * 200), pct_change: -4.5, crime_type: type },
      { period: '2024-06', count: Math.floor(180 + seededRandom(type.length + 6) * 200), pct_change: 15.8, crime_type: type },
    ]);
  },

  async getHotspots(): Promise<HotspotCluster[]> {
    await delay(400);
    return [
      { cluster_id: 1, centroid_lat: 12.9716, centroid_lng: 77.5946, case_count: 12, radius_km: 0.8, crime_type: 'Theft' },
      { cluster_id: 2, centroid_lat: 12.9344, centroid_lng: 77.6102, case_count: 8, radius_km: 0.5, crime_type: 'Robbery' },
      { cluster_id: 3, centroid_lat: 12.9612, centroid_lng: 77.5643, case_count: 15, radius_km: 1.2, crime_type: 'Assault' },
      { cluster_id: 4, centroid_lat: 12.9210, centroid_lng: 77.5910, case_count: 6, radius_km: 0.4, crime_type: 'Burglary' },
      { cluster_id: 5, centroid_lat: 12.9850, centroid_lng: 77.6100, case_count: 20, radius_km: 1.0, crime_type: 'Cyber Crime' },
      { cluster_id: 6, centroid_lat: 12.9500, centroid_lng: 77.5700, case_count: 10, radius_km: 0.6, crime_type: 'Cheating' },
      { cluster_id: 7, centroid_lat: 12.9400, centroid_lng: 77.6200, case_count: 7, radius_km: 0.3, crime_type: 'Kidnapping' },
      { cluster_id: 8, centroid_lat: 12.9800, centroid_lng: 77.5800, case_count: 18, radius_km: 0.9, crime_type: 'Theft' },
    ];
  },

  async getNetwork(accusedName: string): Promise<{ nodes: GraphNode[]; edges: GraphEdge[] }> {
    await delay(600);
    const tiers = ['LOW', 'MODERATE', 'ELEVATED', 'HIGH'] as const;
    const nodes: GraphNode[] = accusedNames.slice(0, 8).map((n, i) => ({
      id: `node_${i}`,
      label: n,
      node_type: 'accused',
      cases: Math.floor(seededRandom(i + 100) * 8) + 1,
      risk_tier: tiers[i % 4],
    }));
    const edges: GraphEdge[] = [];
    for (let i = 0; i < 14; i++) {
      const s = Math.floor(seededRandom(i + 200) * nodes.length);
      let t = Math.floor(seededRandom(i + 300) * nodes.length);
      if (s === t) t = (t + 1) % nodes.length;
      edges.push({
        id: `edge_${i}`,
        source: nodes[s].id,
        target: nodes[t].id,
        weight: Math.floor(seededRandom(i + 400) * 4) + 1,
        shared_cases: [101 + i, 102 + i],
      });
    }
    return { nodes, edges };
  },

  async getDashboardKpis(): Promise<{ label: string; value: string; change: string; icon: string }[]> {
    return [
      { label: 'Total FIRs', value: '12,847', change: '+12.4%', icon: 'FileText' },
      { label: 'Active Cases', value: '156', change: '-8.2%', icon: 'Activity' },
      { label: 'Clearance Rate', value: '71.2%', change: '+3.1%', icon: 'CheckCircle' },
      { label: 'Hotspots Active', value: '8', change: '+2', icon: 'MapPin' },
    ];
  },

  async getAlerts(): Promise<{ id: string; severity: string; title: string; description: string; rule_id: string; trigger_condition: string; created_at: string; acknowledged: boolean }[]> {
    return [
      { id: 'a1', severity: 'critical', title: 'Theft Surge Detected', description: 'Theft cases in Whitefield up 34% this month — automated threshold breach.', rule_id: 'R-THEFT-001', trigger_condition: 'pct_change > 25%', created_at: new Date().toISOString(), acknowledged: false },
      { id: 'a2', severity: 'warning', title: 'Seasonal Pattern Trigger', description: 'Burglary cases expected to rise 18-22% during upcoming festive season.', rule_id: 'R-SEASONAL-003', trigger_condition: 'Prophet forecast 80% CI breach', created_at: new Date(Date.now() - 86400000).toISOString(), acknowledged: false },
      { id: 'a3', severity: 'info', title: 'New Crime Type Detected', description: 'Cryptocurrency fraud cases emerging in Bengaluru Urban — 7 cases this week.', rule_id: 'R-NEWTYPE-007', trigger_condition: 'new_crime_type frequency > 5/week', created_at: new Date(Date.now() - 172800000).toISOString(), acknowledged: true },
      { id: 'a4', severity: 'warning', title: 'Hotspot Expansion', description: 'KG Halli hotspot radius expanded from 0.8km to 1.2km — increased patrol recommended.', rule_id: 'R-HOTSPOT-002', trigger_condition: 'DBSCAN cluster radius change > 30%', created_at: new Date(Date.now() - 259200000).toISOString(), acknowledged: false },
      { id: 'a5', severity: 'critical', title: 'Recidivism Alert', description: 'Known offender Ravi Kumar linked to 3 new cases this month — Priority Score now ELEVATED.', rule_id: 'R-RECIDIVISM-004', trigger_condition: 'Priority Score increase > 15 points in 30 days', created_at: new Date(Date.now() - 3600000).toISOString(), acknowledged: false },
    ];
  },

  async getActivityFeed(): Promise<{ id: string; text: string; time: string; type: string }[]> {
    return [
      { id: 'f1', text: 'New FIR filed: Theft at Whitefield station', time: '2 min ago', type: 'case' },
      { id: 'f2', text: 'Offender score updated for Suresh P — MODERATE', time: '15 min ago', type: 'score' },
      { id: 'f3', text: 'Community detection run on Bengaluru network — 4 communities found', time: '1 hour ago', type: 'network' },
      { id: 'f4', text: 'Prophet forecast refreshed — next 30 days projected', time: '2 hours ago', type: 'forecast' },
      { id: 'f5', text: 'Alert acknowledged: Theft surge in Whitefield', time: '3 hours ago', type: 'alert' },
    ];
  },
};
