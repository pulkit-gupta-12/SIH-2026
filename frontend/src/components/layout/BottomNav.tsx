/**
 * BottomNav component — mobile navigation.
 * Shows 3-4 bottom tabs per role for mobile-first dashboards.
 */
import { NavLink } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
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

  national_admin: [
    { label: 'Console', path: '/admin', icon: '🇮🇳' },
    { label: 'Notices', path: '/admin/rules/notifications', icon: '🔔' },
    { label: 'Rules', path: '/admin/rules', icon: '📜' },
  ],
  business: [
    { label: 'Home', path: '/business', icon: '🏠' },
    { label: 'Pre-Check', path: '/business/pre-check', icon: '✅' },
    { label: 'Notices', path: '/business/notices', icon: '📨' },
  ],

  rule_admin: [
    { label: 'Console', path: '/admin', icon: '⚖️' },
    { label: 'Notices', path: '/admin/rules/notifications', icon: '🔔' },
    { label: 'Rules', path: '/admin/rules', icon: '📜' },
  ],
};

export default function BottomNav() {
  const { activeRole } = useAuthStore();
  if (!activeRole) return null;

  const items = BOTTOM_NAV_ITEMS[activeRole] || [];

  return (
    <nav
      className="md:hidden fixed bottom-0 left-0 right-0 z-50 flex items-stretch justify-around px-2 py-1 bg-white border-t border-[var(--color-border)]"
    >
      {items.map((item) => (
        <NavLink
          key={item.path}
          to={item.path}
          className={({ isActive }) =>
            `flex flex-col items-center gap-0.5 py-2 px-3 rounded-lg text-xs font-medium transition-colors duration-150 min-w-[60px] no-underline ${
              isActive
                ? 'text-[var(--color-accent)]'
                : 'text-[var(--color-text-muted)]'
            }`
          }
        >
          <span className="text-xl">{item.icon}</span>
          <span>{item.label}</span>
        </NavLink>
      ))}
    </nav>
  );
}
