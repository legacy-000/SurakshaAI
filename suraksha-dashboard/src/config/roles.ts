export interface RoleConfig {
  role_id: number;
  role_name: string;
  allowedRoutes: string[];
  allowedActions: string[];
}

export const ROLES: Record<string, RoleConfig> = {
  INVESTIGATOR: {
    role_id: 1,
    role_name: 'Investigator',
    allowedRoutes: ['/', '/chat', '/network', '/offender', '/workspace', '/alerts'],
    allowedActions: ['chat_query', 'view_offender', 'view_network', 'export_pdf', 'manage_investigation'],
  },
  ANALYST: {
    role_id: 2,
    role_name: 'Analyst',
    allowedRoutes: ['/', '/analytics', '/forecast', '/network', '/chat'],
    allowedActions: ['view_trends', 'view_forecast', 'export_pdf', 'chat_query'],
  },
  SUPERVISOR: {
    role_id: 3,
    role_name: 'Supervisor',
    allowedRoutes: ['/', '/chat', '/network', '/analytics', '/offender', '/forecast', '/alerts', '/workspace'],
    allowedActions: ['chat_query', 'view_offender', 'view_network', 'view_trends', 'view_forecast', 'export_pdf', 'manage_investigation'],
  },
  POLICYMAKER: {
    role_id: 4,
    role_name: 'Policymaker',
    allowedRoutes: ['/', '/analytics', '/forecast', '/alerts'],
    allowedActions: ['view_trends', 'view_forecast', 'export_pdf'],
  },
  SYSTEM_ADMIN: {
    role_id: 5,
    role_name: 'System Administrator',
    allowedRoutes: ['/', '/chat', '/network', '/analytics', '/offender', '/forecast', '/alerts', '/workspace'],
    allowedActions: ['*'],
  },
};

export function getRoleConfig(roleName: string): RoleConfig {
  const key = Object.keys(ROLES).find(k => ROLES[k].role_name === roleName);
  return key ? ROLES[key] : ROLES.INVESTIGATOR;
}

export function hasPermission(roleName: string, action: string): boolean {
  const config = getRoleConfig(roleName);
  return config.allowedActions.includes('*') || config.allowedActions.includes(action);
}

export function getNavItemsForRole(roleName: string) {
  const config = getRoleConfig(roleName);
  const allItems = [
    { to: '/', label: 'Dashboard', icon: 'LayoutDashboard' },
    { to: '/chat', label: 'AI Chat', icon: 'MessageSquare' },
    { to: '/network', label: 'Network', icon: 'GitBranch' },
    { to: '/analytics', label: 'Analytics', icon: 'BarChart3' },
    { to: '/offender', label: 'Offender Profile', icon: 'UserSearch' },
    { to: '/forecast', label: 'Forecast', icon: 'TrendingUp' },
    { to: '/alerts', label: 'Alerts', icon: 'Bell' },
    { to: '/workspace', label: 'Workspace', icon: 'FileText' },
  ];
  return allItems.filter(item => config.allowedRoutes.includes(item.to));
}
