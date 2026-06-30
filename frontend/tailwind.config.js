/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#0a0b10",
        card: "#12131a",
        primary: "#6366f1",
        secondary: "#a855f7",
        accent: "#f43f5e",
        text: "#f8fafc",
        muted: "#94a3b8",
        border: "#1e293b"
      }
    },
  },
  plugins: [],
}
