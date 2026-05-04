import React, { useEffect, useRef } from 'react';
import MessageBubble from './MessageBubble';

const SUGGESTIONS = [
  '🔧 I need AC repair',
  '🏠 Book AC installation',
  '📋 Check my booking status',
  '📞 Talk to a support agent',
  '💰 Service pricing & plans',
  '🛡️ Warranty information',
];

const WelcomeBanner = ({ onSuggestion }) => (
  <div className="welcome-banner" role="region" aria-label="Welcome message">
    <div className="welcome-icon" aria-hidden="true">❄️</div>
    <h1 className="welcome-title">FrostGuard AC Services</h1>
    <p className="welcome-subtitle">
      Hi there! I'm your FrostGuard AI assistant. I can help you book AC installation,
      repair, or servicing appointments, track your bookings, and answer any questions
      about our services — instantly, 24/7.
    </p>
    <div className="suggestion-chips" role="list" aria-label="Suggested questions">
      {SUGGESTIONS.map((s, i) => (
        <button
          key={i}
          className="suggestion-chip"
          role="listitem"
          onClick={() => onSuggestion(s.replace(/^[^ ]+ /, ''))}
          id={`suggestion-chip-${i}`}
        >
          {s}
        </button>
      ))}
    </div>
  </div>
);

export default function ChatWindow({ history, isTyping, onSuggestion }) {
  const bottomRef = useRef(null);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [history, isTyping]);

  return (
    <div className="chat-window">
      {history.length === 0 ? (
        <WelcomeBanner onSuggestion={onSuggestion} />
      ) : (
        history.map((msg, i) => <MessageBubble key={i} message={msg} />)
      )}
      {isTyping && (
        <div className="message-row bot">
          <div className="message-avatar bot" aria-hidden="true">❄️</div>
          <div className="message-content">
            <div className="bubble bot typing-indicator">
              <span className="typing-dot" />
              <span className="typing-dot" />
              <span className="typing-dot" />
            </div>
          </div>
        </div>
      )}
      <div ref={bottomRef} />
    </div>
  );
}
