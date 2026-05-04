import React, { useState } from 'react';
import { Link } from 'react-router-dom';
import ChatWindow from './components/ChatWindow';
import InputBar from './components/InputBar';

export default function App() {
  const [history, setHistory] = useState([]);
  const [isTyping, setIsTyping] = useState(false);

  const handleSuggestion = (text) => {
    sendQuery(text);
  };

  const sendQuery = async (query) => {
    const newHist = [...history, { role: 'user', content: query }];
    setHistory(newHist);
    setIsTyping(true);

    try {
      const res = await fetch('http://localhost:8000/api/v1/chat/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ query, history: newHist.slice(0, -1) })
      });
      const data = await res.json();
      setHistory([...newHist, { 
        role: 'bot', 
        content: data.answer, 
        sources: data.sources,
        intent: data.intent,
        tool_calls: data.tool_calls
      }]);
    } catch (e) {
      setHistory([...newHist, { role: 'bot', content: 'Network Error: Could not connect to FrostGuard servers.' }]);
    } finally {
      setIsTyping(false);
    }
  };

  return (
    <>
      <title>FrostGuard AC Services</title>
      <div className="app-shell">
        <header className="app-header">
          <div className="header-avatar" aria-hidden="true">❄️</div>
          <div className="header-info">
            <div className="header-title">FrostGuard Support</div>
            <div className="header-status">
              <span className="status-dot" aria-hidden="true" />
              <span>Online · Powered by AI</span>
            </div>
          </div>
          <div className="header-actions">
            <Link to="/admin" className="icon-btn" aria-label="Admin Panel" title="Admin Panel" style={{textDecoration:'none'}}>🔐</Link>
            <button className="icon-btn" aria-label="Settings">⚙️</button>
          </div>
        </header>
        
        <ChatWindow history={history} isTyping={isTyping} onSuggestion={handleSuggestion} />
        <InputBar onSend={sendQuery} isLoading={isTyping} />
      </div>
    </>
  );
}
