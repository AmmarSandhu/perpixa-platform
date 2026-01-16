/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          blue: "#22B5F6",
          mid: "#5B8EF5",
          purple: "#8B5CF6",
        },
        text: {
          primary: "#0F172A",
          secondary: "#475569",
          muted: "#64748B",
        },
        border: {
          subtle: "#E2E8F0",
        },
      },
    },
  },
  plugins: [],
};
