/**
 * Login Page — role-based login with demo user quick-login cards.
 * Premium dark-mode design with glassmorphism and micro-animations.
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { authService } from '../../services/authService';
import { ROLE_CONFIGS, ALL_ROLES } from '../../utils/roleConfig';
import type { UserRole } from '../../store/authStore';

// Demo credentials per role — matches seed_roles management command
const DEMO_USERS: Record<UserRole, { username: string; password: string }> = {
  citizen: { username: 'citizen_demo', password: 'demo1234' },
  field_officer: { username: 'officer_demo', password: 'demo1234' },
  state_controller: { username: 'controller_demo', password: 'demo1234' },
  national_admin: { username: 'admin_demo', password: 'demo1234' },
  business: { username: 'business_demo', password: 'demo1234' },
  ecommerce_partner: { username: 'ecommerce_demo', password: 'demo1234' },
  rule_admin: { username: 'ruleadmin_demo', password: 'demo1234' },
};

export default function LoginPage() {
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingRole, setLoadingRole] = useState<UserRole | null>(null);

  const handleLogin = async (user: string, pass: string, role?: UserRole) => {
    setError('');
    setLoading(true);
    if (role) setLoadingRole(role);

    try {
      const data = await authService.login({ username: user, password: pass });
      setAuth(data.user, data.access, data.refresh);

      // Navigate to the role's home
      const activeRole = data.user.roles[0] as UserRole;
      const config = ROLE_CONFIGS[activeRole];
      navigate(config?.homePath || '/');
    } catch (err: unknown) {
      const msg =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string } } }).response?.data?.detail || 'Login failed'
          : 'Network error — is the backend running?';
      setError(msg);
    } finally {
      setLoading(false);
      setLoadingRole(null);
    }
  };

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center p-4"
      style={{
        background: 'linear-gradient(135deg, #0f172a 0%, #1e1b4b 50%, #0f172a 100%)',
      }}
    >
      {/* Decorative background orbs */}
      <div
        className="fixed top-20 left-20 w-72 h-72 rounded-full opacity-10 blur-3xl pointer-events-none"
        style={{ background: 'var(--color-national)' }}
      />
      <div
        className="fixed bottom-20 right-20 w-96 h-96 rounded-full opacity-10 blur-3xl pointer-events-none"
        style={{ background: 'var(--color-citizen)' }}
      />

      {/* Main card */}
      <div
        className="relative w-full max-w-5xl glass-card p-6 md:p-10 animate-fade-in"
      >
        {/* Header */}
        <div className="text-center mb-8">
          <div className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4 text-3xl"
            style={{
              background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
              boxShadow: '0 8px 32px rgba(99, 102, 241, 0.3)',
            }}
          >
            ⚖
          </div>
          <h1 className="text-2xl md:text-3xl font-bold mb-2 text-gradient">
            Legal Metrology Compliance Platform
          </h1>
          <p style={{ color: 'var(--color-text-secondary)' }} className="text-sm md:text-base">
            National platform for transparent, tech-driven trade enforcement
          </p>
        </div>

        {/* Manual login form */}
        <div className="max-w-sm mx-auto mb-8">
          <div className="flex flex-col gap-3">
            <input
              id="login-username"
              type="text"
              placeholder="Username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-4 py-3 rounded-xl text-sm outline-none transition-all duration-200"
              style={{
                background: 'var(--color-surface-tertiary)',
                color: 'var(--color-text-primary)',
                border: '1px solid var(--color-border)',
              }}
              onFocus={(e) => (e.target.style.borderColor = 'var(--color-border-focus)')}
              onBlur={(e) => (e.target.style.borderColor = 'var(--color-border)')}
            />
            <input
              id="login-password"
              type="password"
              placeholder="Password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleLogin(username, password)}
              className="w-full px-4 py-3 rounded-xl text-sm outline-none transition-all duration-200"
              style={{
                background: 'var(--color-surface-tertiary)',
                color: 'var(--color-text-primary)',
                border: '1px solid var(--color-border)',
              }}
              onFocus={(e) => (e.target.style.borderColor = 'var(--color-border-focus)')}
              onBlur={(e) => (e.target.style.borderColor = 'var(--color-border)')}
            />
            {error && (
              <p className="text-xs px-1" style={{ color: 'var(--color-non-compliant)' }}>
                {error}
              </p>
            )}
            <button
              id="login-submit"
              onClick={() => handleLogin(username, password)}
              disabled={loading || !username || !password}
              className="w-full py-3 rounded-xl text-sm font-semibold transition-all duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed"
              style={{
                background: 'linear-gradient(135deg, #6366f1, #8b5cf6)',
                color: '#fff',
                border: 'none',
              }}
            >
              {loading && !loadingRole ? 'Signing in...' : 'Sign In'}
            </button>
          </div>
        </div>

        {/* Divider */}
        <div className="flex items-center gap-4 mb-6">
          <div className="flex-1 h-px" style={{ background: 'var(--color-border)' }} />
          <span className="text-xs font-medium" style={{ color: 'var(--color-text-muted)' }}>
            or quick login as a demo user
          </span>
          <div className="flex-1 h-px" style={{ background: 'var(--color-border)' }} />
        </div>

        {/* Role selector grid */}
        <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
          {ALL_ROLES.map((role, index) => {
            const config = ROLE_CONFIGS[role];
            const demo = DEMO_USERS[role];
            const isLoading = loadingRole === role;

            return (
              <button
                key={role}
                id={`demo-login-${role}`}
                onClick={() => handleLogin(demo.username, demo.password, role)}
                disabled={loading}
                className="flex flex-col items-center gap-2 p-4 rounded-2xl transition-all duration-300 cursor-pointer disabled:opacity-50 group"
                style={{
                  background: 'var(--color-surface-secondary)',
                  border: '1px solid var(--color-border)',
                  animationDelay: `${index * 0.05}s`,
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.borderColor = config.color;
                  e.currentTarget.style.boxShadow = `0 4px 20px ${config.color}20`;
                  e.currentTarget.style.transform = 'translateY(-2px)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.borderColor = 'var(--color-border)';
                  e.currentTarget.style.boxShadow = 'none';
                  e.currentTarget.style.transform = 'translateY(0)';
                }}
              >
                <span
                  className="w-12 h-12 rounded-xl flex items-center justify-center text-2xl transition-transform duration-300"
                  style={{
                    background: `${config.color}15`,
                  }}
                >
                  {config.icon}
                </span>
                <div className="text-center">
                  <p
                    className="text-xs font-semibold"
                    style={{ color: 'var(--color-text-primary)' }}
                  >
                    {config.shortLabel}
                  </p>
                  <p
                    className="text-xs mt-0.5 line-clamp-2"
                    style={{ color: 'var(--color-text-muted)' }}
                  >
                    {isLoading ? 'Signing in...' : config.description}
                  </p>
                </div>
                <div
                  className="w-full h-0.5 rounded-full mt-1 transition-all duration-300"
                  style={{
                    background: `linear-gradient(90deg, ${config.color}, ${config.colorDark})`,
                    opacity: 0.3,
                  }}
                />
              </button>
            );
          })}
        </div>

        {/* Footer */}
        <p className="text-center mt-6 text-xs" style={{ color: 'var(--color-text-muted)' }}>
          Demo credentials: username shown on card &middot; password: <code className="px-1.5 py-0.5 rounded" style={{ background: 'var(--color-surface-tertiary)' }}>demo1234</code>
        </p>
      </div>
    </div>
  );
}
