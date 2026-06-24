/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
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
    },
  },
  plugins: [],
}
