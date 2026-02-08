/**
 * Centralized configuration for frontend application
 * All environment variables are injected by Vite at build time
 */

// API Configuration
export const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:9000';
export const HOST_IP = import.meta.env.VITE_HOST_IP || 'localhost';
export const FRONTEND_PORT = import.meta.env.VITE_FRONTEND_PORT || '9080';

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
