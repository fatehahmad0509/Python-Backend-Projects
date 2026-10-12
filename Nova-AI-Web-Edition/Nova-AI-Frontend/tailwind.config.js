/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  darkMode: "class",
  theme: {
    extend: {
      colors: {
        bg: {
          main: "rgb(var(--color-bg-main) / <alpha-value>)",
          card: "rgb(var(--color-bg-card) / <alpha-value>)",
          sidebar: "rgb(var(--color-bg-sidebar) / <alpha-value>)",
          aiMessage: "rgb(var(--color-bg-ai-message) / <alpha-value>)",
        },
        text: {
          heading: "rgb(var(--color-text-heading) / <alpha-value>)",
          body: "rgb(var(--color-text-body) / <alpha-value>)",
          secondary: "rgb(var(--color-text-secondary) / <alpha-value>)",
        },
        accent: {
          DEFAULT: "rgb(var(--color-accent) / <alpha-value>)",
          light: "rgb(var(--color-accent-light) / <alpha-value>)",
          dark: "rgb(var(--color-accent-dark) / <alpha-value>)",
        },
        border: {
          DEFAULT: "rgb(var(--color-border) / <alpha-value>)",
        },
        hover: {
          DEFAULT: "rgb(var(--color-hover) / <alpha-value>)",
        },
        danger: "rgb(var(--color-danger) / <alpha-value>)",
        success: "rgb(var(--color-success) / <alpha-value>)",
      },
      backgroundImage: {
        "user-gradient": "linear-gradient(135deg, #7C3AED 0%, #8B5CF6 100%)",
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "system-ui", "sans-serif"],
      },
      keyframes: {
        pulseDot: {
          "0%, 100%": { opacity: 0.4, transform: "scale(0.8)" },
          "50%": { opacity: 1, transform: "scale(1)" },
        },
        slideInRight: {
          from: { opacity: 0, transform: "translateX(16px)" },
          to: { opacity: 1, transform: "translateX(0)" },
        },
        fadeSlideUp: {
          from: { opacity: 0, transform: "translateY(12px)" },
          to: { opacity: 1, transform: "translateY(0)" },
        },
      },
      animation: {
        pulseDot: "pulseDot 1.4s infinite",
        slideInRight: "slideInRight 0.2s ease-out",
        fadeSlideUp: "fadeSlideUp 0.3s ease-out",
      },
    },
  },
  plugins: [],
};
