import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./features/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        background: "#06090e",
        foreground: "#f1f5f9",
        card: "#0b111a",
        cardBorder: "#1e293b",
        maritime: {
          dark: "#050b14",
          panel: "#0c1524",
          border: "#1b2c45",
          cyan: "#0ea5e9",
          teal: "#14b8a6",
          amber: "#f59e0b",
          coral: "#f43f5e",
          green: "#10b981",
        },
      },
    },
  },
  plugins: [],
};
export default config;
