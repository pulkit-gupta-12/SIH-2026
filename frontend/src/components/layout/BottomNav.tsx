/**
 * BottomNav component — mobile navigation.
 * Shows 3-4 bottom tabs per role for mobile-first dashboards.
 */
import { NavLink } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { getRoleConfig } from '../../utils/roleConfig';
import type { UserRole } from '../../store/authStore';

interface BottomNavItem {
  label: string;
  path: string;
  icon: string;
}

const BOTTOM_NAV_ITEMS: Record<UserRole, BottomNavItem[]> = {
  citizen: [
    { label: 'Home', path: '/citizen', icon: '🏠' },
    { label: 'Scan', path: '/citizen/scan', icon: '📷' },
    { label: 'Complaints', path: '/citizen/complaints', icon: '📝' },
  ],
  field_officer: [
    { label: 'Queue', path: '/officer', icon: '📋' },
    { label: 'Capture', path: '/officer/capture', icon: '📷' },
    { label: 'Cases', path: '/officer/cases', icon: '📁' },
  ],
  state_controller: [
    { label: 'Home', path: '/controller', icon: '🏠' },
    { label: 'Map', path: '/controller/heatmap', icon: '🗺️' },
    { label: 'Escalations', path: '/controller/escalations', icon: '⚠️' },
  ],
  national_admin: [
    { label: 'Home', path: '/national', icon: '🏠' },
    { label: 'Analytics', path: '/national/analytics', icon: '📊' },
    { label: 'Reports', path: '/national/reports', icon: '📄' },
  ],
  business: [
    { label: 'Home', path: '/business', icon: '🏠' },
    { label: 'Pre-Check', path: '/business/pre-check', icon: '✅' },
    { label: 'Notices', path: '/business/notices', icon: '📨' },
  ],
  ecommerce_partner: [
    { label: 'Home', path: '/ecommerce', icon: '🏠' },
    { label: 'Upload', path: '/ecommerce/upload', icon: '📤' },
    { label: 'Flagged', path: '/ecommerce/flagged', icon: '🚩' },
  ],
  rule_admin: [
    { label: 'Home', path: '/rule-admin', icon: '🏠' },
    { label: 'Rules', path: '/rule-admin/rules', icon: '📚' },
    { label: 'Sandbox', path: '/rule-admin/sandbox', icon: '🧪' },
  ],
};

export default function BottomNav() {
  const { activeRole } = useAuthStore();
  if (!activeRole) return null;

  const roleConfig = getRoleConfig(activeRole);
  const items = BOTTOM_NAV_ITEMS[activeRole] || [];

  return (
    <nav
      className="md:hidden fixed bottom-0 left-0 right-0 z-50 flex items-stretch justify-around px-2 py-1 backdrop-blur-xl"
      style={{
        background: 'rgba(15, 23, 42, 0.95)',
        borderTop: '1px solid var(--color-border)',
      }}
    >
      {items.map((item) => (
        <NavLink
          key={item.path}
          to={item.path}
          className="flex flex-col items-center gap-0.5 py-2 px-3 rounded-xl text-xs font-medium transition-all duration-200 min-w-[60px] no-underline"
          style={({ isActive }) => ({
            color: isActive ? roleConfig.color : 'var(--color-text-muted)',
          })}
        >
          <span className="text-xl">{item.icon}</span>
          <span>{item.label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
