/**
 * Centralized configuration for frontend application
 * All environment variables are injected by Vite at build time
 */

// API Configuration
// API Configuration
export const API_URL = import.meta.env.VITE_API_URL;
export const HOST_IP = import.meta.env.VITE_HOST_IP;
export const FRONTEND_PORT = import.meta.env.VITE_FRONTEND_PORT;

// Derived URLs
export const BACKEND_URL = API_URL;
export const FRONTEND_URL = `http://${HOST_IP}:${FRONTEND_PORT}`;

// Export as default for convenience
export default {
    API_URL,
    HOST_IP,
    FRONTEND_PORT,
    BACKEND_URL,
    FRONTEND_URL
};
