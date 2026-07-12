import ReactMarkdown from 'react-markdown';

export default function Message({ msg }) {
  return (
    <div className={`message ${msg.role} ${msg.isThinking ? 'thinking' : ''}`}>
      {msg.isThinking ? (
        <div className="thinking-animation">
          <span></span><span></span><span></span>
        </div>
      ) : (
        <>
          <div className="message-wrapper">
            <div className="message-content">
              <ReactMarkdown>{msg.content}</ReactMarkdown>
            </div>
            {msg.role === 'bot' && msg.sources?.length ? (
              <div className="sources">📎 Sources: {msg.sources.join(', ')}</div>
            ) : null}
          </div>
        </>
      )}
    </div>
  );
}
