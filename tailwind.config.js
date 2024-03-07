/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "src/chapter_sync/web/templates/**/*.html",
    "./node_modules/flowbite/**/*.js",
  ],
  theme: {
    extend: {},
  },
  plugins: [require("flowbite/plugin"), require("flowbite-typography")],
};
