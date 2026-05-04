import React from 'react';

export default function MessageBubble({ message }) {
  const isUser = message.role === 'user';

  return (
    <div className={`message-row ${isUser ? 'user' : 'bot'}`}>
      <div className={`message-avatar ${isUser ? 'user' : 'bot'}`} aria-hidden="true">
        {isUser ? '👤' : '❄️'}
      </div>
      <div className="message-content">
        <div className={`bubble ${isUser ? 'user' : 'bot'}`}>
          <p>{message.content}</p>
        </div>
      </div>
    </div>
  );
}
