import React from 'react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { useAuth } from '../context/AuthContext';

const kpiData = [
  { label: 'Total Cases', value: '12,847' },
  { label: 'Heinous %', value: '28.3%' },
  { label: 'Pending', value: '2,341' },
  { label: 'Districts', value: '31' },
];

const chartData = [
  { month: 'Jan', cases: 234 }, { month: 'Feb', cases: 256 },
  { month: 'Mar', cases: 289 }, { month: 'Apr', cases: 312 },
  { month: 'May', cases: 298 }, { month: 'Jun', cases: 345 },
];

export const DashboardPage: React.FC = () => {
  const { user } = useAuth();

  return (
    <div>
      <div className="page-header">
        <h1>Welcome, {user?.first_name}</h1>
        <p>Karnataka State Police — Crime Analytics Dashboard</p>
      </div>

      <div className="grid-4">
        {kpiData.map(kpi => (
          <div key={kpi.label} className="card kpi-card">
            <div className="kpi-value">{kpi.value}</div>
            <div className="kpi-label">{kpi.label}</div>
          </div>
        ))}
      </div>

      <div className="grid-2" style={{ marginTop: 24 }}>
        <div className="card">
          <div className="card-header">Crime Trends (Last 6 Months)</div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={chartData}>
              <XAxis dataKey="month" stroke="var(--text-muted)" fontSize={12} />
              <YAxis stroke="var(--text-muted)" fontSize={12} />
              <Tooltip
                contentStyle={{
                  background: 'var(--bg-card)',
                  border: '1px solid var(--border)',
                  borderRadius: 8,
                  color: 'var(--text-primary)',
                }}
              />
              <Bar dataKey="cases" fill="var(--primary)" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>

        <div className="card">
          <div className="card-header">Recent Activity</div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {[
              { text: 'New case filed: Theft in Bangalore North', time: '2 min ago' },
              { text: 'Alert: Crime spike detected in Mysuru', time: '15 min ago' },
              { text: 'Offender profile updated: Ravi Kumar', time: '1 hour ago' },
              { text: 'Forecast generated for Bangalore Urban', time: '2 hours ago' },
              { text: 'Investigation workspace updated: Case #101', time: '3 hours ago' },
            ].map((item, i) => (
              <div key={i} style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', padding: '8px 0', borderBottom: '1px solid var(--border)' }}>
                <span style={{ fontSize: 14, color: 'var(--text-secondary)' }}>{item.text}</span>
                <span style={{ fontSize: 12, color: 'var(--text-muted)' }}>{item.time}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
};
