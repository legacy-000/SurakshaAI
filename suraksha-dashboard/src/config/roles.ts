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
    allowedRoutes: ['/', '/chat', '/database', '/network', '/offender', '/workspace', '/alerts', '/registration', '/search', '/chargesheet', '/inbox', '/access-control', '/coordination', '/groups', '/audit-log'],
    allowedActions: ['chat_query', 'view_offender', 'view_network', 'export_pdf', 'manage_investigation', 'file_fir', 'manage_chargesheet'],
  },
  ANALYST: {
    role_id: 2,
    role_name: 'Analyst',
    allowedRoutes: ['/', '/analytics', '/forecast', '/network', '/chat', '/database', '/search', '/command-center', '/similarity', '/agent-workbench', '/inbox', '/access-control', '/coordination', '/groups', '/audit-log'],
    allowedActions: ['view_trends', 'view_forecast', 'export_pdf', 'chat_query', 'view_command_center', 'view_similarity', 'view_geospatial', 'commander_query'],
  },
  SUPERVISOR: {
    role_id: 3,
    role_name: 'Supervisor',
    allowedRoutes: ['/', '/chat', '/network', '/analytics', '/offender', '/forecast', '/alerts', '/workspace', '/registration', '/search', '/chargesheet', '/command-center', '/similarity', '/agent-workbench', '/inbox', '/access-control', '/coordination', '/groups', '/audit-log'],
    allowedActions: ['chat_query', 'view_offender', 'view_network', 'view_trends', 'view_forecast', 'export_pdf', 'manage_investigation', 'file_fir', 'manage_chargesheet', 'view_command_center', 'view_similarity', 'view_geospatial', 'commander_query'],
  },
  POLICYMAKER: {
    role_id: 4,
    role_name: 'Policymaker',
    allowedRoutes: ['/', '/analytics', '/forecast', '/alerts', '/search'],
    allowedActions: ['view_trends', 'view_forecast', 'export_pdf'],
  },
  SYSTEM_ADMIN: {
    role_id: 5,
    role_name: 'System Administrator',
    allowedRoutes: ['/', '/chat', '/network', '/analytics', '/offender', '/forecast', '/alerts', '/workspace', '/registration', '/search', '/chargesheet', '/command-center', '/similarity', '/agent-workbench', '/inbox', '/access-control', '/coordination', '/groups', '/audit-log'],
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

// @ts-ignore - used by role config resolution

export function getNavItemsForRole(roleName: string) {
  const config = getRoleConfig(roleName);
  const allItems = [
    { to: '/', label: 'Dashboard', icon: 'LayoutDashboard' },
    { to: '/chat', label: 'AI Chat', icon: 'MessageSquare' },
    { to: '/database', label: 'Database Mode', icon: 'Database' },
    { to: '/network', label: 'Network', icon: 'GitBranch' },
    { to: '/analytics', label: 'Analytics', icon: 'BarChart3' },
    { to: '/offender', label: 'Offender Profile', icon: 'UserSearch' },
    { to: '/forecast', label: 'Forecast', icon: 'TrendingUp' },
    { to: '/alerts', label: 'Alerts', icon: 'Bell' },
    { to: '/workspace', label: 'Workspace', icon: 'FileText' },
    { to: '/registration', label: 'Case Registration', icon: 'FileText' },
    { to: '/search', label: 'Search', icon: 'UserSearch' },
    { to: '/chargesheet', label: 'Chargesheet', icon: 'FileText' },
    { to: '/command-center', label: 'Command Center', icon: 'Shield' },
    { to: '/similarity', label: 'Case Similarity', icon: 'GitBranch' },
    { to: '/agent-workbench', label: 'Agent Workbench', icon: 'Bot' },
    { to: '/inbox', label: 'Message Inbox', icon: 'Mail' },
    { to: '/access-control', label: 'Access Control', icon: 'UserCheck' },
    { to: '/coordination', label: 'Coordination', icon: 'GitPullRequest' },
    { to: '/groups', label: 'Groups', icon: 'Users' },
    { to: '/audit-log', label: 'Audit Log', icon: 'Activity' },
  ];
  return allItems.filter(item => config.allowedRoutes.includes(item.to));
}
