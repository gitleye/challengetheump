/** @type {import('tailwindcss').Config} */
export default {
  content: ['./src/**/*.{astro,html,js,jsx,md,mdx,svelte,ts,tsx,vue}'],
  theme: {
    extend: {
      // Design tokens will be added in the brand prompt (03-brand-design.md)
      colors: {
        // MLB-inspired palette — to be refined in brand prompt
        brand: {
          navy: '#002D72',
          red: '#D50032',
          cream: '#F5F0E8',
          slate: '#4A5568',
          gold: '#C9A84C',
        },
      },
      fontFamily: {
        // Will be replaced with custom fonts in brand prompt
        display: ['Georgia', 'serif'],
        mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
      },
    },
  },
  plugins: [],
};
