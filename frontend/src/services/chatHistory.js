import axios from 'axios';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Create a new chat session
 * @param {string} mode - "chat" or "report"
 * @param {string} title - Optional session title
 * @returns {Promise} New session object
 */
export const createSession = async (mode, title = null) => {
  try {
    const response = await api.post('/api/sessions', {
      mode,
      title,
      user_id: 'default_user'
    });
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Get all sessions for a user, optionally filtered by mode
 * @param {number} limit - Max number of sessions to return
 * @param {string} mode - Optional filter by mode ("chat" or "report")
 * @returns {Promise} Array of sessions
 */
export const getSessions = async (limit = 50, mode = null) => {
  try {
    const params = { user_id: 'default_user', limit };
    if (mode) {
      params.mode = mode;
    }
    const response = await api.get('/api/sessions', { params });
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Get a specific session with all messages
 * @param {string} sessionId - Session ID
 * @returns {Promise} Session with messages
 */
export const getSession = async (sessionId) => {
  try {
    const response = await api.get(`/api/sessions/${sessionId}`);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Add a message to a session
 * @param {string} sessionId - Session ID
 * @param {object} message - Message object {role, content, metadata}
 * @returns {Promise} Added message
 */
export const addMessage = async (sessionId, message) => {
  try {
    const response = await api.post(`/api/sessions/${sessionId}/messages`, message);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Update session details
 * @param {string} sessionId - Session ID
 * @param {object} updates - Updates object {title}
 * @returns {Promise} Success response
 */
export const updateSession = async (sessionId, updates) => {
  try {
    const response = await api.patch(`/api/sessions/${sessionId}`, updates);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Delete a session
 * @param {string} sessionId - Session ID
 * @returns {Promise} Success response
 */
export const deleteSession = async (sessionId) => {
  try {
    const response = await api.delete(`/api/sessions/${sessionId}`);
    return response.data;
  } catch (error) {
    throw handleApiError(error);
  }
};

/**
 * Clear all messages from a session
 * @param {string} sessionId - Session ID
 * @returns {Promise} Success response
 */
export const clearSessionMessages = async (sessionId) => {
  try {
    const response = await api.delete(`/api/sessions/${sessionId}/messages`);
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
    const detail = error.response.data?.detail || error.response.data;
    return new Error(
      typeof detail === 'string' ? detail : detail?.message || 'An error occurred'
    );
  } else if (error.request) {
    return new Error('Unable to connect to the server');
  } else {
    return new Error(error.message || 'An unexpected error occurred');
  }
};

export default api;
