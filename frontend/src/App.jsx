import { useState, useEffect } from 'react';
import Header from './components/Header';
import ChatMode from './components/ChatMode';
import ThinkMode from './components/ThinkMode';
import ChatHistorySidebar from './components/ChatHistorySidebar';
import { checkHealth } from "./services/api";
import { Wifi, WifiOff, X } from "lucide-react";
import {
  createSession,
  getSessions,
  getSession,
  deleteSession,
  updateSession
} from './services/chatHistory';

function App() {
  const [mode, setMode] = useState('chat');
  const [apiStatus, setApiStatus] = useState('checking');
  const [showApiStatusBanner, setShowApiStatusBanner] = useState(true);

  // Chat history state
  const [sessions, setSessions] = useState([]);
  const [currentSessionId, setCurrentSessionId] = useState(null);
  const [messages, setMessages] = useState([]);
  const [sidebarOpen, setSidebarOpen] = useState(true);

  useEffect(() => {
    // Check API health on mount
    const checkApiHealth = async () => {
      try {
        await checkHealth();
        setApiStatus('connected');
      } catch (error) {
        setApiStatus('disconnected');
      }
    };

    checkApiHealth();

    // Check every 30 seconds
    const interval = setInterval(checkApiHealth, 30000);
    return () => clearInterval(interval);
  }, []);

  // Load sessions when component mounts or mode changes
  useEffect(() => {
    loadSessions();
  }, [mode]);

  const loadSessions = async () => {
    try {
      // Filter sessions by current mode
      const sessionList = await getSessions(50, mode);
      setSessions(sessionList);
    } catch (error) {
      console.error('Failed to load sessions:', error);
    }
  };

  const handleNewSession = async () => {
    try {
      const newSession = await createSession(mode);
      setSessions([newSession, ...sessions]);
      setCurrentSessionId(newSession._id);
      setMessages([]);
    } catch (error) {
      console.error('Failed to create session:', error);
    }
  };

  const handleSelectSession = async (sessionId) => {
    try {
      const sessionData = await getSession(sessionId);
      setCurrentSessionId(sessionId);
      setMessages(sessionData.messages || []);
    } catch (error) {
      console.error('Failed to load session:', error);
    }
  };

  const handleDeleteSession = async (sessionId) => {
    try {
      await deleteSession(sessionId);
      setSessions(sessions.filter(s => s._id !== sessionId));

      // If deleting current session, clear it
      if (currentSessionId === sessionId) {
        setCurrentSessionId(null);
        setMessages([]);
      }
    } catch (error) {
      console.error('Failed to delete session:', error);
    }
  };

  const handleUpdateSessionTitle = async (sessionId, title) => {
    try {
      await updateSession(sessionId, { title });
      setSessions(sessions.map(s =>
        s._id === sessionId ? { ...s, title } : s
      ));
    } catch (error) {
      console.error('Failed to update session:', error);
    }
  };

  const handleModeChange = async (newMode) => {
    setMode(newMode);
    setCurrentSessionId(null);
    setMessages([]);
  };

  const handleMessageAdded = () => {
    // Refresh sessions to update message counts and timestamps
    loadSessions();
  };

  const handleSessionCreated = (sessionId) => {
    // Update current session ID and refresh session list
    setCurrentSessionId(sessionId);
    loadSessions();
  };

  return (
    <div className="h-screen flex flex-col bg-chat-bg text-chat-text">
      <Header mode={mode} onModeChange={handleModeChange} />

      <div className="flex flex-1 overflow-hidden relative">
        {/* Chat History Sidebar */}
        <ChatHistorySidebar
          sessions={sessions}
          currentSessionId={currentSessionId}
          onSelectSession={handleSelectSession}
          onNewSession={handleNewSession}
          onDeleteSession={handleDeleteSession}
          onUpdateSessionTitle={handleUpdateSessionTitle}
          isOpen={sidebarOpen}
          onToggle={() => setSidebarOpen(!sidebarOpen)}
          mode={mode}
        />

        {/* Main Content Area */}
        <div className={`flex-1 flex flex-col transition-all duration-300 ${sidebarOpen ? 'ml-64' : 'ml-0'}`}>
          {/* API Status Banner */}
          {showApiStatusBanner && apiStatus === 'disconnected' && (
            <div className="bg-red-900/30 border-b border-red-700/50">
              <div className="max-w-4xl mx-auto px-4 py-2 flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <WifiOff size={16} className="text-red-400" />
                  <span className="text-red-300">
                    Agent Unavailable
                  </span>
                </div>
                <button onClick={() => setShowApiStatusBanner(false)} className="text-red-300 hover:text-red-100">
                  <X size={18} />
                </button>
              </div>
            </div>
          )}

          {showApiStatusBanner && apiStatus === 'connected' && (
            <div className="bg-green-900/20 border-b border-green-700/50">
              <div className="max-w-4xl mx-auto px-4 py-2 flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <Wifi size={16} className="text-green-400" />
                  <span className="text-green-300">Agent in Service</span>
                </div>
                <button onClick={() => setShowApiStatusBanner(false)} className="text-green-300 hover:text-green-100">
                  <X size={18} />
                </button>
              </div>
            </div>
          )}

          {/* Main Chat/Report Content */}
          <main className="flex-1 overflow-hidden">
            {mode === 'chat' ? (
              <ChatMode
                currentSessionId={currentSessionId}
                messages={messages}
                setMessages={setMessages}
                onMessageAdded={handleMessageAdded}
                onSessionCreated={handleSessionCreated}
              />
            ) : (
              <ThinkMode
                currentSessionId={currentSessionId}
                messages={messages}
                setMessages={setMessages}
                onMessageAdded={handleMessageAdded}
                onSessionCreated={handleSessionCreated}
              />
            )}
          </main>
        </div>
      </div>
    </div>
  );
}

export default App;
