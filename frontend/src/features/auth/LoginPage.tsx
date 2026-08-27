/**
 * Login & Registration Page — role-based auth with demo user quick-login cards
 * and a full Create Account flow for any of the 7 roles.
 * Premium dark-mode design with glassmorphism, dynamic lane colors, and animations.
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { authService } from '../../services/authService';
import type { RegisterData } from '../../services/authService';
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

const INDIAN_STATES = [
  'Delhi',
  'Maharashtra',
  'Karnataka',
  'Tamil Nadu',
  'Gujarat',
  'Uttar Pradesh',
  'Telangana',
  'West Bengal',
  'Rajasthan',
  'Madhya Pradesh',
  'Punjab',
  'Haryana',
  'Kerala',
  'Assam',
];

export default function LoginPage() {
  const navigate = useNavigate();
  const { setAuth } = useAuthStore();

  const [activeTab, setActiveTab] = useState<'login' | 'register'>('login');

  // Sign In State
  const [loginUsername, setLoginUsername] = useState('');
  const [loginPassword, setLoginPassword] = useState('');

  // Register State
  const [regRole, setRegRole] = useState<UserRole>('citizen');
  const [regFirstName, setRegFirstName] = useState('');
  const [regLastName, setRegLastName] = useState('');
  const [regUsername, setRegUsername] = useState('');
  const [regEmail, setRegEmail] = useState('');
  const [regPhone, setRegPhone] = useState('');
  const [regPassword, setRegPassword] = useState('');
  const [regState, setRegState] = useState('Delhi');
  const [regOrg, setRegOrg] = useState('');

  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingRole, setLoadingRole] = useState<UserRole | null>(null);

  const selectedRoleConfig = ROLE_CONFIGS[regRole];

  // Handle Login
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
          ? (err as { response?: { data?: { detail?: string; error?: string } } }).response?.data?.detail ||
            (err as { response?: { data?: { detail?: string; error?: string } } }).response?.data?.error ||
            'Login failed. Please check your credentials.'
          : 'Network error — is the backend running?';
      setError(msg);
    } finally {
      setLoading(false);
      setLoadingRole(null);
    }
  };

  // Handle Register
  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');

    if (!regUsername.trim() || !regPassword) {
      setError('Please provide a username and password.');
      return;
    }

    if (regPassword.length < 6) {
      setError('Password must be at least 6 characters.');
      return;
    }

    setLoading(true);

    const payload: RegisterData = {
      username: regUsername.trim(),
      password: regPassword,
      email: regEmail.trim() || undefined,
      first_name: regFirstName.trim() || undefined,
      last_name: regLastName.trim() || undefined,
      phone: regPhone.trim() || undefined,
      role: regRole,
      state: regRole === 'field_officer' || regRole === 'state_controller' ? regState : undefined,
      organization: regRole === 'business' || regRole === 'ecommerce_partner' ? regOrg.trim() : undefined,
    };

    try {
      const data = await authService.register(payload);
      setAuth(data.user, data.access, data.refresh);

      const activeRole = data.user.roles[0] as UserRole;
      const config = ROLE_CONFIGS[activeRole];
      navigate(config?.homePath || '/');
    } catch (err: unknown) {
      let msg = 'Registration failed. Please check the entered details.';
      if (err && typeof err === 'object' && 'response' in err) {
        const resData = (err as { response?: { data?: Record<string, string[] | string> } }).response?.data;
        if (resData) {
          const firstKey = Object.keys(resData)[0];
          const val = resData[firstKey];
          msg = Array.isArray(val) ? `${firstKey}: ${val[0]}` : typeof val === 'string' ? val : msg;
        }
      }
      setError(msg);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen flex flex-col items-center justify-center p-4 py-8"
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

      {/* Main container */}
      <div className="relative w-full max-w-4xl glass-card p-6 md:p-10 animate-fade-in my-auto">
        {/* Header */}
        <div className="text-center mb-6">
          <div
            className="inline-flex items-center justify-center w-16 h-16 rounded-2xl mb-4 text-3xl"
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

        {/* Tab Switcher */}
        <div className="flex justify-center mb-8">
          <div
            className="inline-flex p-1 rounded-xl"
            style={{
              background: 'var(--color-surface-tertiary)',
              border: '1px solid var(--color-border)',
            }}
          >
            <button
              onClick={() => {
                setActiveTab('login');
                setError('');
              }}
              className={`px-6 py-2 rounded-lg text-sm font-semibold transition-all duration-200 cursor-pointer ${
                activeTab === 'login'
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => {
                setActiveTab('register');
                setError('');
              }}
              className={`px-6 py-2 rounded-lg text-sm font-semibold transition-all duration-200 cursor-pointer ${
                activeTab === 'register'
                  ? 'bg-indigo-600 text-white shadow-md'
                  : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              Create Account
            </button>
          </div>
        </div>

        {/* ===================== TAB 1: SIGN IN ===================== */}
        {activeTab === 'login' && (
          <div className="animate-fade-in">
            {/* Manual login form */}
            <div className="max-w-sm mx-auto mb-8">
              <div className="flex flex-col gap-3">
                <input
                  id="login-username"
                  type="text"
                  placeholder="Username"
                  value={loginUsername}
                  onChange={(e) => setLoginUsername(e.target.value)}
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
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleLogin(loginUsername, loginPassword)}
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
                  <p className="text-xs px-1 text-red-400">
                    {error}
                  </p>
                )}
                <button
                  id="login-submit"
                  onClick={() => handleLogin(loginUsername, loginPassword)}
                  disabled={loading || !loginUsername || !loginPassword}
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
                    className="flex flex-col items-center gap-2 p-4 rounded-2xl transition-all duration-300 cursor-pointer disabled:opacity-50 group text-left"
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
              Demo credentials: username shown on card &middot; password:{' '}
              <code className="px-1.5 py-0.5 rounded" style={{ background: 'var(--color-surface-tertiary)' }}>
                demo1234
              </code>
            </p>
          </div>
        )}

        {/* ===================== TAB 2: CREATE ACCOUNT ===================== */}
        {activeTab === 'register' && (
          <form onSubmit={handleRegister} className="animate-fade-in max-w-2xl mx-auto">
            {/* Step 1: Select Role */}
            <div className="mb-6">
              <label className="block text-xs font-semibold uppercase tracking-wider mb-2 text-slate-300">
                1. Select Your Dashboard Role
              </label>
              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                {ALL_ROLES.map((role) => {
                  const config = ROLE_CONFIGS[role];
                  const isSelected = regRole === role;

                  return (
                    <button
                      type="button"
                      key={role}
                      onClick={() => setRegRole(role)}
                      className={`flex flex-col items-center gap-1.5 p-3 rounded-xl transition-all duration-200 cursor-pointer text-center ${
                        isSelected ? 'ring-2' : 'opacity-70 hover:opacity-100'
                      }`}
                      style={{
                        background: isSelected ? `${config.color}20` : 'var(--color-surface-secondary)',
                        border: `1px solid ${isSelected ? config.color : 'var(--color-border)'}`,
                        boxShadow: isSelected ? `0 0 16px ${config.color}30` : 'none',
                      }}
                    >
                      <span className="text-2xl">{config.icon}</span>
                      <span className="text-xs font-semibold" style={{ color: 'var(--color-text-primary)' }}>
                        {config.shortLabel}
                      </span>
                    </button>
                  );
                })}
              </div>
              <p className="text-xs mt-2 text-slate-400 flex items-center gap-1.5">
                <span className="font-medium text-slate-200">{selectedRoleConfig.label}:</span>
                {selectedRoleConfig.description}
              </p>
            </div>

            {/* Step 2: Personal & Account Information */}
            <div className="mb-6">
              <label className="block text-xs font-semibold uppercase tracking-wider mb-2 text-slate-300">
                2. Account Credentials
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
                <div>
                  <input
                    type="text"
                    placeholder="First Name"
                    value={regFirstName}
                    onChange={(e) => setRegFirstName(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl text-sm outline-none"
                    style={{
                      background: 'var(--color-surface-tertiary)',
                      color: 'var(--color-text-primary)',
                      border: '1px solid var(--color-border)',
                    }}
                  />
                </div>
                <div>
                  <input
                    type="text"
                    placeholder="Last Name"
                    value={regLastName}
                    onChange={(e) => setRegLastName(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl text-sm outline-none"
                    style={{
                      background: 'var(--color-surface-tertiary)',
                      color: 'var(--color-text-primary)',
                      border: '1px solid var(--color-border)',
                    }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
                <div>
                  <input
                    type="text"
                    placeholder="Username *"
                    required
                    value={regUsername}
                    onChange={(e) => setRegUsername(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl text-sm outline-none"
                    style={{
                      background: 'var(--color-surface-tertiary)',
                      color: 'var(--color-text-primary)',
                      border: '1px solid var(--color-border)',
                    }}
                  />
                </div>
                <div>
                  <input
                    type="email"
                    placeholder="Email Address"
                    value={regEmail}
                    onChange={(e) => setRegEmail(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl text-sm outline-none"
                    style={{
                      background: 'var(--color-surface-tertiary)',
                      color: 'var(--color-text-primary)',
                      border: '1px solid var(--color-border)',
                    }}
                  />
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <div>
                  <input
                    type="tel"
                    placeholder="Phone Number (e.g. +91...)"
                    value={regPhone}
                    onChange={(e) => setRegPhone(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl text-sm outline-none"
                    style={{
                      background: 'var(--color-surface-tertiary)',
                      color: 'var(--color-text-primary)',
                      border: '1px solid var(--color-border)',
                    }}
                  />
                </div>
                <div>
                  <input
                    type="password"
                    placeholder="Password * (min 6 characters)"
                    required
                    value={regPassword}
                    onChange={(e) => setRegPassword(e.target.value)}
                    className="w-full px-4 py-2.5 rounded-xl text-sm outline-none"
                    style={{
                      background: 'var(--color-surface-tertiary)',
                      color: 'var(--color-text-primary)',
                      border: '1px solid var(--color-border)',
                    }}
                  />
                </div>
              </div>
            </div>

            {/* Step 3: Role-Specific Details */}
            {(regRole === 'field_officer' || regRole === 'state_controller') && (
              <div className="mb-6">
                <label className="block text-xs font-semibold uppercase tracking-wider mb-2 text-slate-300">
                  3. Officer Jurisdiction
                </label>
                <select
                  value={regState}
                  onChange={(e) => setRegState(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl text-sm outline-none"
                  style={{
                    background: 'var(--color-surface-tertiary)',
                    color: 'var(--color-text-primary)',
                    border: '1px solid var(--color-border)',
                  }}
                >
                  {INDIAN_STATES.map((st) => (
                    <option key={st} value={st} style={{ background: '#1e293b' }}>
                      {st} State / Division
                    </option>
                  ))}
                </select>
              </div>
            )}

            {(regRole === 'business' || regRole === 'ecommerce_partner') && (
              <div className="mb-6">
                <label className="block text-xs font-semibold uppercase tracking-wider mb-2 text-slate-300">
                  3. Organization Details
                </label>
                <input
                  type="text"
                  placeholder="Company / Marketplace / Enterprise Name (e.g. PureFoods India Pvt Ltd)"
                  value={regOrg}
                  onChange={(e) => setRegOrg(e.target.value)}
                  className="w-full px-4 py-2.5 rounded-xl text-sm outline-none"
                  style={{
                    background: 'var(--color-surface-tertiary)',
                    color: 'var(--color-text-primary)',
                    border: '1px solid var(--color-border)',
                  }}
                />
              </div>
            )}

            {error && (
              <p className="text-xs mb-4 text-red-400">
                {error}
              </p>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full py-3.5 rounded-xl text-sm font-semibold transition-all duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed shadow-lg"
              style={{
                background: `linear-gradient(135deg, ${selectedRoleConfig.color}, ${selectedRoleConfig.colorDark})`,
                color: '#fff',
                border: 'none',
              }}
            >
              {loading ? 'Creating Account & Initializing Dashboard...' : `Register as ${selectedRoleConfig.shortLabel} & Enter Dashboard`}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
