import React, { useState, useRef, useEffect } from 'react';
import { Plus, Sparkles, ChevronDown, ArrowUp, BookOpen } from 'lucide-react';
import { useNavigate } from 'react-router-dom';
import './Chat.css';

const STANDARDS = ['Std 6', 'Std 7', 'Std 8'];

const Chat = () => {
  const navigate = useNavigate();
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [selectedStd, setSelectedStd] = useState('Std 6');
  const [stdOpen, setStdOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages, isLoading]);

  const handleSend = () => {
    const text = input.trim();
    if (!text || isLoading) return;

    setMessages(prev => [...prev, { role: 'user', text }]);
    setInput('');
    setIsLoading(true);

    // Simulated bot response — replace with real API call
    setTimeout(() => {
      setMessages(prev => [...prev, {
        role: 'bot',
        text: `हे उत्तर ${selectedStd} च्या अभ्यासक्रमावर आधारित आहे.\n\nThis answer is based on the ${selectedStd} Maharashtra State Board syllabus. I found relevant information from your textbook to answer: "${text}".`,
      }]);
      setIsLoading(false);
    }, 1500);
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  const isEmpty = messages.length === 0;

  return (
    <div className="chat-root">

      {/* ── TOP NAV ─────────────────────────────────── */}
      <header className="chat-nav">
        <button className="logo-badge" onClick={() => navigate('/explore')}>
          <Sparkles size={16} color="var(--primary-yellow)" />
          <span>Marathi RAG Tutor</span>
        </button>

        {/* Standard Selector */}
        <div className="std-selector-wrapper">
          <button
            className="std-selector-btn"
            onClick={() => setStdOpen(o => !o)}
            id="std-selector"
          >
            <BookOpen size={14} />
            {selectedStd}
            <ChevronDown size={14} style={{ transition: 'transform 0.2s', transform: stdOpen ? 'rotate(180deg)' : 'rotate(0deg)' }} />
          </button>
          {stdOpen && (
            <div className="std-dropdown">
              {STANDARDS.map(std => (
                <button
                  key={std}
                  className={`std-option ${std === selectedStd ? 'active' : ''}`}
                  onClick={() => { setSelectedStd(std); setStdOpen(false); }}
                >
                  {std}
                </button>
              ))}
            </div>
          )}
        </div>

        <div className="model-badge">Mistral Large</div>
      </header>

      {/* ── DARK CHAT BODY ───────────────────────────── */}
      <div className="chat-body">
        <div className="messages-scroll">

          {isEmpty ? (
            <div className="welcome-screen">
              <div className="welcome-icon">
                <Sparkles size={36} color="var(--primary-yellow)" />
              </div>
              <h2 className="welcome-title">
                नमस्ते! Welcome to Marathi RAG Tutor
              </h2>
              <p className="welcome-subtitle">
                Ask any question from your <strong>{selectedStd}</strong> Maharashtra State Board Marathi textbook.
                I will find the answer directly from your textbook content.
              </p>
              <span className="welcome-hint">
                मराठीत किंवा इंग्रजीत विचारा — Ask in Marathi or English
              </span>
            </div>
          ) : (
            messages.map((msg, i) =>
              msg.role === 'bot' ? (
                <div key={i} className="message-group">
                  <div className="bot-label">
                    <Sparkles size={13} color="#888" />
                    <span>Tutor ({selectedStd})</span>
                  </div>
                  <div className="bot-bubble">
                    {msg.text.split('\n').filter(Boolean).map((line, j) => (
                      <p key={j}>{line}</p>
                    ))}
                  </div>
                </div>
              ) : (
                <div key={i} className="user-group">
                  <div className="user-label">
                    <div className="avatar-dot" />
                    <span>Student</span>
                  </div>
                  <div className="user-bubble">{msg.text}</div>
                </div>
              )
            )
          )}

          {isLoading && (
            <div className="message-group">
              <div className="bot-label">
                <Sparkles size={13} color="#888" />
                <span>Tutor ({selectedStd})</span>
              </div>
              <div className="bot-bubble">
                <div className="typing-indicator">
                  <span /><span /><span />
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>

        {/* ── INPUT BAR ─────────────────────────────── */}
        <div className="input-bar">
          <div className="input-inner">
            <input
              ref={inputRef}
              id="chat-input"
              type="text"
              value={input}
              onChange={e => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="विचारा... (Ask your question here...)"
              disabled={isLoading}
              autoComplete="off"
            />
            <button
              id="send-btn"
              className={`send-btn ${input.trim() && !isLoading ? 'active' : ''}`}
              onClick={handleSend}
              disabled={!input.trim() || isLoading}
            >
              <ArrowUp size={20} />
            </button>
          </div>
          <p className="input-hint">Press Enter to send &nbsp;&middot;&nbsp; Shift+Enter for new line</p>
        </div>
      </div>
    </div>
  );
};

export default Chat;
