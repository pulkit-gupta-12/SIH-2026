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

  national_admin: [
    { label: 'Admin Console', path: '/admin', icon: '🇮🇳' },
    { label: 'Notifications', path: '/admin/rules/notifications', icon: '🔔' },
    { label: 'Rule Repository', path: '/admin/rules', icon: '📜' },
  ],
  business: [
    { label: 'Dashboard', path: '/business', icon: '🏠' },
    { label: 'Pre-Check', path: '/business/pre-check', icon: '✅' },
    { label: 'Compliance', path: '/business/compliance', icon: '📋' },
    { label: 'Notices', path: '/business/notices', icon: '📨' },
  ],

  rule_admin: [
    { label: 'Admin Console', path: '/admin', icon: '⚖️' },
    { label: 'Notifications', path: '/admin/rules/notifications', icon: '🔔' },
    { label: 'Rule Repository', path: '/admin/rules', icon: '📜' },
  ],
};

export default function Sidebar() {
  const { activeRole } = useAuthStore();
  if (!activeRole) return null;

  const roleConfig = getRoleConfig(activeRole);
  const items = NAV_ITEMS[activeRole] || [];

  return (
    <aside
      className="hidden md:flex flex-col w-60 min-h-screen py-4 px-3 border-r border-[var(--color-border)] bg-white"
    >
      {/* Role label */}
      <div className="mb-6 px-3">
        <div
          className="flex items-center gap-2 px-3 py-2 rounded-lg text-sm font-semibold"
          style={{
            background: `${roleConfig.color}12`,
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
            end={item.path === '/admin' || item.path === '/citizen' || item.path === '/officer' || item.path === '/business'}
            className={({ isActive }) =>
              `flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm font-medium transition-colors duration-150 no-underline ${
                isActive
                  ? 'bg-[var(--color-accent-subtle)] text-[var(--color-accent)] font-semibold'
                  : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-tertiary)] hover:text-[var(--color-text-primary)]'
              }`
            }
          >
            <span className="text-base">{item.icon}</span>
            {item.label}
          </NavLink>
        ))}
      </nav>

      {/* Bottom: platform version */}
      <div className="px-3 py-2 text-xs text-[var(--color-text-muted)]">
        v1.0.0 · Phase 4.3
      </div>
    </aside>
  );
}
