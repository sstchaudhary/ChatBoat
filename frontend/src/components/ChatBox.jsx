import { useEffect, useRef, useState } from 'react';
import { askStream } from '../api/api';
import Message from './Message';

export default function ChatBox() {
  const [messages, setMessages] = useState([
    { role: 'bot', content: 'Hello! 👋 Upload a document, then ask a question about it.' },
  ]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState(false);
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const sendMessage = async () => {
    const question = input.trim();
    if (!question || loading) {
      return;
    }

    setMessages((prev) => [...prev, { role: 'user', content: question }]);
    setInput('');
    setLoading(true);
    setStreaming(false);

    // Add an empty bot message that will be filled token by token
    setMessages((prev) => [...prev, { role: 'bot', content: '', isThinking: true }]);

    try {
      await askStream(
        question,
        // onToken: append each chunk to the last message
        (token) => {
          setStreaming(true);
          setMessages((prev) => {
            const msgs = [...prev];
            const last = msgs[msgs.length - 1];
            msgs[msgs.length - 1] = { ...last, content: last.content + token, isThinking: false };
            return msgs;
          });
        },
        // onDone: attach sources to the last message
        (sources) => {
          setMessages((prev) => {
            const msgs = [...prev];
            msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], sources, isThinking: false };
            return msgs;
          });
        },
        // onError: replace last message with the error text
        (errorMsg) => {
          setMessages((prev) => {
            const msgs = [...prev];
            msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], content: errorMsg, isThinking: false };
            return msgs;
          });
        },
      );
    } finally {
      setLoading(false);
      setStreaming(false);
    }
  };

  const handleKeyDown = (event) => {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="chatbox">
      <div className="messages">
        {messages.map((msg, idx) => (
          <Message key={idx} msg={msg} />
        ))}
        <div ref={bottomRef} />
      </div>
      <div className="input-row">
        <div className="textarea-wrapper">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question about your documents..."
            rows={3}
          />
          <button 
            className="send-btn" 
            onClick={sendMessage} 
            disabled={!input.trim() || loading}
            title="Send message"
          >
            ➤
          </button>
        </div>
      </div>
    </div>
  );
}
