/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,jsx}",
  ],
  theme: {
    extend: {
      colors: {
        'chat-bg': '#212121',
        'chat-surface': '#2f2f2f',
        'chat-input': '#424242',
        'chat-border': '#4a4a4a',
        'chat-text': '#e3e3e3',
        'chat-text-secondary': '#b4b4b4',
        'accent-blue': '#8ab4f8',
        'accent-purple': '#c58af9',
      },
      animation: {
        'pulse-slow': 'pulse 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
      }
    },
  },
  plugins: [],
}
