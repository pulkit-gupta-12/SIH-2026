/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'Segoe UI', 'system-ui', '-apple-system', 'sans-serif'],
      },
      colors: {
        // === Lane colors (matching approved flow diagram legend) ===
        citizen: {
          DEFAULT: '#16a34a',
          light: '#bbf7d0',
          dark: '#15803d',
        },
        officer: {
          DEFAULT: '#2563eb',
          light: '#bfdbfe',
          dark: '#1d4ed8',
        },
        controller: {
          DEFAULT: '#9333ea',
          light: '#e9d5ff',
          dark: '#7e22ce',
        },
        national: {
          DEFAULT: '#4f46e5',
          light: '#c7d2fe',
          dark: '#4338ca',
        },
        business: {
          DEFAULT: '#0d9488',
          light: '#ccfbf1',
          dark: '#0f766e',
        },
        ecommerce: {
          DEFAULT: '#e11d48',
          light: '#fecdd3',
          dark: '#be123c',
        },
        ruleadmin: {
          DEFAULT: '#ea580c',
          light: '#fed7aa',
          dark: '#c2410c',
        },
        enforcement: '#d97706',

        // === Surfaces (dark mode) ===
        surface: {
          primary: '#0f172a',
          secondary: '#1e293b',
          tertiary: '#334155',
          card: 'rgba(30, 41, 59, 0.8)',
          glass: 'rgba(30, 41, 59, 0.5)',
        },

        // === Text ===
        'text-primary': '#f1f5f9',
        'text-secondary': '#94a3b8',
        'text-muted': '#64748b',

        // === Status ===
        compliant: '#22c55e',
        'non-compliant': '#ef4444',
        'needs-review': '#f59e0b',
        pending: '#64748b',

        // === Borders ===
        border: 'rgba(148, 163, 184, 0.15)',
        'border-focus': 'rgba(99, 102, 241, 0.5)',
      },
      animation: {
        'fade-in': 'fadeIn 0.4s ease-out both',
        'slide-up': 'slideUp 0.5s ease-out both',
        'pulse-glow': 'pulseGlow 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(8px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        pulseGlow: {
          '0%, 100%': { boxShadow: '0 0 0 0 rgba(99, 102, 241, 0.3)' },
          '50%': { boxShadow: '0 0 20px 4px rgba(99, 102, 241, 0.15)' },
        },
      },
      backdropBlur: {
        xs: '2px',
      },
    },
  },
  plugins: [],
};
