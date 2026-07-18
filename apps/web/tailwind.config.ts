import type { Config } from "tailwindcss";

// Warm residential palette — deep green + cream + charcoal (not SaaS blue).
const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        pine: {
          50: "#f2f6f3",
          100: "#dfe9e1",
          300: "#9dbda6",
          500: "#4d7a5c",
          700: "#2c5140",
          800: "#1f3d2f",
          900: "#152b21",
        },
        cream: {
          DEFAULT: "#f8f4ec",
          dark: "#efe8da",
        },
        charcoal: {
          DEFAULT: "#26241f",
          light: "#4a463e",
        },
        brass: "#b08d3f",
      },
      fontFamily: {
        display: ["Georgia", "Cambria", "serif"],
        body: ["-apple-system", "Segoe UI", "Helvetica Neue", "Arial", "sans-serif"],
      },
    },
  },
  plugins: [],
};

export default config;
