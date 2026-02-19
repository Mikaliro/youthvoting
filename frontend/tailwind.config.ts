import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./hooks/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        // Tier colors (match scripts/config.py TIERS)
        priority: "#1a237e",
        target: "#3949ab",
        watchlist: "#7986cb",
        "tier-low": "#c5cae9",
      },
    },
  },
  plugins: [],
};

export default config;
