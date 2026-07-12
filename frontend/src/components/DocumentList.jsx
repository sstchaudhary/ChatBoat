import { useEffect, useState } from 'react';
import { getDocuments, deleteDocument } from '../api/api';

export default function DocumentList({ refresh }) {
  const [documents, setDocuments] = useState([]);
  const [error, setError] = useState('');

  const loadDocuments = async () => {
    try {
      setError('');
      const res = await getDocuments();
      setDocuments(res.data);
    } catch {
      setError('Unable to load documents.');
    }
  };

  useEffect(() => {
    loadDocuments();
  }, [refresh]);

  useEffect(() => {
    const interval = setInterval(() => {
      if (documents.some((doc) => !doc.indexed)) {
        loadDocuments();
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [documents]);

  const handleDelete = async (id, name) => {
    if (!window.confirm(`Delete "${name}"?`)) return;
    try {
      await deleteDocument(id);
      setDocuments((prev) => prev.filter((doc) => doc.id !== id));
    } catch {
      setError('Failed to delete document.');
    }
  };

  return (
    <div className="doc-list">
      <div className="doc-list-header">
        <h3>Uploaded Documents</h3>
        <span>{documents.length} files</span>
      </div>
      {error && <p className="error-text">{error}</p>}
      {documents.length === 0 ? (
        <p className="empty">No documents uploaded yet.</p>
      ) : (
        documents.map((doc) => (
          <div key={doc.id} className="doc-item">
            <div className="doc-item-meta">
              <span className="doc-name">{doc.name}</span>
              <span className="doc-details">{doc.size_kb} KB · {doc.file_type}</span>
            </div>
            <div className="doc-actions">
              <span className={`doc-status ${doc.indexed ? 'indexed' : ''}`}>
                {doc.indexed ? 'Indexed' : 'Pending'}
              </span>
              <button className="delete-btn" onClick={() => handleDelete(doc.id, doc.name)}>
                Delete
              </button>
            </div>
          </div>
        ))
      )}
    </div>
  );
}
