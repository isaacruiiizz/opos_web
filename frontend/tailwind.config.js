/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{vue,js}'],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        primary: '#2563EB',
        surface: {
          light: '#FFFFFF',
          dark: '#1E1E2E',
        }
      }
    }
  },
  plugins: [],
}

