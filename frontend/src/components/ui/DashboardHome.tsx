/**
 * DashboardHome — role-specific placeholder dashboard page.
 * Used for all 7 roles in Phase 1. Shows role info, welcome message,
 * and role-colored styling.
 */
import { useAuthStore } from '../../store/authStore';
import { getRoleConfig } from '../../utils/roleConfig';
import type { UserRole } from '../../store/authStore';

interface Props {
  role: UserRole;
}

interface StatCard {
  label: string;
  value: string;
  icon: string;
  trend?: string;
}

const ROLE_STATS: Record<UserRole, StatCard[]> = {
  citizen: [
    { label: 'Products Scanned', value: '—', icon: '📷', trend: 'Scan a product to start' },
    { label: 'Complaints Filed', value: '0', icon: '📝' },
    { label: 'Compliant Products', value: '—', icon: '✅' },
  ],
  field_officer: [
    { label: 'Pending Inspections', value: '—', icon: '📋', trend: 'Queue loading...' },
    { label: 'Cases Created', value: '0', icon: '📁' },
    { label: 'Scans This Week', value: '0', icon: '📷' },
    { label: 'Compliance Rate', value: '—', icon: '📊' },
  ],
  state_controller: [
    { label: 'Active Officers', value: '—', icon: '👮' },
    { label: 'Pending Escalations', value: '0', icon: '⚠️' },
    { label: 'Open Cases', value: '—', icon: '📁' },
    { label: 'State Compliance', value: '—', icon: '📊' },
  ],
  national_admin: [
    { label: 'States Monitored', value: '36', icon: '🇮🇳' },
    { label: 'Total Inspections', value: '—', icon: '🔍' },
    { label: 'Active Violations', value: '—', icon: '🔴' },
    { label: 'Compliance Trend', value: '—', icon: '📈' },
  ],
  business: [
    { label: 'Products Registered', value: '—', icon: '📦' },
    { label: 'Compliance Score', value: '—', icon: '✅' },
    { label: 'Active Notices', value: '0', icon: '📨' },
    { label: 'Last Pre-Check', value: '—', icon: '🕐' },
  ],
  ecommerce_partner: [
    { label: 'Listings Uploaded', value: '—', icon: '📤' },
    { label: 'Flagged Products', value: '0', icon: '🚩' },
    { label: 'Screening Pass Rate', value: '—', icon: '✅' },
  ],
  rule_admin: [
    { label: 'Active Rules', value: '—', icon: '📚' },
    { label: 'Pending Drafts', value: '0', icon: '✏️' },
    { label: 'Last Published', value: '—', icon: '📅' },
    { label: 'Sandbox Runs', value: '0', icon: '🧪' },
  ],
};

export default function DashboardHome({ role }: Props) {
  const { user } = useAuthStore();
  const config = getRoleConfig(role);
  const stats = ROLE_STATS[role];

  return (
    <div className="animate-fade-in">
      {/* Welcome banner */}
      <div
        className="rounded-2xl p-6 md:p-8 mb-6"
        style={{
          background: `linear-gradient(135deg, ${config.color}15, ${config.colorDark}10)`,
          border: `1px solid ${config.color}25`,
        }}
      >
        <div className="flex items-start gap-4">
          <div
            className="w-14 h-14 rounded-2xl flex items-center justify-center text-3xl shrink-0"
            style={{
              background: `linear-gradient(135deg, ${config.color}, ${config.colorDark})`,
              boxShadow: `0 8px 24px ${config.color}30`,
            }}
          >
            {config.icon}
          </div>
          <div>
            <h1 className="text-xl md:text-2xl font-bold mb-1" style={{ color: 'var(--color-text-primary)' }}>
              Welcome back, {user?.name || 'User'}
            </h1>
            <p className="text-sm" style={{ color: 'var(--color-text-secondary)' }}>
              {config.label} Dashboard &middot; {config.description}
            </p>
          </div>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4 mb-6">
        {stats.map((stat, i) => (
          <div
            key={stat.label}
            className="glass-card p-4 md:p-5 transition-all duration-300 animate-slide-up"
            style={{
              animationDelay: `${i * 0.1}s`,
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.borderColor = `${config.color}40`;
              e.currentTarget.style.transform = 'translateY(-2px)';
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.borderColor = 'var(--color-border)';
              e.currentTarget.style.transform = 'translateY(0)';
            }}
          >
            <div className="flex items-center justify-between mb-3">
              <span className="text-2xl">{stat.icon}</span>
              {stat.trend && (
                <span className="text-xs px-2 py-0.5 rounded-full" style={{
                  background: `${config.color}15`,
                  color: config.color,
                }}>
                  {stat.trend}
                </span>
              )}
            </div>
            <p className="text-2xl font-bold mb-1" style={{ color: 'var(--color-text-primary)' }}>
              {stat.value}
            </p>
            <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
              {stat.label}
            </p>
          </div>
        ))}
      </div>

      {/* Phase 1 notice */}
      <div
        className="glass-card p-5 flex items-start gap-3"
        style={{ borderColor: `${config.color}20` }}
      >
        <span className="text-xl">🚧</span>
        <div>
          <p className="text-sm font-semibold mb-1" style={{ color: 'var(--color-text-primary)' }}>
            Phase 1 — Foundation
          </p>
          <p className="text-xs leading-relaxed" style={{ color: 'var(--color-text-secondary)' }}>
            Authentication and role-based routing are active. Dashboard widgets will be
            populated with real API data in Phase 2 (Data Layer) and Phase 4 (Dashboard Build).
            All values shown as "—" will be replaced by live database queries.
          </p>
        </div>
      </div>
    </div>
  );
}
