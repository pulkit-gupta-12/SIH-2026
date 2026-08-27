/**
 * Header component — top bar with user info, role badge, and logout.
 */
import { useAuthStore } from '../../store/authStore';
import { getRoleConfig } from '../../utils/roleConfig';

export default function Header() {
  const { user, activeRole, logout } = useAuthStore();
  const roleConfig = activeRole ? getRoleConfig(activeRole) : null;

  return (
    <header
      style={{
        background: 'var(--color-surface-secondary)',
        borderBottom: '1px solid var(--color-border)',
      }}
      className="sticky top-0 z-50 px-4 py-3 flex items-center justify-between backdrop-blur-md"
    >
      {/* Logo & Title */}
      <div className="flex items-center gap-3">
        <div
          className="w-9 h-9 rounded-lg flex items-center justify-center text-lg font-bold"
          style={{
            background: roleConfig
              ? `linear-gradient(135deg, ${roleConfig.color}, ${roleConfig.colorDark})`
              : 'linear-gradient(135deg, #6366f1, #4f46e5)',
          }}
        >
          ⚖
        </div>
        <div className="hidden sm:block">
          <h1 className="text-sm font-semibold" style={{ color: 'var(--color-text-primary)' }}>
            Legal Metrology
          </h1>
          <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
            Compliance Platform
          </p>
        </div>
      </div>

      {/* Right side: role badge + user + logout */}
      <div className="flex items-center gap-3">
        {roleConfig && (
          <span
            className="px-3 py-1 rounded-full text-xs font-medium hidden sm:inline-flex items-center gap-1.5"
            style={{
              background: `${roleConfig.color}20`,
              color: roleConfig.color,
              border: `1px solid ${roleConfig.color}30`,
            }}
          >
            <span>{roleConfig.icon}</span>
            {roleConfig.shortLabel}
          </span>
        )}

        <div className="text-right hidden sm:block">
          <p className="text-sm font-medium" style={{ color: 'var(--color-text-primary)' }}>
            {user?.name}
          </p>
          <p className="text-xs" style={{ color: 'var(--color-text-muted)' }}>
            {user?.email}
          </p>
        </div>

        <button
          onClick={logout}
          className="px-3 py-1.5 rounded-lg text-xs font-medium transition-all duration-200 cursor-pointer"
          style={{
            background: 'var(--color-surface-tertiary)',
            color: 'var(--color-text-secondary)',
            border: '1px solid var(--color-border)',
          }}
          onMouseEnter={(e) => {
            e.currentTarget.style.background = 'var(--color-non-compliant)';
            e.currentTarget.style.color = '#fff';
            e.currentTarget.style.borderColor = 'var(--color-non-compliant)';
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.background = 'var(--color-surface-tertiary)';
            e.currentTarget.style.color = 'var(--color-text-secondary)';
            e.currentTarget.style.borderColor = 'var(--color-border)';
          }}
        >
          Logout
        </button>
      </div>
    </header>
  );
}
