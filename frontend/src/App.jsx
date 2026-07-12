import { useState } from 'react';
import FileUpload from './components/FileUpload';
import DocumentList from './components/DocumentList';
import ChatBox from './components/ChatBox';

export default function App() {
  const [refreshDocs, setRefreshDocs] = useState(0);
  const [activeTab, setActiveTab] = useState('chat');

  return (
    <div className="app">
      <header className="header">
        <div>
          <h1>Document Chatbot</h1>
          <p>Upload PDF, DOCX, or TXT and ask questions from your own files.</p>
        </div>
        <nav>
          <button className={activeTab === 'chat' ? 'active' : ''} onClick={() => setActiveTab('chat')}>
            Chat
          </button>
          <button className={activeTab === 'docs' ? 'active' : ''} onClick={() => setActiveTab('docs')}>
            Documents
          </button>
        </nav>
      </header>

      <main className="main">
        {activeTab === 'chat' ? (
          <ChatBox />
        ) : (
          <div className="docs-tab">
            <FileUpload onUploadSuccess={() => setRefreshDocs((prev) => prev + 1)} />
            <DocumentList refresh={refreshDocs} />
          </div>
        )}
      </main>
    </div>
  );
}
