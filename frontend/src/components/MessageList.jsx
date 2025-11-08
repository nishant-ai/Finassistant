import React, { useEffect, useRef } from 'react';
import Message from './Message';
import { Loader2 } from 'lucide-react';

const MessageList = ({ messages, isLoading, mode, onSendMessage }) => {
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isLoading]);

  return (
    <div className="flex-1 overflow-y-auto">
      {messages.length === 0 ? (
        <EmptyState mode={mode} onSendMessage={onSendMessage} />
      ) : (
        <>
          {messages.map((message, index) => (
            <Message key={index} message={message} />
          ))}
        </>
      )}

      {isLoading && <LoadingIndicator />}
      <div ref={messagesEndRef} />
    </div>
  );
};

const EmptyState = ({ mode, onSendMessage }) => (
  <div className="h-full flex items-center justify-center">
    <div className="text-center max-w-2xl px-4">
      <div className="text-6xl mb-4">💰</div>
      <h2 className="text-2xl font-semibold text-chat-text mb-2">
        Welcome to Financial Assistant
      </h2>
      { mode === 'chat' ?
        (        
        <>
        <p className="text-chat-text-secondary mb-6">
          Ask me anything about stocks, companies, financial analysis, and market insights.
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-left">
          <ExamplePrompt text="What is Apple's P/E ratio?" onSendMessage={onSendMessage} />
          <ExamplePrompt text="Analyze Tesla's financial health" onSendMessage={onSendMessage} />
          <ExamplePrompt text="Compare Microsoft and Google" onSendMessage={onSendMessage} />
          <ExamplePrompt text="What are the latest market trends?" onSendMessage={onSendMessage} />
        </div>
        </>
        ) : mode === 'think' ?
        (
        <>
        <p className="text-chat-text-secondary mb-6">
          Analyze Stocks, News, Stats in Depth
        </p>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-left">
          <ExamplePrompt text="What is Apple's P/E ratio?" onSendMessage={onSendMessage} />
          <ExamplePrompt text="Analyze Tesla's financial health" onSendMessage={onSendMessage} />
          <ExamplePrompt text="Compare Microsoft and Google" onSendMessage={onSendMessage} />
          <ExamplePrompt text="What are the latest market trends?" onSendMessage={onSendMessage} />
        </div>
        </>
        ) : null
      }
    </div>
  </div>
);
const ExamplePrompt = ({ text, onSendMessage }) => (
  <div
    className="bg-chat-surface border border-chat-border rounded-lg p-3 hover:border-accent-blue transition-colors cursor-pointer"
    onClick={() => onSendMessage(text)}
  >
    <p className="text-sm text-chat-text">{text}</p>
  </div>
);

const LoadingIndicator = () => (
  <div className="py-6 bg-chat-surface">
    <div className="max-w-4xl mx-auto px-4 flex gap-4">
      <div className="flex-shrink-0 w-8 h-8 rounded-full bg-gradient-to-br from-accent-blue to-accent-purple flex items-center justify-center">
        <Loader2 size={18} className="text-white animate-spin" />
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-sm font-medium mb-2 text-chat-text">Assistant</div>
        <div className="flex gap-2">
          <div className="w-2 h-2 bg-accent-blue rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
          <div className="w-2 h-2 bg-accent-blue rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></div>
          <div className="w-2 h-2 bg-accent-blue rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
        </div>
      </div>
    </div>
  </div>
);


export default MessageList;
