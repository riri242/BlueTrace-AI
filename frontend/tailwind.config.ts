import type { Config } from "tailwindcss";

const config = {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: [
          "Inter",
          "ui-sans-serif",
          "system-ui",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "sans-serif"
        ]
      },
      colors: {
        ocean: {
          50: "#f2f9fd",
          100: "#e4f2f8",
          500: "#1f8ab5",
          600: "#146f94",
          700: "#105a78"
        },
        research: {
          ink: "#102033",
          muted: "#5d6f82",
          line: "#d8e5ee"
        }
      },
      boxShadow: {
        research: "0 24px 80px -36px rgba(16, 32, 51, 0.35)"
      }
    }
  },
  plugins: []
} satisfies Config;

export default config;

