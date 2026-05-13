import React, { useState, useEffect, useRef } from 'react';
import API from '../api/axios';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import './Chatbot.css';

const SESSION_KEY = 'chatbot_session_id';
const SESSION_TS_KEY = 'chatbot_session_ts';
const SESSION_TIMEOUT_MS = 30 * 60 * 1000; // 30 minutes

const Chatbot = ({ isOpen, onClose }) => {
  const [sessionId, setSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [financialContext, setFinancialContext] = useState(null);
  const [sessions, setSessions] = useState([]);
  const [activeSessionId, setActiveSessionId] = useState(null);
  const [sessionLoading, setSessionLoading] = useState(false);
  const messagesEndRef = useRef(null);

  // On open: resume existing session if still valid, else create new one
  useEffect(() => {
    if (!isOpen) return;

    const savedId = localStorage.getItem(SESSION_KEY);
    const savedTs = parseInt(localStorage.getItem(SESSION_TS_KEY) || '0', 10);
    const isExpired = Date.now() - savedTs > SESSION_TIMEOUT_MS;

    if (savedId && !isExpired) {
      resumeSession(savedId);
    } else {
      createNewSession();
    }

    fetchFinancialContext();
    fetchSessions();
  }, [isOpen]);

  // Update session activity timestamp whenever a message is sent
  const touchSession = () => {
    localStorage.setItem(SESSION_TS_KEY, String(Date.now()));
  };

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const resumeSession = async (id) => {
    setSessionLoading(true);
    try {
      const response = await API.get(`/api/chatbot/sessions/${id}/`);
      const existingMessages = response.data.messages || [];
      setSessionId(id);
      setActiveSessionId(id);

      if (existingMessages.length > 0) {
        setMessages(existingMessages);
      } else {
        setMessages([{
          id: Date.now(),
          role: 'assistant',
          content: "👋 Hello! I'm your financial assistant. I can help you analyze spending, create savings goals, check budgets, and much more. What would you like to do?"
        }]);
      }
      touchSession();
    } catch {
      // Session no longer exists on server — create a fresh one
      createNewSession();
    } finally {
      setSessionLoading(false);
    }
  };

  const createNewSession = async () => {
    setSessionLoading(true);
    try {
      const response = await API.post('/api/chatbot/sessions/', {
        title: `Chat - ${new Date().toLocaleString()}`
      });

      const newSessionId = response.data.id;
      setSessionId(newSessionId);
      setActiveSessionId(newSessionId);

      // Persist session ID and timestamp
      localStorage.setItem(SESSION_KEY, String(newSessionId));
      localStorage.setItem(SESSION_TS_KEY, String(Date.now()));

      setMessages([{
        id: Date.now(),
        role: 'assistant',
        content: "👋 Hello! I'm your financial assistant. I can help you analyze spending, create savings goals, check budgets, and much more. What would you like to do?"
      }]);
    } catch (error) {
      console.error('❌ Failed to create chat session:', error);
      setMessages([{
        id: Date.now(),
        role: 'assistant',
        content: '❌ Could not connect to chat service. Make sure the Django server is running at http://localhost:8000'
      }]);
    } finally {
      setSessionLoading(false);
    }
  };

  const fetchSessions = async () => {
    try {
      const response = await API.get('/api/chatbot/sessions/');
      setSessions(response.data.results || response.data);
    } catch (error) {
      console.error('Failed to fetch sessions', error);
    }
  };

  const fetchFinancialContext = async () => {
    try {
      const response = await API.get('/api/chatbot/sessions/get_financial_context/');
      setFinancialContext(response.data);
    } catch (error) {
      console.error('Failed to fetch financial context', error);
    }
  };

  const loadSession = async (id) => {
    try {
      const response = await API.get(`/api/chatbot/sessions/${id}/`);
      setSessionId(id);
      setActiveSessionId(id);
      setMessages(response.data.messages || []);
      localStorage.setItem(SESSION_KEY, String(id));
      localStorage.setItem(SESSION_TS_KEY, String(Date.now()));
    } catch (error) {
      console.error('Failed to load session', error);
    }
  };

  const sendMessage = async (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    if (!sessionId) return;

    const userMessage = input;
    setInput('');
    setLoading(true);
    touchSession();

    setMessages(prev => [...prev, {
      id: Date.now(),
      role: 'user',
      content: userMessage
    }]);

    try {
      const response = await API.post(`/api/chatbot/sessions/${sessionId}/send_message/`, {
        message: userMessage
      });

      setMessages(prev => [...prev, {
        id: response.data.message_id || Date.now(),
        role: 'assistant',
        content: response.data.response
      }]);

      fetchFinancialContext();
    } catch (error) {
      console.error('Chat error:', error);
      const errorMsg = error.response?.data?.error || error.message || 'Failed to process message';
      setMessages(prev => [...prev, {
        id: Date.now(),
        role: 'assistant',
        content: '❌ Error: ' + errorMsg
      }]);
    } finally {
      setLoading(false);
    }
  };

  const clearChatHistory = async () => {
    if (window.confirm('Are you sure you want to clear all your chat history? This cannot be undone.')) {
      try {
        await API.post('/api/chatbot/sessions/clear_sessions/');
        setMessages([]);
        setSessions([]);
        localStorage.removeItem(SESSION_KEY);
        localStorage.removeItem(SESSION_TS_KEY);
        createNewSession();
      } catch (error) {
        console.error('Failed to clear sessions', error);
      }
    }
  };

  // Format currency using context symbol if available
  const fmt = (val) => {
    const sym = financialContext?.summary?.currency_symbol || '₹';
    return `${sym}${Number(val).toFixed(2)}`;
  };

  const suggestedQueries = [
    "What's my spending pattern?",
    "Set a budget for food of ₹5000",
    "Check my budget status",
    "Add a bill reminder",
    "Analyze my spending",
  ];

  if (!isOpen) return null;

  return (
    <div className="chatbot-overlay">
      <div className="chatbot-container">
        {/* Header */}
        <div className="chatbot-header">
          <div className="header-left">
            <h2>💰 Finance Assistant</h2>
          </div>
          <div className="header-right">
            <button
              className="clear-chat-btn"
              onClick={clearChatHistory}
              title="Clear All History"
            >
              🗑️
            </button>
            <button
              className="new-chat-btn"
              onClick={createNewSession}
              title="New Chat"
            >
              ➕
            </button>
            <button
              className="close-btn"
              onClick={onClose}
              title="Close"
            >
              ✕
            </button>
          </div>
        </div>

        <div className="chatbot-content">
          {/* Financial Summary — Balance & Monthly Net only */}
          {financialContext && (
            <div className="financial-summary">
              <div className="summary-card">
                <span className="label">Balance</span>
                <p className="value">{fmt(financialContext.summary.total_balance)}</p>
              </div>
              <div className="summary-card">
                <span className="label">Monthly Net</span>
                <p className="value" style={{ color: financialContext.summary.net_monthly >= 0 ? '#4CAF50' : '#FF5252' }}>
                  {fmt(financialContext.summary.net_monthly)}
                </p>
              </div>
            </div>
          )}

          {/* Sessions List */}
          {sessions.length > 1 && (
            <div className="sessions-list">
              <details>
                <summary>📋 Chat History ({sessions.length})</summary>
                <div className="sessions-scroll">
                  {sessions.map(session => (
                    <button
                      key={session.id}
                      className={`session-item ${session.id === activeSessionId ? 'active' : ''}`}
                      onClick={() => loadSession(session.id)}
                    >
                      {session.title}
                    </button>
                  ))}
                </div>
              </details>
            </div>
          )}

          {/* Chat Messages */}
          <div className="messages-container">
            {messages.length === 1 && messages[0].role === 'assistant' && (
              <div className="suggested-queries">
                <p className="suggestion-title">What can I help you with?</p>
                {suggestedQueries.map((query, idx) => (
                  <button
                    key={idx}
                    className="query-button"
                    onClick={() => setInput(query)}
                  >
                    {query}
                  </button>
                ))}
              </div>
            )}

            {messages.map(msg => (
              <div key={msg.id} className={`message ${msg.role}`}>
                <div className="message-avatar">
                  {msg.role === 'assistant' ? '🤖' : '👤'}
                </div>
                <div className="message-content">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {msg.content}
                  </ReactMarkdown>
                </div>
              </div>
            ))}

            {loading && (
              <div className="message assistant">
                <div className="message-avatar">🤖</div>
                <div className="loading-dots">
                  <span></span><span></span><span></span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* Input */}
          <form onSubmit={sendMessage} className="chat-input-form">
            {sessionLoading && (
              <div style={{ width: '100%', textAlign: 'center', padding: '8px', fontSize: '12px', color: '#999' }}>
                ⏳ Initializing chat...
              </div>
            )}
            {!sessionLoading && (
              <>
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder={!sessionId ? "Connecting..." : "Ask about your finances..."}
                  disabled={loading || !sessionId}
                  autoFocus
                  style={{ opacity: !sessionId ? 0.5 : 1 }}
                />
                <button type="submit" disabled={loading || !input.trim() || !sessionId || sessionLoading}>
                  {loading ? '⏳' : '📤'}
                </button>
              </>
            )}
          </form>
        </div>
      </div>
    </div>
  );
};

export default Chatbot;
