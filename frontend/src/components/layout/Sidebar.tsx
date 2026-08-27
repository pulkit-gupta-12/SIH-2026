/**
 * Sidebar component — desktop navigation.
 * Shows navigation items relevant to the current role.
 */
import { NavLink } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { getRoleConfig } from '../../utils/roleConfig';
import type { UserRole } from '../../store/authStore';

interface NavItem {
  label: string;
  path: string;
  icon: string;
}

const NAV_ITEMS: Record<UserRole, NavItem[]> = {
  citizen: [
    { label: 'Dashboard', path: '/citizen', icon: '🏠' },
    { label: 'Scan Product', path: '/citizen/scan', icon: '📷' },
    { label: 'My Complaints', path: '/citizen/complaints', icon: '📝' },
  ],
  field_officer: [
    { label: 'Dashboard', path: '/officer', icon: '🏠' },
    { label: 'Inspection Queue', path: '/officer/queue', icon: '📋' },
    { label: 'Capture', path: '/officer/capture', icon: '📷' },
    { label: 'Cases', path: '/officer/cases', icon: '📁' },
  ],
  state_controller: [
    { label: 'Dashboard', path: '/controller', icon: '🏠' },
    { label: 'Heatmap', path: '/controller/heatmap', icon: '🗺️' },
    { label: 'Assignments', path: '/controller/assign', icon: '📋' },
    { label: 'Escalations', path: '/controller/escalations', icon: '⚠️' },
  ],
  national_admin: [
    { label: 'Command Center', path: '/national', icon: '🏠' },
    { label: 'Analytics', path: '/national/analytics', icon: '📊' },
    { label: 'Top Violators', path: '/national/violators', icon: '🔴' },
    { label: 'Policy', path: '/national/policy', icon: '📜' },
    { label: 'Reports', path: '/national/reports', icon: '📄' },
  ],
  business: [
    { label: 'Dashboard', path: '/business', icon: '🏠' },
    { label: 'Pre-Check', path: '/business/pre-check', icon: '✅' },
    { label: 'Compliance', path: '/business/compliance', icon: '📋' },
    { label: 'Notices', path: '/business/notices', icon: '📨' },
  ],
  ecommerce_partner: [
    { label: 'Dashboard', path: '/ecommerce', icon: '🏠' },
    { label: 'Upload', path: '/ecommerce/upload', icon: '📤' },
    { label: 'Flagged', path: '/ecommerce/flagged', icon: '🚩' },
  ],
  rule_admin: [
    { label: 'Dashboard', path: '/rule-admin', icon: '🏠' },
    { label: 'Rules', path: '/rule-admin/rules', icon: '📚' },
    { label: 'Drafts', path: '/rule-admin/drafts', icon: '✏️' },
    { label: 'Sandbox', path: '/rule-admin/sandbox', icon: '🧪' },
  ],
};

export default function Sidebar() {
  const { activeRole } = useAuthStore();
  if (!activeRole) return null;

  const roleConfig = getRoleConfig(activeRole);
  const items = NAV_ITEMS[activeRole] || [];

  return (
    <aside
      className="hidden md:flex flex-col w-60 min-h-screen py-4 px-3"
      style={{
        background: 'var(--color-surface-secondary)',
        borderRight: '1px solid var(--color-border)',
      }}
    >
      {/* Role label */}
      <div className="mb-6 px-3">
        <div
          className="flex items-center gap-2 px-3 py-2 rounded-xl text-sm font-semibold"
          style={{
            background: `${roleConfig.color}15`,
            color: roleConfig.color,
          }}
        >
          <span className="text-lg">{roleConfig.icon}</span>
          {roleConfig.shortLabel}
        </div>
      </div>

      {/* Nav items */}
      <nav className="flex-1 flex flex-col gap-1">
        {items.map((item) => (
          <NavLink
            key={item.path}
            to={item.path}
            end={item.path === `/${activeRole === 'field_officer' ? 'officer' : activeRole === 'state_controller' ? 'controller' : activeRole === 'national_admin' ? 'national' : activeRole === 'ecommerce_partner' ? 'ecommerce' : activeRole === 'rule_admin' ? 'rule-admin' : activeRole}`}
            className="flex items-center gap-3 px-3 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 no-underline"
            style={({ isActive }) => ({
              background: isActive ? `${roleConfig.color}20` : 'transparent',
              color: isActive ? roleConfig.color : 'var(--color-text-secondary)',
              border: isActive ? `1px solid ${roleConfig.color}30` : '1px solid transparent',
            })}
          >
            <span className="text-base">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* Bottom: platform version */}
      <div className="px-3 py-2 text-xs" style={{ color: 'var(--color-text-muted)' }}>
        v1.0.0 · Phase 1
      </div>
    </aside>
  );
}
