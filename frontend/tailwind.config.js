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
        // === Lane colors (role identification badges only) ===
        citizen: {
          DEFAULT: '#16a34a',
          light: '#dcfce7',
          dark: '#15803d',
        },
        officer: {
          DEFAULT: '#2563eb',
          light: '#dbeafe',
          dark: '#1d4ed8',
        },
        controller: {
          DEFAULT: '#9333ea',
          light: '#f3e8ff',
          dark: '#7e22ce',
        },
        national: {
          DEFAULT: '#4f46e5',
          light: '#e0e7ff',
          dark: '#4338ca',
        },
        business: {
          DEFAULT: '#0d9488',
          light: '#ccfbf1',
          dark: '#0f766e',
        },
        ecommerce: {
          DEFAULT: '#e11d48',
          light: '#ffe4e6',
          dark: '#be123c',
        },
        ruleadmin: {
          DEFAULT: '#ea580c',
          light: '#ffedd5',
          dark: '#c2410c',
        },
        enforcement: '#d97706',

        // === Primary accent (orange) ===
        accent: {
          DEFAULT: '#e8730c',
          hover: '#d4670a',
          subtle: '#fef3e7',
          muted: '#fde0c2',
        },

        // === Surfaces (light theme) ===
        surface: {
          primary: '#f8f8f8',
          secondary: '#ffffff',
          tertiary: '#f1f1f1',
          card: '#ffffff',
        },

        // === Text ===
        'text-primary': '#1a1a1a',
        'text-secondary': '#5a5a5a',
        'text-muted': '#9a9a9a',

        // === Status ===
        compliant: '#16a34a',
        'non-compliant': '#dc2626',
        'needs-review': '#d97706',
        pending: '#6b7280',

        // === Borders ===
        border: '#e5e5e5',
        'border-focus': 'rgba(232, 115, 12, 0.45)',
      },
      animation: {
        'fade-in': 'fadeIn 0.2s ease-out both',
        'slide-up': 'slideUp 0.25s ease-out both',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0', transform: 'translateY(6px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        slideUp: {
          '0%': { opacity: '0', transform: 'translateY(12px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
      },
    },
  },
  plugins: [],
};
