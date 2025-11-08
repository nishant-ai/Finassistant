import React, { useState } from 'react';
import { Plus, MessageSquare, Brain, Trash2, Edit2, Check, X, ChevronLeft, ChevronRight } from 'lucide-react';

const ChatHistorySidebar = ({
  sessions,
  currentSessionId,
  onSelectSession,
  onNewSession,
  onDeleteSession,
  onUpdateSessionTitle,
  isOpen,
  onToggle,
  mode
}) => {
  const [editingSessionId, setEditingSessionId] = useState(null);
  const [editTitle, setEditTitle] = useState('');

  const handleStartEdit = (session) => {
    setEditingSessionId(session._id);
    setEditTitle(session.title);
  };

  const handleSaveEdit = async (sessionId) => {
    if (editTitle.trim()) {
      await onUpdateSessionTitle(sessionId, editTitle.trim());
    }
    setEditingSessionId(null);
    setEditTitle('');
  };

  const handleCancelEdit = () => {
    setEditingSessionId(null);
    setEditTitle('');
  };

  const formatDate = (dateString) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now - date;
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const filteredSessions = sessions.filter(s => s.mode === mode);

  return (
    <>
      {/* Toggle Button */}
      <button
        onClick={onToggle}
        className={`fixed top-20 z-20 p-2 bg-chat-surface border border-chat-border rounded-r-lg hover:bg-chat-input transition-all ${
          isOpen ? 'left-64' : 'left-0'
        }`}
      >
        {isOpen ? <ChevronLeft size={20} /> : <ChevronRight size={20} />}
      </button>

      {/* Sidebar */}
      <div
        className={`fixed left-0 top-16 h-[calc(100vh-4rem)] bg-chat-surface border-r border-chat-border transition-transform duration-300 z-10 ${
          isOpen ? 'translate-x-0' : '-translate-x-full'
        } w-64 flex flex-col`}
      >
        {/* New Chat Button */}
        <div className="p-3 border-b border-chat-border">
          <button
            onClick={onNewSession}
            className={`w-full flex items-center gap-2 px-4 py-2 rounded-lg font-medium transition-colors ${
              mode === 'chat'
                ? 'bg-accent-blue text-gray-900 hover:bg-accent-blue/90'
                : 'bg-accent-purple text-gray-900 hover:bg-accent-purple/90'
            }`}
          >
            <Plus size={18} />
            <span>New {mode === 'chat' ? 'Chat' : 'Thought'}</span>
          </button>
        </div>

        {/* Sessions List */}
        <div className="flex-1 overflow-y-auto">
          {filteredSessions.length === 0 ? (
            <div className="p-4 text-center text-chat-text-secondary text-sm">
              No {mode} sessions yet
            </div>
          ) : (
            <div className="p-2 space-y-1">
              {filteredSessions.map((session) => (
                <div
                  key={session._id}
                  className={`group relative rounded-lg transition-colors ${
                    currentSessionId === session._id
                      ? 'bg-chat-input'
                      : 'hover:bg-chat-input/50'
                  }`}
                >
                  {editingSessionId === session._id ? (
                    <div className="p-2 flex items-center gap-1">
                      <input
                        type="text"
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleSaveEdit(session._id);
                          if (e.key === 'Escape') handleCancelEdit();
                        }}
                        className="flex-1 px-2 py-1 text-sm bg-chat-bg border border-chat-border rounded text-chat-text outline-none focus:border-accent-blue"
                        autoFocus
                      />
                      <button
                        onClick={() => handleSaveEdit(session._id)}
                        className="p-1 text-green-400 hover:bg-chat-bg rounded"
                      >
                        <Check size={16} />
                      </button>
                      <button
                        onClick={handleCancelEdit}
                        className="p-1 text-red-400 hover:bg-chat-bg rounded"
                      >
                        <X size={16} />
                      </button>
                    </div>
                  ) : (
                    <button
                      onClick={() => onSelectSession(session._id)}
                      className="w-full text-left p-3"
                    >
                      <div className="flex items-start gap-2">
                        <div className="flex-shrink-0 mt-0.5">
                          {session.mode === 'chat' ? (
                            <MessageSquare size={16} className="text-accent-blue" />
                          ) : (
                            <Brain size={16} className="text-accent-purple" />
                          )}
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="text-sm text-chat-text truncate">
                            {session.title}
                          </div>
                          <div className="text-xs text-chat-text-secondary mt-0.5">
                            {formatDate(session.updated_at)} · {session.message_count} msgs
                          </div>
                        </div>
                      </div>
                      {/* Action Buttons */}
                      <div className="absolute right-2 top-2 hidden group-hover:flex gap-1">
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            handleStartEdit(session);
                          }}
                          className="p-1 text-chat-text-secondary hover:text-chat-text hover:bg-chat-bg rounded"
                          title="Rename"
                        >
                          <Edit2 size={14} />
                        </button>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            if (confirm('Delete this session?')) {
                              onDeleteSession(session._id);
                            }
                          }}
                          className="p-1 text-chat-text-secondary hover:text-red-400 hover:bg-chat-bg rounded"
                          title="Delete"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </button>
                  )}
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* Overlay for mobile */}
      {isOpen && (
        <div
          className="fixed inset-0 bg-black/50 z-0 lg:hidden"
          onClick={onToggle}
        />
      )}
    </>
  );
};

export default ChatHistorySidebar;
