import React, { useState } from 'react';

export default function InputBar({ onSend, isLoading }) {
  const [text, setText] = useState('');
  const maxLength = 300;

  const handleSend = () => {
    if (text.trim() && !isLoading) {
      onSend(text.trim());
      setText('');
    }
  };

  const onKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="input-bar-wrapper">
      <div className="input-bar">
        <textarea
          value={text}
          onChange={(e) => setText(e.target.value)}
          onKeyDown={onKeyDown}
          className="chat-input"
          placeholder="Ask FrostGuard support..."
          maxLength={maxLength}
          rows={1}
          disabled={isLoading}
        />
        <button 
          onClick={handleSend} 
          className="send-btn" 
          disabled={!text.trim() || isLoading}
          aria-label="Send message"
        >
          ↑
        </button>
      </div>
      <div className="input-footer">
        <span className="input-hint">Powered by advanced AI. Models can make mistakes.</span>
        <span className={`char-count ${text.length >= maxLength ? 'over' : ''}`}>
          {text.length}/{maxLength}
        </span>
      </div>
    </div>
  );
}
