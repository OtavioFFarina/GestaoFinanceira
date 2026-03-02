/** @type {import('tailwindcss').Config} */
module.exports = {
    content: [
        "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
        "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    ],
    theme: {
        extend: {
            colors: {
                avocado: {
                    DEFAULT: "#5CA34F",
                    light: "#7CC96E",
                    dark: "#3D7233",
                },
                surface: "#161B22",
                elevated: "#1E2530",
                "app-border": "#2A3140",
                "app-muted": "#8B949E",
                "app-bg": "#0D1117",
                "app-danger": "#F85149",
                "app-warning": "#D2A12A",
            },
            fontFamily: {
                sans: ["Inter", "system-ui", "sans-serif"],
            },
        },
    },
    plugins: [],
};
