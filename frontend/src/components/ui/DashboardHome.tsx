/**
 * DashboardHome — role-specific placeholder dashboard page.
 * Used for placeholder roles (Controller, Business, E-commerce).
 * Shows role info, welcome message, and KPI stat cards.
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
        className="rounded-xl p-6 md:p-8 mb-6 card-accent-left bg-white border border-[var(--color-border)]"
      >
        <div className="flex items-start gap-4">
          <div
            className="w-14 h-14 rounded-xl flex items-center justify-center text-3xl shrink-0 text-[var(--color-text-primary)]"
            style={{
              background: 'linear-gradient(135deg, var(--color-accent), var(--color-accent-hover))',
            }}
          >
            {config.icon}
          </div>
          <div>
            <h1 className="text-xl md:text-2xl font-bold mb-1 text-[var(--color-text-primary)]">
              Welcome back, {user?.name || 'User'}
            </h1>
            <p className="text-sm text-[var(--color-text-secondary)]">
              {config.label} Dashboard &middot; {config.description}
            </p>
          </div>
        </div>
      </div>

      {/* Stats grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 md:gap-4 mb-6">
        {stats.map((stat, i) => (
          <div
            key={stat.label}
            className="glass-card p-4 md:p-5 transition-all duration-150 animate-slide-up hover:shadow-md hover:-translate-y-px"
            style={{
              animationDelay: `${i * 0.05}s`,
            }}
          >
            <div className="flex items-center justify-between mb-3">
              <span
                className="w-10 h-10 rounded-lg flex items-center justify-center text-xl bg-[var(--color-accent-subtle)]"
              >
                {stat.icon}
              </span>
              {stat.trend && (
                <span className="text-xs px-2 py-0.5 rounded-full bg-[var(--color-accent-subtle)] text-[var(--color-accent)]">
                  {stat.trend}
                </span>
              )}
            </div>
            <p className="text-2xl font-bold mb-1 text-[var(--color-text-primary)]">
              {stat.value}
            </p>
            <p className="text-xs text-[var(--color-text-muted)]">
              {stat.label}
            </p>
          </div>
        ))}
      </div>

      {/* Phase notice */}
      <div
        className="glass-card card-accent-left p-5 flex items-start gap-3"
      >
        <span className="text-xl">🚧</span>
        <div>
          <p className="text-sm font-semibold mb-1 text-[var(--color-text-primary)]">
            Phase 1 — Foundation
          </p>
          <p className="text-xs leading-relaxed text-[var(--color-text-secondary)]">
            Authentication and role-based routing are active. Dashboard widgets will be
            populated with real API data in Phase 2 (Data Layer) and Phase 4 (Dashboard Build).
            All values shown as "—" will be replaced by live database queries.
          </p>
        </div>
      </div>
    </div>
  );
}
