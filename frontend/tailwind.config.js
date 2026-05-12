/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        janneau: {
          teal:      "#009BAD",
          "teal-dark": "#007A8A",
          "teal-light": "#E0F5F7",
          red:       "#E31E24",
          dark:      "#1A2B3C",
        },
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
      },
    },
  },
  plugins: [],
};
