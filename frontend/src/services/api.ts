import axios from 'axios';

/**
 * Resolves the centralized API base URL:
 * 1. Checks VITE_API_URL or VITE_API_BASE_URL environment variable.
 * 2. In production (e.g. Vercel deployment), falls back to Render backend: https://labgap.onrender.com
 * 3. In local development (localhost / 127.0.0.1), falls back to: http://localhost:8000
 * 4. Strictly normalizes the path so /api/v1 is appended exactly once without duplication.
 */
export const getApiBaseUrl = (): string => {
  const envUrl = (import.meta as any).env?.VITE_API_URL || (import.meta as any).env?.VITE_API_BASE_URL;

  let rawUrl: string;
  if (envUrl && typeof envUrl === 'string' && envUrl.trim().length > 0) {
    rawUrl = envUrl.trim();
  } else if (
    import.meta.env.PROD ||
    (typeof window !== 'undefined' &&
      window.location.hostname !== 'localhost' &&
      window.location.hostname !== '127.0.0.1')
  ) {
    rawUrl = 'https://labgap.onrender.com';
  } else {
    rawUrl = 'http://localhost:8000';
  }

  // Remove trailing slashes
  rawUrl = rawUrl.replace(/\/+$/, '');

  // Ensure /api/v1 is appended, without duplication
  if (!rawUrl.endsWith('/api/v1')) {
    rawUrl = `${rawUrl}/api/v1`;
  }

  return rawUrl;
};

export const API_BASE_URL = getApiBaseUrl();

export const api = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor to attach JWT token
api.interceptors.request.use(
  (config) => {
    if (!config.baseURL) {
      config.baseURL = getApiBaseUrl();
    }
    const token = localStorage.getItem('labgap_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor for auth errors
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response && error.response.status === 401) {
      // Clear token on 401
      localStorage.removeItem('labgap_token');
      localStorage.removeItem('labgap_user');
      if (window.location.pathname !== '/login') {
        window.location.href = '/login';
      }
    }
    return Promise.reject(error);
  }
);
