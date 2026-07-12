import { useEffect, useState } from 'react';
import { getHealth } from '../api/api';

export default function HealthCheck() {
  const [health, setHealth] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(true);
  const [checkedAt, setCheckedAt] = useState(null);

  const loadHealth = async () => {
    setLoading(true);
    setError('');
    try {
      const response = await getHealth();
      setHealth(response.data);
      setCheckedAt(new Date());
    } catch {
      setHealth(null);
      setError('The backend health endpoint could not be reached.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadHealth();
  }, []);

  const isHealthy = health?.status === 'ok';

  return (
    <section className="dashboard-card health-card">
      <div className="page-card-header">
        <div>
          <h3>Backend Health</h3>
          <p>Live response from <code>/api/health/</code></p>
        </div>
        <button className="secondary-btn" type="button" onClick={loadHealth} disabled={loading}>
          {loading ? 'Checking…' : 'Refresh'}
        </button>
      </div>

      {error ? (
        <div className="status-panel error-panel">
          <strong>Unavailable</strong>
          <span>{error}</span>
        </div>
      ) : health ? (
        <>
          <div className={`status-panel ${isHealthy ? 'success-panel' : 'error-panel'}`}>
            <strong>{isHealthy ? 'Operational' : 'Needs attention'}</strong>
            <span>Backend status: {health.status}</span>
          </div>
          <div className="metric-grid">
            <div className="metric-card">
              <span>Documents</span>
              <strong>{health.documents}</strong>
            </div>
            <div className="metric-card">
              <span>Saved chats</span>
              <strong>{health.chats}</strong>
            </div>
          </div>
          {checkedAt && <p className="checked-at">Last checked: {checkedAt.toLocaleString()}</p>}
        </>
      ) : null}
    </section>
  );
}
