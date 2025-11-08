import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120000, // 2 minutes for complex queries
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Send a chat query to the backend
 * @param {string} query - The user's question
 * @returns {Promise} Response with chat result
 */
export const sendChatQuery = async (query) => {
  try {
    const response = await api.post('/api/chat', null, {
      params: { query }
    });
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Send a think query to the backend (comprehensive analysis)
 * @param {string} query - The user's question
 * @param {boolean} verbose - Include detailed execution info
 * @returns {Promise} Response with analysis result
 */
export const sendThinkQuery = async (query, verbose = false) => {
  try {
    const response = await api.post('/api/think', null, {
      params: { query, verbose }
    });
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

// Alias for backward compatibility
export const sendReportQuery = sendThinkQuery;

/**
 * Check API health status
 * @returns {Promise} Health check response
 */
export const checkHealth = async () => {
  try {
    const response = await api.get('/api/health');
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Handle API errors consistently
 * @param {Error} error - The error object
 * @returns {Error} Formatted error
 */
const handleApiError = (error) => {
  if (error.response) {
    // Server responded with error
    const detail = error.response.data?.detail || error.response.data;
    return new Error(
      detail?.error || detail?.message || 'An error occurred processing your request'
    );
  } else if (error.request) {
    // Request made but no response
    return new Error('Unable to connect to the server. Please check if the API is running.');
  } else {
    // Something else happened
    return new Error(error.message || 'An unexpected error occurred');
  }
};

export default api;
