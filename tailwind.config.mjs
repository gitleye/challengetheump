/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,ts,tsx}'],
  darkMode: 'class',
  theme: {
    extend: {
      // ---- Colors -------------------------------------------------------
      colors: {
        // Dark-mode surfaces (CSS vars drive the actual theming)
        base: 'rgb(var(--color-base) / <alpha-value>)',
        surface: 'rgb(var(--color-surface) / <alpha-value>)',
        elevated: 'rgb(var(--color-elevated) / <alpha-value>)',
        border: 'rgb(var(--color-border) / <alpha-value>)',

        // Text
        'text-primary': 'rgb(var(--color-text-primary) / <alpha-value>)',
        'text-secondary': 'rgb(var(--color-text-secondary) / <alpha-value>)',
        'text-tertiary': 'rgb(var(--color-text-tertiary) / <alpha-value>)',

        // Accent — Hawk-Eye strike-zone yellow-green
        accent: {
          DEFAULT: '#D4FF3D',
          muted: 'rgb(212 255 61 / 0.6)',
          subtle: 'rgb(212 255 61 / 0.1)',
        },

        // Semantic
        success: '#22C55E',
        danger: '#EF4444',
        warning: '#F59E0B',
      },

      // ---- Typography ---------------------------------------------------
      fontFamily: {
        display: ['Space Grotesk', 'system-ui', 'sans-serif'],
        body: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },

      fontSize: {
        'display-xl': ['72px', { lineHeight: '1.05', letterSpacing: '-0.04em', fontWeight: '900' }],
        'display-lg': ['56px', { lineHeight: '1.07', letterSpacing: '-0.03em', fontWeight: '800' }],
        'display-md': ['40px', { lineHeight: '1.1', letterSpacing: '-0.02em', fontWeight: '800' }],
        h1: ['32px', { lineHeight: '1.2', letterSpacing: '-0.02em', fontWeight: '700' }],
        h2: ['24px', { lineHeight: '1.25', letterSpacing: '-0.01em', fontWeight: '700' }],
        h3: ['20px', { lineHeight: '1.3', fontWeight: '600' }],
        'body-lg': ['18px', { lineHeight: '1.6' }],
        body: ['16px', { lineHeight: '1.6' }],
        'body-sm': ['14px', { lineHeight: '1.5' }],
        caption: ['12px', { lineHeight: '1.4', letterSpacing: '0.06em', fontWeight: '500' }],
        'stat-xl': ['64px', { lineHeight: '1', fontWeight: '700', fontVariantNumeric: 'tabular-nums' }],
        'stat-lg': ['40px', { lineHeight: '1.05', fontWeight: '700', fontVariantNumeric: 'tabular-nums' }],
        stat: ['24px', { lineHeight: '1.1', fontWeight: '600', fontVariantNumeric: 'tabular-nums' }],
      },

      // ---- Border radius -----------------------------------------------
      borderRadius: {
        sm: '4px',
        md: '8px',
        lg: '12px',
        xl: '16px',
        '2xl': '20px',
      },

      // ---- Shadows ------------------------------------------------------
      boxShadow: {
        'surface': '0 1px 3px rgb(0 0 0 / 0.4), 0 1px 2px rgb(0 0 0 / 0.3)',
        'elevated': '0 4px 16px rgb(0 0 0 / 0.5), 0 2px 4px rgb(0 0 0 / 0.3)',
        'accent': '0 0 0 1px #D4FF3D, 0 0 20px rgb(212 255 61 / 0.2)',
        'accent-sm': '0 0 0 1px rgb(212 255 61 / 0.4), 0 0 8px rgb(212 255 61 / 0.15)',
        'glow': '0 0 30px rgb(212 255 61 / 0.15)',
      },

      // ---- Transitions --------------------------------------------------
      transitionTimingFunction: {
        DEFAULT: 'cubic-bezier(0.4, 0, 0.2, 1)',
      },
      transitionDuration: {
        DEFAULT: '200ms',
      },

      // ---- Spacing tweaks -----------------------------------------------
      spacing: {
        18: '4.5rem',
        22: '5.5rem',
      },

      // ---- Animation ----------------------------------------------------
      keyframes: {
        'fade-in': {
          from: { opacity: '0', transform: 'translateY(6px)' },
          to: { opacity: '1', transform: 'translateY(0)' },
        },
        'count-up': {
          from: { opacity: '0' },
          to: { opacity: '1' },
        },
        'draw': {
          from: { strokeDashoffset: 'var(--path-length, 1000)' },
          to: { strokeDashoffset: '0' },
        },
      },
      animation: {
        'fade-in': 'fade-in 0.4s ease-out both',
        'fade-in-delay': 'fade-in 0.4s ease-out 0.1s both',
      },
    },
  },
  plugins: [],
};
