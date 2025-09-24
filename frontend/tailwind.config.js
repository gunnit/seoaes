/** @type {import('tailwindcss').Config} */
const path = require('path');
const fs = require('fs');

// Determine the correct base path
let basePath = __dirname;

// Log for debugging on Render
console.log('[Tailwind] Current directory:', process.cwd());
console.log('[Tailwind] Config directory:', __dirname);

module.exports = {
  content: [
    // Relative paths (work when building from frontend dir)
    './app/**/*.{js,ts,jsx,tsx,mdx}',
    './pages/**/*.{js,ts,jsx,tsx,mdx}',
    './components/**/*.{js,ts,jsx,tsx,mdx}',
    './src/**/*.{js,ts,jsx,tsx,mdx}',

    // Absolute paths (work from any directory)
    path.join(basePath, './app/**/*.{js,ts,jsx,tsx,mdx}'),
    path.join(basePath, './pages/**/*.{js,ts,jsx,tsx,mdx}'),
    path.join(basePath, './components/**/*.{js,ts,jsx,tsx,mdx}'),
    path.join(basePath, './src/**/*.{js,ts,jsx,tsx,mdx}'),

    // Explicit file paths to ensure critical files are included
    path.join(basePath, './app/page.tsx'),
    path.join(basePath, './app/layout.tsx'),
    path.join(basePath, './app/providers.tsx'),
    path.join(basePath, './app/analyze/[id]/page.tsx'),

    // Alternative paths in case we're building from root
    './frontend/app/**/*.{js,ts,jsx,tsx,mdx}',
    './frontend/pages/**/*.{js,ts,jsx,tsx,mdx}',
    './frontend/components/**/*.{js,ts,jsx,tsx,mdx}',
    './frontend/src/**/*.{js,ts,jsx,tsx,mdx}',
  ],
  // Important: Do not purge CSS in production
  safelist: [
    { pattern: /^(bg|text|border)-/ },
    { pattern: /^(w|h)-/ },
    { pattern: /^(m|p)(t|r|b|l|x|y)?-/ },
    { pattern: /^flex/ },
    { pattern: /^grid/ },
    { pattern: /^gap-/ },
    { pattern: /^space-/ },
    { pattern: /^rounded/ },
    { pattern: /^shadow/ },
    { pattern: /^opacity-/ },
    { pattern: /^transition/ },
    { pattern: /^duration-/ },
    { pattern: /^ease-/ },
    { pattern: /^font-/ },
    { pattern: /^text-/ },
    { pattern: /^leading-/ },
    { pattern: /^tracking-/ },
    { pattern: /^min-/ },
    { pattern: /^max-/ },
    { pattern: /^hover:/ },
    { pattern: /^focus:/ },
    { pattern: /^active:/ },
    { pattern: /^disabled:/ },
    { pattern: /^group-hover:/ },
    'container',
    'mx-auto',
    'gradient-text',
    'btn-primary',
    'btn-secondary',
    'card',
    'input-field',
    'animate-pulse-slow',
    'glass-effect',
  ],
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          100: '#dbeafe',
          200: '#bfdbfe',
          300: '#93c5fd',
          400: '#60a5fa',
          500: '#3b82f6',
          600: '#2563eb',
          700: '#1d4ed8',
          800: '#1e40af',
          900: '#1e3a8a',
        },
        success: {
          50: '#f0fdf4',
          100: '#dcfce7',
          200: '#bbf7d0',
          300: '#86efac',
          400: '#4ade80',
          500: '#22c55e',
          600: '#16a34a',
          700: '#15803d',
          800: '#166534',
          900: '#14532d',
        },
        danger: {
          50: '#fef2f2',
          100: '#fee2e2',
          200: '#fecaca',
          300: '#fca5a5',
          400: '#f87171',
          500: '#ef4444',
          600: '#dc2626',
          700: '#b91c1c',
          800: '#991b1b',
          900: '#7f1d1d',
        },
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'sans-serif'],
      },
      animation: {
        'pulse-slow': 'pulse 3s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'fade-in': 'fadeIn 0.5s ease-in-out',
        'slide-up': 'slideUp 0.3s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        slideUp: {
          '0%': { transform: 'translateY(10px)', opacity: '0' },
          '100%': { transform: 'translateY(0)', opacity: '1' },
        },
      },
    },
  },
  plugins: [],
};