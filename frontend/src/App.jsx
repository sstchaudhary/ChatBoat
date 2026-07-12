import { useState } from 'react';
import FileUpload from './components/FileUpload';
import DocumentList from './components/DocumentList';
import ChatBox from './components/ChatBox';
import ChatHistory from './components/ChatHistory';
import HealthCheck from './components/HealthCheck';

const navigationItems = [
  { id: 'chat', label: 'Chat', icon: '💬' },
  { id: 'documents', label: 'Documents', icon: '📄' },
  { id: 'history', label: 'Chat History', icon: '🕘' },
  { id: 'health', label: 'Health Check', icon: '♥' },
];

const pageTitles = {
  chat: 'Document Chat',
  documents: 'Documents',
  history: 'Chat History',
  health: 'System Health',
};

const initialMessages = [
  { role: 'bot', content: 'Hello! 👋 Upload a document, then ask a question about it.' },
];

export default function App() {
  const [refreshDocs, setRefreshDocs] = useState(0);
  const [activeTab, setActiveTab] = useState('chat');
  const [menuOpen, setMenuOpen] = useState(false);
  const [messages, setMessages] = useState(initialMessages);

  const selectTab = (tab) => {
    setActiveTab(tab);
    setMenuOpen(false);
  };

  const resumeChat = (historyItem) => {
    setMessages([
      { role: 'user', content: historyItem.question },
      { role: 'bot', content: historyItem.answer, sources: historyItem.sources },
    ]);
    selectTab('chat');
  };

  return (
    <div className="app">
      <button
        className="menu-toggle"
        type="button"
        aria-label="Open navigation menu"
        onClick={() => setMenuOpen((isOpen) => !isOpen)}
      >
        ☰
      </button>
      {menuOpen && <button className="menu-backdrop" type="button" aria-label="Close navigation menu" onClick={() => setMenuOpen(false)} />}

      <aside className={`sidebar ${menuOpen ? 'open' : ''}`}>
        <div className="brand">
          <span className="brand-mark">DC</span>
          <div>
            <h1>Document Chat</h1>
            <p>Ask from your files</p>
          </div>
        </div>
        <nav className="sidebar-nav" aria-label="Main navigation">
          {navigationItems.map((item) => (
            <button
              key={item.id}
              className={activeTab === item.id ? 'active' : ''}
              type="button"
              onClick={() => selectTab(item.id)}
            >
              <span aria-hidden="true">{item.icon}</span>
              {item.label}
            </button>
          ))}
        </nav>
      </aside>

      <main className="main-content">
        <header className="content-header">
          <div>
            <p className="eyebrow">Document assistant</p>
            <h2>{pageTitles[activeTab]}</h2>
          </div>
          <p className="header-description">Upload PDF, DOCX, or TXT files and ask questions from your own content.</p>
        </header>

        {activeTab === 'chat' && (
          <ChatBox messages={messages} setMessages={setMessages} />
        )}
        {activeTab === 'documents' && (
          <div className="docs-tab">
            <FileUpload onUploadSuccess={() => setRefreshDocs((prev) => prev + 1)} />
            <DocumentList refresh={refreshDocs} />
          </div>
        )}
        {activeTab === 'history' && <ChatHistory onResume={resumeChat} />}
        {activeTab === 'health' && <HealthCheck />}
      </main>
    </div>
  );
}
