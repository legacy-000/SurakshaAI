import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./frontend/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./frontend/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./frontend/layouts/**/*.{js,ts,jsx,tsx,mdx}",
    "./frontend/components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
        // Custom branding colors for Suraksha AI (Karnataka Police Theme)
        police: {
          blue: {
            50: "#f0f4f8",
            100: "#d9e2ec",
            200: "#bcccdc",
            300: "#9fb3c8",
            400: "#829ab1",
            500: "#627d98",
            600: "#486581",
            700: "#334e68",
            800: "#243b53",
            900: "#102a43",
          },
          gold: {
            50: "#fdf8e2",
            100: "#fbeeb7",
            200: "#f9e48c",
            300: "#f7da61",
            400: "#f5d036",
            500: "#f3c60b",
            600: "#c29e09",
            700: "#927707",
            800: "#614f04",
            900: "#312802",
          }
        }
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: "0" },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: "0" },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
};

export default config;
