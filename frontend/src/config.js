const config = {
    API_URL: import.meta.env.VITE_API_URL || 'http://localhost:8001',
    CARTO_API_KEY: import.meta.env.VITE_CARTO_API_KEY || ''
};

export default config;
