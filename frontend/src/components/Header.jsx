import React from 'react';
import { MessageSquare, Brain, Settings } from 'lucide-react';

const Header = ({ mode, onModeChange }) => {
  return (
    <header className="sticky top-0 z-10 bg-chat-surface border-b border-chat-border">
      <div className="max-w-4xl mx-auto px-4 py-3 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="text-xl font-semibold text-chat-text flex items-center gap-2">
            <span className="text-2xl">💰</span>
            <span>Financial Assistant</span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          {/* Mode Toggle */}
          <div className="flex bg-chat-input rounded-lg p-1">
            <button
              onClick={() => onModeChange('chat')}
              className={`flex items-center gap-2 px-4 py-2 rounded-md transition-all ${
                mode === 'chat'
                  ? 'bg-accent-blue text-gray-900 font-medium'
                  : 'text-chat-text-secondary hover:text-chat-text'
              }`}
            >
              <MessageSquare size={18} />
              <span>Chat</span>
            </button>
            <button
              onClick={() => onModeChange('think')}
              className={`flex items-center gap-2 px-4 py-2 rounded-md transition-all ${
                mode === 'think'
                  ? 'bg-accent-purple text-gray-900 font-medium'
                  : 'text-chat-text-secondary hover:text-chat-text'
              }`}
            >
              <Brain size={18} />
              <span>Think</span>
            </button>
          </div>

          {/* Settings Icon */}
          <button className="p-2 text-chat-text-secondary hover:text-chat-text rounded-lg hover:bg-chat-input transition-colors">
            <Settings size={20} />
          </button>
        </div>
      </div>
    </header>
  );
};

export default Header;
