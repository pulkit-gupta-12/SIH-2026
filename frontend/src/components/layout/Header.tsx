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
      className="sticky top-0 z-50 px-4 py-3 flex items-center justify-between bg-white border-b border-[var(--color-border)]"
    >
      {/* Logo & Title */}
      <div className="flex items-center gap-3">
        <div
          className="w-9 h-9 rounded-lg flex items-center justify-center text-lg font-bold text-[var(--color-text-primary)]"
          style={{
            background: 'linear-gradient(135deg, #e8730c, #d4670a)',
          }}
        >
          ⚖
        </div>
        <div className="hidden sm:block">
          <h1 className="text-sm font-semibold text-[var(--color-text-primary)]">
            Legal Metrology
          </h1>
          <p className="text-xs text-[var(--color-text-muted)]">
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
              background: `${roleConfig.color}12`,
              color: roleConfig.color,
              border: `1px solid ${roleConfig.color}25`,
            }}
          >
            <span>{roleConfig.icon}</span>
            {roleConfig.shortLabel}
          </span>
        )}

        <div className="text-right hidden sm:block">
          <p className="text-sm font-medium text-[var(--color-text-primary)]">
            {user?.name}
          </p>
          <p className="text-xs text-[var(--color-text-muted)]">
            {user?.email}
          </p>
        </div>

        <button
          onClick={logout}
          className="px-3 py-1.5 rounded-lg text-xs font-medium transition-colors duration-150 cursor-pointer bg-[var(--color-surface-tertiary)] text-[var(--color-text-secondary)] border border-[var(--color-border)] hover:bg-red-50 hover:text-red-600 hover:border-red-200"
        >
          Sign out
        </button>
      </div>
    </header>
  );
}
