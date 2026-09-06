/**
 * Login & Registration Page — role-based auth with demo user quick-login cards
 * and a full Create Account flow for any of the 7 roles.
 * Clean light theme with orange accent.
 */
import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '../../store/authStore';
import { authService } from '../../services/authService';
import type { RegisterData, AuthUser } from '../../services/authService';
import { ROLE_CONFIGS, ALL_ROLES } from '../../utils/roleConfig';
import type { UserRole } from '../../store/authStore';

// Demo credentials per role — matches seed_roles management command
const DEMO_USERS: Record<UserRole, { username: string; password: string; name: string; email: string }> = {
  citizen: {
    username: 'citizen_demo',
    password: 'demo1234',
    name: 'Priya Sharma (Citizen)',
    email: 'citizen@legalmetro.test',
  },
  field_officer: {
    username: 'officer_demo',
    password: 'demo1234',
    name: 'Rajesh Kumar (Inspector)',
    email: 'officer@legalmetro.test',
  },
  rule_admin: {
    username: 'ruleadmin_demo',
    password: 'demo1234',
    name: 'Sunil Verma (Rule Admin)',
    email: 'ruleadmin@legalmetro.test',
  },
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

  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [loadingRole, setLoadingRole] = useState<UserRole | null>(null);

  const selectedRoleConfig = ROLE_CONFIGS[regRole];

  // Handle Login
  const handleLogin = async (user: string, pass: string, role?: UserRole) => {
    setError('');
    setLoading(true);
    if (role) setLoadingRole(role);

    // Identify if this is a demo account (either clicked via card or typed manually)
    const matchedRole = role || (Object.keys(DEMO_USERS) as UserRole[]).find(
      (r) => DEMO_USERS[r].username.toLowerCase() === user.trim().toLowerCase()
    );

    try {
      // 1. Attempt real authentication with backend (with timeout)
      const loginPromise = authService.login({ username: user.trim(), password: pass });
      const timeoutPromise = new Promise<never>((_, reject) =>
        setTimeout(() => reject(new Error('Login timeout')), 3500)
      );

      const data = await Promise.race([loginPromise, timeoutPromise]);
      setAuth(data.user, data.access, data.refresh);

      // Navigate to the role's home
      const activeRole = (data.user.roles[0] || matchedRole || 'citizen') as UserRole;
      const config = ROLE_CONFIGS[activeRole];
      navigate(config?.homePath || '/');
    } catch (err: unknown) {
      // 2. If this is a demo user, guarantee instant one-click entry to dashboards!
      if (matchedRole && DEMO_USERS[matchedRole]) {
        const demo = DEMO_USERS[matchedRole];
        const demoUser: AuthUser = {
          id: matchedRole === 'citizen' ? 1 : matchedRole === 'field_officer' ? 2 : 3,
          username: demo.username,
          email: demo.email,
          name: demo.name,
          roles: [matchedRole],
        };
        setAuth(
          demoUser,
          `demo_access_${matchedRole}_${Date.now()}`,
          `demo_refresh_${matchedRole}_${Date.now()}`
        );
        const config = ROLE_CONFIGS[matchedRole];
        navigate(config?.homePath || '/');
        return;
      }

      // Non-demo credentials error handling
      const msg =
        err && typeof err === 'object' && 'response' in err
          ? (err as { response?: { data?: { detail?: string; error?: string } } }).response?.data?.detail ||
            (err as { response?: { data?: { detail?: string; error?: string } } }).response?.data?.error ||
            'Login failed. Please check your credentials.'
          : 'Network error — backend is not reachable.';
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
      state: regRole === 'field_officer' ? regState : undefined,
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

  const inputClasses = "w-full px-4 py-2.5 rounded-lg text-sm outline-none transition-all duration-200 bg-white/80 text-slate-800 border border-slate-200 focus:bg-white focus:border-orange-400 focus:ring-4 focus:ring-orange-400/10 placeholder:text-slate-400 font-medium";
  const inputClassesSmall = "w-full px-3 py-2 rounded-lg text-sm outline-none transition-all duration-200 bg-white/80 text-slate-800 border border-slate-200 focus:bg-white focus:border-orange-400 focus:ring-4 focus:ring-orange-400/10 placeholder:text-slate-400 font-medium";

  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-4 py-6 relative overflow-hidden bg-slate-50">
      {/* Premium ambient background */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <div className="absolute top-[-10%] left-[-10%] w-[50%] h-[50%] rounded-full bg-orange-100/50 blur-[120px]" />
        <div className="absolute bottom-[-10%] right-[-10%] w-[50%] h-[50%] rounded-full bg-blue-100/50 blur-[120px]" />
      </div>

      {/* Main container */}
      <div className="relative z-10 w-full max-w-3xl bg-white/60 backdrop-blur-2xl border border-white/60 shadow-[0_8px_40px_rgb(0,0,0,0.04)] p-6 md:p-8 rounded-2xl animate-fade-in my-auto">
        {/* Header */}
        <div className="text-center mb-6">
          <div className="inline-flex items-center justify-center w-12 h-12 rounded-xl mb-4 shadow-sm border border-orange-100 bg-gradient-to-br from-orange-50 to-orange-100/50 text-2xl text-orange-600">
            ⚖
          </div>
          <h1 className="text-2xl md:text-3xl font-bold mb-1.5 text-slate-800 tracking-tight">
            Legal Metrology Platform
          </h1>
          <p className="text-xs md:text-sm text-slate-500 font-medium">
            National platform for transparent, tech-driven trade enforcement
          </p>
        </div>

        {/* Tab Switcher */}
        <div className="flex justify-center mb-6">
          <div className="inline-flex p-1 rounded-lg bg-slate-100/80 backdrop-blur-sm border border-slate-200/60 shadow-inner">
            <button
              onClick={() => {
                setActiveTab('login');
                setError('');
              }}
              className={`px-6 py-2 rounded-md text-xs font-semibold transition-all duration-200 cursor-pointer ${
                activeTab === 'login'
                  ? 'bg-white text-slate-800 shadow-sm ring-1 ring-slate-900/5'
                  : 'text-slate-500 hover:text-slate-700'
              }`}
            >
              Sign In
            </button>
            <button
              onClick={() => {
                setActiveTab('register');
                setError('');
              }}
              className={`px-6 py-2 rounded-md text-xs font-semibold transition-all duration-200 cursor-pointer ${
                activeTab === 'register'
                  ? 'bg-white text-slate-800 shadow-sm ring-1 ring-slate-900/5'
                  : 'text-slate-500 hover:text-slate-700'
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
                  className={inputClasses}
                />
                <input
                  id="login-password"
                  type="password"
                  placeholder="Password"
                  value={loginPassword}
                  onChange={(e) => setLoginPassword(e.target.value)}
                  onKeyDown={(e) => e.key === 'Enter' && handleLogin(loginUsername, loginPassword)}
                  className={inputClasses}
                />
                {error && (
                  <p className="text-xs px-1 text-red-600">
                    {error}
                  </p>
                )}
                <button
                  id="login-submit"
                  onClick={() => handleLogin(loginUsername, loginPassword)}
                  disabled={loading || !loginUsername || !loginPassword}
                  className="w-full py-2.5 rounded-lg text-sm font-bold transition-all duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed text-white shadow-md hover:shadow-lg hover:-translate-y-0.5 active:translate-y-0 bg-gradient-to-r from-orange-600 to-orange-500"
                >
                  {loading && !loadingRole ? 'Signing in...' : 'Sign in to Dashboard'}
                </button>
              </div>
            </div>

            {/* Divider */}
            <div className="flex items-center gap-4 mb-5 mt-6 max-w-xl mx-auto">
              <div className="flex-1 h-px bg-gradient-to-r from-transparent via-slate-200 to-transparent" />
              <span className="text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                Demo Accounts
              </span>
              <div className="flex-1 h-px bg-gradient-to-r from-transparent via-slate-200 to-transparent" />
            </div>

            {/* Role selector grid */}
            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-4 gap-3">
              {ALL_ROLES.map((role) => {
                const config = ROLE_CONFIGS[role];
                const demo = DEMO_USERS[role];
                const isLoading = loadingRole === role;

                return (
                  <button
                    key={role}
                    id={`demo-login-${role}`}
                    onClick={() => handleLogin(demo.username, demo.password, role)}
                    disabled={loading}
                    className="group flex flex-col items-center gap-2 p-3.5 rounded-xl transition-all duration-200 cursor-pointer disabled:opacity-50 text-center bg-white/50 hover:bg-white border border-slate-200/60 hover:border-orange-200 hover:shadow-[0_4px_12px_rgb(0,0,0,0.04)] hover:-translate-y-0.5"
                  >
                    <span className="w-10 h-10 rounded-xl flex items-center justify-center text-xl bg-slate-50 group-hover:bg-orange-50 group-hover:scale-110 transition-transform duration-200 ring-1 ring-slate-100 group-hover:ring-orange-100">
                      {config.icon}
                    </span>
                    <div>
                      <p className="text-xs font-bold text-slate-700 group-hover:text-orange-700 transition-colors">
                        {config.shortLabel}
                      </p>
                      <p className="text-[10px] mt-0.5 leading-tight text-slate-500 group-hover:text-slate-600 line-clamp-2">
                        {isLoading ? 'Connecting...' : config.description}
                      </p>
                    </div>
                  </button>
                );
              })}
            </div>

            {/* Footer */}
            <p className="text-center mt-5 text-[10px] text-slate-400">
              Demo credentials: username shown on card &middot; password:{' '}
              <code className="px-1 py-0.5 rounded bg-slate-100 text-slate-500 border border-slate-200">
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
              <label className="block text-xs font-semibold mb-2 text-[var(--color-text-secondary)]">
                1. Select your dashboard role
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
                      className={`flex flex-col items-center gap-1.5 p-3 rounded-xl transition-all duration-200 cursor-pointer text-center border ${
                        isSelected
                          ? 'bg-orange-50/50 border-orange-300 shadow-sm ring-1 ring-orange-200'
                          : 'bg-white/50 border-slate-200 hover:bg-white hover:border-slate-300'
                      }`}
                    >
                      <span className={`text-xl transition-transform duration-200 ${isSelected ? 'scale-110' : ''}`}>{config.icon}</span>
                      <span className={`text-[10px] font-bold ${isSelected ? 'text-orange-700' : 'text-slate-600'}`}>
                        {config.shortLabel}
                      </span>
                    </button>
                  );
                })}
              </div>
              <p className="text-xs mt-2 text-[var(--color-text-muted)] flex items-center gap-1.5">
                <span className="font-medium text-[var(--color-text-primary)]">{selectedRoleConfig.label}:</span>
                {selectedRoleConfig.description}
              </p>
            </div>

            {/* Step 2: Personal & Account Information */}
            <div className="mb-6">
              <label className="block text-xs font-semibold mb-2 text-[var(--color-text-secondary)]">
                2. Account credentials
              </label>
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
                <input
                  type="text"
                  placeholder="First Name"
                  value={regFirstName}
                  onChange={(e) => setRegFirstName(e.target.value)}
                  className={inputClassesSmall}
                />
                <input
                  type="text"
                  placeholder="Last Name"
                  value={regLastName}
                  onChange={(e) => setRegLastName(e.target.value)}
                  className={inputClassesSmall}
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 mb-3">
                <input
                  type="text"
                  placeholder="Username *"
                  required
                  value={regUsername}
                  onChange={(e) => setRegUsername(e.target.value)}
                  className={inputClassesSmall}
                />
                <input
                  type="email"
                  placeholder="Email Address"
                  value={regEmail}
                  onChange={(e) => setRegEmail(e.target.value)}
                  className={inputClassesSmall}
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                <input
                  type="tel"
                  placeholder="Phone Number (e.g. +91...)"
                  value={regPhone}
                  onChange={(e) => setRegPhone(e.target.value)}
                  className={inputClassesSmall}
                />
                <input
                  type="password"
                  placeholder="Password * (min 6 characters)"
                  required
                  value={regPassword}
                  onChange={(e) => setRegPassword(e.target.value)}
                  className={inputClassesSmall}
                />
              </div>
            </div>

            {/* Step 3: Role-Specific Details */}
            {(regRole === 'field_officer') && (
              <div className="mb-6">
                <label className="block text-xs font-semibold mb-2 text-[var(--color-text-secondary)]">
                  3. Officer jurisdiction
                </label>
                <select
                  value={regState}
                  onChange={(e) => setRegState(e.target.value)}
                  className={inputClassesSmall}
                >
                  {INDIAN_STATES.map((st) => (
                    <option key={st} value={st}>
                      {st} State / Division
                    </option>
                  ))}
                </select>
              </div>
            )}



            {error && (
              <p className="text-xs mb-4 text-red-600">
                {error}
              </p>
            )}

            {/* Submit Button */}
            <button
              type="submit"
              disabled={loading}
              className="w-full mt-2 py-3 rounded-lg text-sm font-bold transition-all duration-200 cursor-pointer disabled:opacity-50 disabled:cursor-not-allowed text-white shadow-md hover:shadow-lg hover:-translate-y-0.5 active:translate-y-0 bg-gradient-to-r from-orange-600 to-orange-500"
            >
              {loading ? 'Creating account...' : `Create ${selectedRoleConfig.shortLabel} Account`}
            </button>
          </form>
        )}
      </div>
    </div>
  );
}
