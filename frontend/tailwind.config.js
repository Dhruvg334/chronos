/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: '#F7F3EC',
        surface: '#FFFFFF',
        'surface-subtle': '#FBF8F2',
        line: '#E5DDD2',
        ink: '#27221D',
        muted: '#6B6259',
        faint: '#93887D',
        success: '#537047',
        'success-soft': '#EEF4EA',
        danger: '#A94438',
        'danger-soft': '#FAEEEC',
        warm: {
          ivory: '#FAF6EF',
          cream: '#FFF9F0',
          surface: '#F4EDE3',
          border: '#E7DCCB',
        },
        text: {
          primary: '#211B16',
          secondary: '#5E5147',
          muted: '#8A7C70',
        },
        accent: {
          DEFAULT: '#C97928',
          strong: '#9E581E',
          soft: '#F8E9D6',
          amber: '#D88A21',
          terracotta: '#C96F45',
          copper: '#9E4F2F',
        },
        risk: {
          stable: '#6F8A4D',
          watch: '#D89B2B',
          atrisk: '#C86A2D',
          critical: '#A63A2E',
          rescue: '#6F1D1B',
        },
      },
      boxShadow: { soft: '0 8px 24px rgba(54, 42, 30, 0.08)' },
    },
  },
  plugins: [],
}
