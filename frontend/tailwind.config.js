/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        canvas: '#F8F8F6',
        surface: '#FFFFFF',
        'surface-subtle': '#F2F2EF',
        line: '#E3E3DF',
        ink: '#20201E',
        muted: '#666661',
        faint: '#92928B',
        success: '#3F6B4E',
        'success-soft': '#EDF5EF',
        danger: '#A84539',
        'danger-soft': '#FBEFED',
        warm: {
          ivory: '#FAFAF7',
          cream: '#F7F4EE',
          surface: '#F1ECE3',
          border: '#E4DBCE',
        },
        text: {
          primary: '#20201E',
          secondary: '#5F5F59',
          muted: '#8B8B84',
        },
        accent: {
          DEFAULT: '#C66A1E',
          strong: '#9D4D12',
          soft: '#FAECDC',
          amber: '#D58429',
          terracotta: '#BE633A',
          copper: '#9B4F2F',
        },
        risk: {
          stable: '#5D794B',
          watch: '#C88B29',
          atrisk: '#BD6428',
          critical: '#A74436',
          rescue: '#762E2C',
        },
      },
      boxShadow: {
        soft: '0 12px 36px rgba(31, 31, 27, 0.06)',
        float: '0 18px 50px rgba(31, 31, 27, 0.10)',
      },
    },
  },
  plugins: [],
}
