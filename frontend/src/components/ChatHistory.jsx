import { useEffect, useState } from 'react';
import { getChatHistory } from '../api/api';
import Message from './Message';

export default function ChatHistory({ onResume }) {
  const [history, setHistory] = useState([]);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);

  const loadHistory = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await getChatHistory();
      setHistory(response.data);
    } catch {
      setError('Unable to load chat history.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHistory();
  }, []);

  return (
    <section className="dashboard-card history-card">
      <div className="page-card-header">
        <div>
          <h3>Previous Conversations</h3>
          <p>Latest 50 questions saved by the backend.</p>
        </div>
        <button className="secondary-btn" type="button" onClick={loadHistory} disabled={loading}>
          {loading ? 'Loading…' : 'Refresh'}
        </button>
      </div>

      {error && <p className="error-text">{error}</p>}
      {!loading && !error && history.length === 0 && <p className="empty">No chat history yet.</p>}
      <div className="history-list">
        {history.map((item) => (
          <article className="history-item" key={item.id}>
            <div className="history-meta">
              <span>{new Date(item.asked_at).toLocaleString()}</span>
              {item.sources?.length > 0 && <span>{item.sources.length} source{item.sources.length === 1 ? '' : 's'}</span>}
            </div>
            <div className="history-messages">
              <Message msg={{ role: 'user', content: item.question }} />
              <Message msg={{ role: 'bot', content: item.answer, sources: item.sources }} />
            </div>
            <button className="secondary-btn resume-btn" type="button" onClick={() => onResume(item)}>
              Resume chat
            </button>
          </article>
        ))}
      </div>
    </section>
  );
}
