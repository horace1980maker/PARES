/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                nature: {
                    50: '#f2fcf5',
                    100: '#e1f8e8',
                    200: '#c3efd4',
                    300: '#94e0b5',
                    400: '#5cc992',
                    500: '#34af76',
                    600: '#258e5d',
                    700: '#20714c',
                    800: '#1d5a3f',
                    900: '#194a35',
                    950: '#0c281d',
                }
            }
        },
    },
    plugins: [],
}
