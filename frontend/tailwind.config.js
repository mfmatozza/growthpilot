/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,ts,jsx,tsx}"],
  theme: {
    extend: {
      colors: {
        // Validated via the dataviz skill's CVD/contrast checker — see
        // docs/DECISIONS.md #18. `green`/`blue` are for marks, icons, and
        // active-state text (enough contrast on white); the `Soft`/`Tint`
        // steps are pastel and reserved for backgrounds/chips, never for a
        // thin chart mark or as a text color on white.
        brand: {
          green: "#0DA678",
          greenSoft: "#A7F3D0",
          greenTint: "#ECFDF6",
          blue: "#2A9BE0",
          blueSoft: "#BAE6FD",
          blueTint: "#EFF8FE",
        },
      },
    },
  },
  plugins: [],
};
