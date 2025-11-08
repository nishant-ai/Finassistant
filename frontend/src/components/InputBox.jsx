import React, { useState, useRef, useEffect } from 'react';
import { Send, StopCircle } from 'lucide-react';

const InputBox = ({ onSendMessage, isLoading, mode }) => {
  const [input, setInput] = useState('');
  const textareaRef = useRef(null);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (input.trim() && !isLoading) {
      onSendMessage(input.trim());
      setInput('');
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto';
      textareaRef.current.style.height = Math.min(textareaRef.current.scrollHeight, 200) + 'px';
    }
  }, [input]);

  const placeholder = mode === 'chat'
    ? 'Ask about stocks, companies, or financial data...'
    : 'Analyze a stock, compare companies, or get an in-depth market summary...';

  return (
    <div className="sticky bottom-0 bg-chat-bg border-t border-chat-border">
      <div className="max-w-4xl mx-auto px-4 py-4">
        <form onSubmit={handleSubmit} className="relative">
          <div className="relative flex items-end bg-chat-input rounded-2xl border border-chat-border focus-within:border-accent-blue transition-colors">
            <textarea
              ref={textareaRef}
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={placeholder}
              disabled={isLoading}
              className="flex-1 bg-transparent text-chat-text placeholder-chat-text-secondary px-4 py-3 pr-12 resize-none outline-none min-h-[52px] max-h-[200px]"
              rows={1}
            />
            <button
              type="submit"
              disabled={!input.trim() || isLoading}
              className={`absolute right-2 bottom-2 p-2 rounded-lg transition-all ${
                input.trim() && !isLoading
                  ? mode === 'chat'
                    ? 'bg-accent-blue text-gray-900 hover:bg-accent-blue/90'
                    : 'bg-accent-purple text-gray-900 hover:bg-accent-purple/90'
                  : 'bg-chat-border text-chat-text-secondary cursor-not-allowed'
              }`}
            >
              {isLoading ? (
                <StopCircle size={20} />
              ) : (
                <Send size={20} />
              )}
            </button>
          </div>

          {/* Helper text */}
          <div className="mt-2 px-2 flex items-center justify-between text-xs text-chat-text-secondary">
            <span>
              {mode === 'chat' ? 'Quick responses' : 'In-depth analysis'}
            </span>
            <span>Press Enter to send, Shift+Enter for new line</span>
          </div>
        </form>
      </div>
    </div>
  );
};

export default InputBox;
