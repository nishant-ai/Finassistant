'use client';

import { useState, useEffect, useRef, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';
import Link from 'next/link';
import ReactMarkdown from 'react-markdown';

interface Message {
  sender: 'user' | 'ai';
  text: string;
}

// Wrap the component in Suspense for useSearchParams
export default function ChatPageWrapper() {
  return (
    <Suspense fallback={<div className="flex h-screen items-center justify-center bg-gray-900 text-white">Loading Chat...</div>}>
      <ChatPage />
    </Suspense>
  )
}

function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const searchParams = useSearchParams();
  const chatContainerRef = useRef<HTMLDivElement>(null);

  const docId = searchParams.get('docId');
  const ticker = searchParams.get('ticker');
  const companyName = searchParams.get('companyName');

  // --- 1. NEW: LOAD MESSAGES FROM LOCAL STORAGE ON PAGE LOAD ---
  useEffect(() => {
    if (docId) {
      const savedMessages = localStorage.getItem(`chat_${docId}`);
      if (savedMessages) {
        setMessages(JSON.parse(savedMessages));
      }
    }
  }, [docId]); // This effect runs only when the docId changes

  // --- 2. NEW: SAVE MESSAGES TO LOCAL STORAGE WHENEVER THEY CHANGE ---
  useEffect(() => {
    // Don't save if there are no messages or no docId
    if (docId && messages.length > 0) {
      localStorage.setItem(`chat_${docId}`, JSON.stringify(messages));
    }
    // Scroll to bottom
    chatContainerRef.current?.scrollTo({ top: chatContainerRef.current.scrollHeight, behavior: 'smooth' });
  }, [messages, docId]); // This effect runs whenever messages change

  const streamAIResponse = (fullText: string) => {
    // ... (This function remains unchanged)
    let currentText = '';
    setMessages(prev => [...prev, { sender: 'ai', text: '' }]);
    const interval = setInterval(() => {
      const chunkSize = 2;
      currentText = fullText.slice(0, currentText.length + chunkSize);
      if (currentText.length > fullText.length) currentText = fullText;
      setMessages(prev => {
        const newMessages = [...prev];
        newMessages[newMessages.length - 1].text = currentText;
        return newMessages;
      });
      if (currentText.length === fullText.length) {
        clearInterval(interval);
        setIsTyping(false);
      }
    }, 10);
  };

  const handleSendMessage = async (e: React.FormEvent) => {
    // ... (This function remains unchanged)
    e.preventDefault();
    if (!input.trim() || !docId || isTyping) return;
    const userMessage: Message = { sender: 'user', text: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsTyping(true);
    try {
      const response = await fetch('http://127.0.0.1:8000/ask', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ document_id: docId, ticker, question: input }),
      });
      if (!response.ok) throw new Error('Failed to get a response from the agent.');
      const data = await response.json();
      streamAIResponse(data.answer);
    } catch (err: any) {
      streamAIResponse(`Error: ${err.message}`);
      setIsTyping(false);
    }
  };

  // The rest of your JSX remains unchanged
  return (
    <div className="flex flex-col h-screen bg-gray-900 text-white">
      <header className="flex items-center justify-between p-4 bg-gray-800 border-b border-gray-700 shadow-md">
        <Link href="/" className="p-2 rounded-full hover:bg-gray-700 transition">
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6 text-gray-300">
                <path fillRule="evenodd" d="M11.03 3.97a.75.75 0 0 1 0 1.06l-6.22 6.22H21a.75.75 0 0 1 0 1.5H4.81l6.22 6.22a.75.75 0 1 1-1.06 1.06l-7.5-7.5a.75.75 0 0 1 0-1.06l7.5-7.5a.75.75 0 0 1 1.06 0Z" clipRule="evenodd" />
            </svg>
        </Link>
        <div className="text-center">
            <h1 className="text-lg font-bold text-gray-200">
                Analysis: <span className="text-purple-400">{companyName}</span>
            </h1>
            <p className="text-sm text-gray-500">Ticker: {ticker}</p>
        </div>
        <div className="w-10"></div>
      </header>

      <main ref={chatContainerRef} className="flex-1 p-6 overflow-y-auto space-y-6">
        {messages.map((msg, index) => (
          <div key={index} className={`flex items-end gap-3 ${msg.sender === 'user' ? 'justify-end' : 'justify-start'}`}>
            <div className={`max-w-xl px-5 py-3 rounded-2xl shadow-lg prose prose-invert prose-sm ${
                msg.sender === 'user' 
                ? 'bg-gradient-to-br from-purple-800 to-pink-800 text-white rounded-br-none' 
                : 'bg-gray-700 text-gray-200 rounded-bl-none'
            }`}>
              {msg.sender === 'user' ? msg.text : <ReactMarkdown>{msg.text}</ReactMarkdown>}
            </div>
          </div>
        ))}
        {isTyping && (
          <div className="flex justify-start">
             <div className="px-5 py-3 bg-gray-700 rounded-2xl rounded-bl-none shadow-lg">
              <span className="inline-block w-2.5 h-2.5 mr-1 bg-purple-500 rounded-full animate-pulse"></span>
              <span className="inline-block w-2.5 h-2.5 mr-1 bg-purple-500 rounded-full animate-pulse delay-75"></span>
              <span className="inline-block w-2.5 h-2.5 bg-purple-500 rounded-full animate-pulse delay-150"></span>
            </div>
          </div>
        )}
      </main>

      <footer className="p-4 bg-gray-800 border-t border-gray-700">
        <form onSubmit={handleSendMessage} className="flex items-center gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Ask a question about the filing..."
            className="flex-1 px-5 py-3 text-gray-200 bg-gray-700 border border-gray-600 rounded-full focus:outline-none focus:ring-2 focus:ring-purple-500 transition duration-200"
            disabled={isTyping}
          />
          <button type="submit" className="p-3 font-bold text-white bg-gradient-to-r from-purple-700 to-pink-700 rounded-full hover:from-purple-800 hover:to-pink-800 disabled:opacity-50 transition-transform transform hover:scale-110" disabled={isTyping || !input.trim()}>
            <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="currentColor" className="w-6 h-6">
                <path d="M3.478 2.404a.75.75 0 0 0-.926.941l2.432 7.905H13.5a.75.75 0 0 1 0 1.5H4.984l-2.432 7.905a.75.75 0 0 0 .926.94 60.519 60.519 0 0 0 18.445-8.986.75.75 0 0 0 0-1.218A60.517 60.517 0 0 0 3.478 2.404Z" />
            </svg>
          </button>
        </form>
      </footer>
    </div>
  );
}