/**
 * StreamingMessage Component
 *
 * Displays a streaming message with real-time updates and agent status
 * Similar to Claude.ai's streaming interface
 */

import React from 'react';
import './StreamingMessage.css';

const StreamingMessage = ({ message, agentStatus, isStreaming }) => {
  return (
    <div className="streaming-message-container">
      {/* Agent Status Bar */}
      {agentStatus && (
        <div className="agent-status-bar">
          <div className="status-indicator">
            {isStreaming && <div className="pulse-dot" />}
            <span className="status-text">{agentStatus}</span>
          </div>
        </div>
      )}

      {/* Streaming Message Content */}
      <div className="message assistant-message">
        <div className="message-avatar">
          <span className="avatar-icon">🤖</span>
        </div>
        <div className="message-content">
          {message && (
            <>
              {message}
              {isStreaming && <span className="streaming-cursor">▋</span>}
            </>
          )}
          {!message && isStreaming && (
            <span className="waiting-indicator">...</span>
          )}
        </div>
      </div>
    </div>
  );
};

export default StreamingMessage;
