import axios from 'axios';
import { API_URL } from './config';

const api = axios.create({
  baseURL: API_URL,
});

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

export const login = async (email) => {
  const response = await api.post('/auth/dev-login', { email });
  localStorage.setItem('token', response.data.access_token);
  return response.data;
};

export const checkAuth = async () => {
  const response = await api.get('/auth/me');
  return response.data;
};

export const getSettings = async () => {
  const response = await api.get('/settings');
  return response.data;
};

export const updateSettings = async (apiKey) => {
  const response = await api.put('/settings', { openrouter_api_key: apiKey });
  return response.data;
};

export const getHistory = async () => {
  const response = await api.get('/history');
  return response.data;
};

export const getConversation = async (id) => {
  const response = await api.get(`/history/${id}`);
  return response.data;
};

export const fetchModels = async () => {
  const response = await api.get('/models');
  return response.data;
};

export const getOpenRouterUsage = async () => {
  const response = await api.get('/openrouter/usage');
  return response.data.usage;
};

export const updateNodeCost = async (nodeId, actualCost) => {
  const response = await api.put(`/nodes/${nodeId}/cost`, { actual_cost: actualCost });
  return response.data;
};




export const uploadFiles = async (files) => {
  const formData = new FormData();
  files.forEach(file => formData.append('files', file));

  const token = localStorage.getItem('token');
  const response = await fetch(`${API_URL}/api/upload`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`
    },
    body: formData
  });

  if (!response.ok) {
    throw new Error('Upload failed');
  }

  return response.json();
};

export const streamSuperChat = (prompt, conversationId, councilMembers, chairmanModel, onEvent, attachmentIds = []) => {
  const token = localStorage.getItem('token');

  fetch(`${API_URL}/superchat/chat`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      prompt,
      conversation_id: conversationId,
      council_members: councilMembers,
      chairman_model: chairmanModel,
      attachment_ids: attachmentIds
    })
  }).then(async response => {
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    if (!response.body) {
      throw new Error('Response body is null');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');
        buffer = lines.pop();

        for (const line of lines) {
          if (line.trim() === '') continue;
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6));
              onEvent(data);
              if (data.type === 'error') return;
            } catch (e) {
              console.error("Error parsing SSE data", e, line);
            }
          }
        }
      }
    } catch (streamError) {
      console.error("Error reading stream", streamError);
      onEvent({ type: 'error', message: `Stream error: ${streamError.message}` });
    } finally {
      reader.releaseLock();
    }
  }).catch(err => {
    console.error("Network/Request error", err);
    onEvent({ type: 'error', message: err.message || 'Network error occurred' });
  });
};

export const streamCouncil = (prompt, councilMembers, chairmanModel, method, onEvent, roles = [], maxIterations = 3, attachmentIds = []) => {
  const token = localStorage.getItem('token');

  // Use fetch for streaming body support if possible, or just standard SSE endpoint
  // But we implemented POST streaming. Fetch API supports reading stream body.

  fetch(`${API_URL}/council/run`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`
    },
    body: JSON.stringify({
      prompt,
      council_members: councilMembers,
      chairman_model: chairmanModel,
      method: method,
      roles: roles,
      max_iterations: maxIterations,
      attachment_ids: attachmentIds
    })
  }).then(async response => {
    if (!response.ok) {
      const errorText = await response.text();
      throw new Error(`HTTP ${response.status}: ${errorText}`);
    }

    if (!response.body) {
      throw new Error('Response body is null');
    }

    const reader = response.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    try {
      while (true) {
        const { done, value } = await reader.read();
        if (done) {
          // Stream ended normally
          break;
        }

        buffer += decoder.decode(value, { stream: true });
        const lines = buffer.split('\n');

        // Process all complete lines
        buffer = lines.pop(); // Keep the last incomplete line in buffer

        for (const line of lines) {
          if (line.trim() === '') continue;
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.substring(6));
              onEvent(data);
              // If we got an error event, stop processing
              if (data.type === 'error') {
                return;
              }
            } catch (e) {
              console.error("Error parsing SSE data", e, "Line:", line);
            }
          }
        }
      }
    } catch (streamError) {
      console.error("Error reading stream", streamError);
      onEvent({ type: 'error', message: `Stream error: ${streamError.message}` });
    } finally {
      reader.releaseLock();
    }
  }).catch(err => {
    console.error("Network/Request error", err);
    onEvent({ type: 'error', message: err.message || 'Network error occurred' });
  });
};

export default api;
