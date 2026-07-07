import React, { useState } from 'react';
import { Shield } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { api } from '../services/api';

export const LoginPage: React.FC = () => {
  const { login } = useAuth();
  const [kgid, setKgid] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);
    try {
      const res = await api.login(kgid, password);
      login(res.user, res.token);
    } catch {
      setError('Invalid KGID or password. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-page">
      <div className="login-card">
        <div style={{ textAlign: 'center', marginBottom: 32 }}>
          <Shield size={48} color="var(--primary)" />
          <h1>Suraksha AI</h1>
          <p>KSP Intelligent Crime Analytics Platform</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>KGID</label>
            <input className="input" placeholder="Enter your KGID" value={kgid}
              onChange={e => setKgid(e.target.value)} required />
          </div>
          <div className="form-group">
            <label>Password</label>
            <input className="input" type="password" placeholder="Enter your password"
              value={password} onChange={e => setPassword(e.target.value)} required />
          </div>

          {error && <div style={{ color: 'var(--danger)', fontSize: 13, marginBottom: 16 }}>{error}</div>}

          <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'center' }} disabled={loading}>
            {loading ? 'Signing in...' : 'Sign In'}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: 24, fontSize: 12, color: 'var(--text-muted)' }}>
          <p>Demo credentials: INV001 / ANL001 / SUP001</p>
          <p style={{ marginTop: 4 }}>Password: test</p>
        </div>
      </div>
    </div>
  );
};
