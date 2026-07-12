import axios from 'axios';

const API = axios.create({ baseURL: 'http://localhost:8000/api', timeout: 120000 });

export const uploadDocument = (file) => {
  const formData = new FormData();
  formData.append('file', file);
  return API.post('/documents/', formData);
};

export const getDocuments = () => API.get('/documents/');
export const deleteDocument = (id) => API.delete(`/documents/${id}/`);
export const getHealth = () => API.get('/health/');
export const askQuestion = (question) => API.post('/ask/', { question });
export const getChatHistory = () => API.get('/history/');
export const clearHistory = () => API.delete('/history/');

/**
 * Stream a response from the chatbot token by token.
 * @param {string} question
 * @param {{role: string, content: string}[]} conversation - prior chat messages
 * @param {(token: string) => void} onToken  - called for each text chunk
 * @param {(sources: string[]) => void} onDone - called once with final sources list
 * @param {(message: string) => void} onError - called on any error
 */
export const askStream = async (question, conversation, onToken, onDone, onError) => {
  let response;
  try {
    response = await fetch('http://localhost:8000/api/ask/stream/', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, conversation }),
    });
  } catch (err) {
    onError('Network error: could not reach the server.');
    return;
  }

  if (!response.ok) {
    try {
      const data = await response.json();
      onError(data.error || 'Request failed.');
    } catch {
      onError('Request failed.');
    }
    return;
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
      // Keep the last (potentially incomplete) line in the buffer
      buffer = lines.pop();

      for (const line of lines) {
        if (!line.startsWith('data: ')) continue;
        try {
          const event = JSON.parse(line.slice(6));
          if (event.type === 'token') {
            onToken(event.text);
          } else if (event.type === 'done') {
            onDone(event.sources || []);
          } else if (event.type === 'error') {
            onError(event.message || 'An error occurred.');
          }
        } catch {
          // ignore malformed SSE lines
        }
      }
    }
  } finally {
    reader.releaseLock();
  }
};
