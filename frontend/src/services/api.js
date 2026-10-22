import axios from 'axios';

/**
 * Centralized API Client for the Intent-Aware Deception System REST API.
 */
const apiClient = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api',
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
  getDigitalTwin: (sessionId) => apiClient.get(`/sessions/${sessionId}/digital-twin`),
  getStoryboard: (sessionId) => apiClient.get(`/sessions/${sessionId}/storyboard`),
  simulateCounterfactual: (sessionId, excludedEventId) =>
    apiClient.post(`/sessions/${sessionId}/counterfactual`, { excluded_event_id: excludedEventId }),

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
  getModelRegistry: () => apiClient.get('/analytics/models'),
  getDriftReport: () => apiClient.get('/analytics/drift'),
  getCampaignGraph: () => apiClient.get('/analytics/campaign-graph'),
  testCommandDrift: (command) => apiClient.post('/analytics/drift/test-command', { command }),

  // Evidence-First AI Security Copilot & Research Laboratories
  queryCopilot: (data) => apiClient.post('/research/copilot/query', data),
  getIndustrialInvariants: () => apiClient.get('/research/industrial/invariants'),
  evaluateIndustrialTelemetry: (data) => apiClient.post('/research/industrial/evaluate', data),
  runAdversarialTest: (data) => apiClient.post('/research/industrial/adversarial-test', data),
  getVulnBenchmarks: () => apiClient.get('/research/vuln/benchmarks'),
  verifyVulnPayload: (data) => apiClient.post('/research/vuln/verify', data),

  // Controlled Financial Services Security Laboratory
  getFinancialAccounts: () => apiClient.get('/financial/accounts'),
  getFinancialIncidents: () => apiClient.get('/financial/incidents'),
  submitFinancialTransfer: (data) => apiClient.post('/financial/transfer', data),

  // Controlled AI Services & Agent Security Laboratory
  evaluatePromptInjection: (data) => apiClient.post('/ai-security/evaluate-prompt', data),
  evaluateMCPToolCall: (data) => apiClient.post('/ai-security/evaluate-tool-call', data),
  getRAGCanaryDocuments: () => apiClient.get('/ai-security/rag-canaries'),
  testRAGLeak: (data) => apiClient.post('/ai-security/test-rag-leak', data),
};

export default api;
