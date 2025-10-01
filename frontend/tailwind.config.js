/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        base: {
          900: "#101319",
        },
        brand: {
          400: "#65A4EF",
          500: "#4781D6",
          600: "#1E59AF",
        },
        accent: {
          400: "#9AD5E2",
        },
      },
    },
  },
  plugins: [],
};
