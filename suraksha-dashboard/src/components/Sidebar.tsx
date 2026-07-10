import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';
import { useTheme } from '../context/ThemeContext';
import { useLanguage } from '../context/LanguageContext';
import { getNavItemsForRole } from '../config/roles';
import {
  LayoutDashboard, MessageSquare, GitBranch, BarChart3, UserSearch,
  TrendingUp, Bell, Shield, FileText, LogOut, Moon, Sun, Languages
} from 'lucide-react';

const iconMap: Record<string, React.FC<any>> = {
  LayoutDashboard, MessageSquare, GitBranch, BarChart3,
  UserSearch, TrendingUp, Bell, FileText,
};

export const Sidebar: React.FC = () => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { lang, toggleLang, t } = useLanguage();

  const navItems = user ? getNavItemsForRole(user.role_name) : [];

  return (
    <aside className="sidebar">
      <div className="sidebar-logo">
        <Shield size={28} />
        <span>Suraksha AI</span>
      </div>

      <nav className="sidebar-nav">
        {navItems.map(item => {
          const Icon = iconMap[item.icon] || LayoutDashboard;
          return (
            <NavLink key={item.to} to={item.to} end={item.to === '/'}
              className={({ isActive }) => `nav-item ${isActive ? 'active' : ''}`}>
              <Icon size={20} />
              <span>{t(item.label, item.label === 'Dashboard' ? 'ಡ್ಯಾಶ್ಬೋರ್ಡ್' : item.label === 'AI Chat' ? 'ಎಐ ಚಾಟ್' : item.label === 'Network' ? 'ನೆಟ್ವರ್ಕ್' : item.label === 'Analytics' ? 'ವಿಶ್ಲೇಷಣೆ' : item.label === 'Offender Profile' ? 'ಅಪರಾಧಿ ಪ್ರೊಫೈಲ್' : item.label === 'Forecast' ? 'ಮುನ್ಸೂಚನೆ' : item.label === 'Alerts' ? 'ಎಚ್ಚರಿಕೆಗಳು' : item.label === 'Workspace' ? 'ಕಾರ್ಯಕ್ಷೇತ್ರ' : item.label)}</span>
            </NavLink>
          );
        })}
      </nav>

      <div style={{ borderTop: '1px solid var(--border)', paddingTop: 16, marginTop: 'auto' }}>
        <div style={{ padding: '8px 16px', marginBottom: 8 }}>
          <div style={{ fontSize: 13, fontWeight: 500 }}>{user?.first_name}</div>
          <div style={{ fontSize: 12, color: 'var(--text-muted)' }}>{user?.role_name}</div>
        </div>
        <button className={`nav-item ${lang === 'kn' ? 'active' : ''}`} onClick={toggleLang}>
          <Languages size={20} />
          <span>{lang === 'en' ? 'ಕನ್ನಡ' : 'English'}</span>
        </button>
        <button className="nav-item" onClick={toggleTheme}>
          {theme === 'dark' ? <Sun size={20} /> : <Moon size={20} />}
          <span>{theme === 'dark' ? 'Light Mode' : 'Dark Mode'}</span>
        </button>
        <button className="nav-item" onClick={logout}>
          <LogOut size={20} />
          <span>{t('Logout', 'ನಿರ್ಗಮಿಸಿ')}</span>
        </button>
      </div>
    </aside>
  );
};
