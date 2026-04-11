/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Core backgrounds
        void:   '#0D0D0D',
        'void-1': '#111111',
        'void-2': '#161616',
        'void-3': '#1C1C1C',
        // Legacy navy (kept for Dashboard + other pages)
        navy: {
          950: '#0D0D2B',
          900: '#1A1A40',
          800: '#1E1E50',
          700: '#252560',
          600: '#2E2E7A',
        },
        // Electric mint accent
        mint: {
          DEFAULT: '#16A34A',
          dim:     '#15803D',
          glow:    '#4ADE80',
          muted:   'rgba(22,163,74,0.12)',
        },
        // Warm sand — product card bg
        sand: {
          DEFAULT: '#F8FAF7',
          dark:    '#EDE6DC',
          light:   '#FFFFFF',
        },
        // Legacy accent (kept for compatibility)
        accent: {
          green: '#00FFAB',
          glow:  '#00FFD1',
          dim:   '#00CC88',
        },
        // Amber rim
        amber: {
          rim:  '#C97A2A',
          glow: 'rgba(201,122,42,0.25)',
        },
        warn: {
          amber: '#FFB800',
          red:   '#FF4545',
        },
      },
      fontFamily: {
        sans:     ['Inter', 'system-ui', 'sans-serif'],
        mono:     ['JetBrains Mono', 'monospace'],
        display:  ['Inter', 'system-ui', 'sans-serif'],
      },
      fontSize: {
        '2xs': '0.65rem',
      },
      keyframes: {
        pricePulse: {
          '0%, 100%': { boxShadow: '0 0 0px #16A34A' },
          '50%':      { boxShadow: '0 0 14px 4px #16A34A' },
        },
        mintPulse: {
          '0%, 100%': { opacity: '1', transform: 'scale(1)' },
          '50%':      { opacity: '0.4', transform: 'scale(1.5)' },
        },
        'fade-in': {
          from: { opacity: '0', transform: 'translateY(8px)' },
          to:   { opacity: '1', transform: 'translateY(0)' },
        },
        shimmer: {
          '0%':   { backgroundPosition: '-200% 0' },
          '100%': { backgroundPosition:  '200% 0' },
        },
        ticker: {
          '0%':   { transform: 'translateX(0)' },
          '100%': { transform: 'translateX(-50%)' },
        },
      },
      animation: {
        pricePulse:  'pricePulse 1.2s ease-in-out 2',
        mintPulse:   'mintPulse 2s ease-in-out infinite',
        'fade-in':   'fade-in 0.4s ease-out forwards',
        shimmer:     'shimmer 1.6s linear infinite',
        ticker:      'ticker 28s linear infinite',
      },
      backdropBlur: {
        xs: '2px',
      },
      boxShadow: {
        'amber-rim': '0 0 0 1px rgba(201,122,42,0.35), 0 8px 32px rgba(201,122,42,0.12), inset 0 1px 0 rgba(255,255,255,0.06)',
        'mint-glow': '0 0 24px rgba(22,163,74,0.18)',
        'card-float':'0 24px 64px rgba(0,0,0,0.6)',
      },
    },
  },
  plugins: [],
}
