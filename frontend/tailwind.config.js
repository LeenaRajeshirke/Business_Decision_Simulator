/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        base: {
          950: "#0a0b0d",
          900: "#111318",
          800: "#181b21",
          700: "#22262e",
          600: "#2c313b",
        },
        accent: {
          400: "#f2c14e",
          500: "#e0a92f",
          600: "#c68f1e",
        },
      },
    },
  },
  plugins: [],
};
