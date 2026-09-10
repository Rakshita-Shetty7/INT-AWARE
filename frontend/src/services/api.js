import axios from 'axios';

/**
 * Centralized API Client for the Intent-Aware Deception System REST API.
 */
const apiClient = axios.create({
  baseURL: '/api',
  timeout: 30000, // 30s timeout for AI analysis calls
  headers: {
    'Content-Type': 'application/json',
  },
});

// Response interceptor for unwrapping response data and error handling
apiClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const errorMsg =
      error.response?.data?.detail ||
      error.response?.data?.message ||
      error.message ||
      'An unexpected error occurred while communicating with the deception API.';
    return Promise.reject(new Error(errorMsg));
  }
);

export const api = {
  // System Health
  getHealth: () => apiClient.get('/health'),

  // Executive Dashboard Stats
  getDashboardStats: () => apiClient.get('/dashboard/stats'),

  // Telemetry Events
  getEvents: (params = {}) => apiClient.get('/events', { params }),
  getRecentEvents: (limit = 20) => apiClient.get('/events/recent', { params: { limit } }),
  getEvent: (eventId) => apiClient.get(`/events/${eventId}`),

  // Attacker Sessions
  getSessions: (params = {}) => apiClient.get('/sessions', { params }),
  getSession: (sessionId) => apiClient.get(`/sessions/${sessionId}`),
  analyzeSession: (sessionId) => apiClient.post(`/sessions/${sessionId}/analyze`),
  getSessionMitre: (sessionId) => apiClient.get(`/sessions/${sessionId}/mitre`),

  // Attacker Profiles
  getAttackers: (params = {}) => apiClient.get('/attackers', { params }),
  getAttacker: (sourceIp) => apiClient.get(`/attackers/${sourceIp}`),

  // Threat Alerts
  getAlerts: (params = {}) => apiClient.get('/alerts', { params }),

  // Security Analytics & Trends
  getIntentAnalytics: () => apiClient.get('/analytics/intents'),
  getSeverityAnalytics: () => apiClient.get('/analytics/severity'),
  getTimelineAnalytics: () => apiClient.get('/analytics/timeline'),
  getStageAnalytics: () => apiClient.get('/analytics/stages'),
  getRiskDistribution: () => apiClient.get('/analytics/risk-distribution'),
  getRiskHeatmap: () => apiClient.get('/analytics/heatmap'),
};

export default api;
