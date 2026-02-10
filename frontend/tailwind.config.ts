import type { Config } from 'tailwindcss'

export default {
  content: ['./app/**/*.{ts,tsx}', './components/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        panel: '#121727',
        neon: '#58f5f0',
      },
      boxShadow: {
        glass: '0 12px 40px rgba(0,0,0,0.35)'
      }
    },
  },
  plugins: [],
} satisfies Config
