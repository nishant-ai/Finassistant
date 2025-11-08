import { useState, useEffect, useRef } from 'react';
import MessageList from './MessageList';
import InputBox from './InputBox';
import StreamingMessage from './StreamingMessage';
import { sendReportQuery } from '../services/api';
import { addMessage, createSession } from '../services/chatHistory';
import { useWebSocket } from '../hooks/useWebSocket';
import { Brain, Download } from 'lucide-react';

const ThinkMode = ({ currentSessionId, messages, setMessages, onMessageAdded, onSessionCreated }) => {
  const [isLoading, setIsLoading] = useState(false);
  const [useStreaming, setUseStreaming] = useState(true); // Toggle for streaming mode
  const lastStreamedMessageRef = useRef(null); // Track the last streamed message to prevent duplicates

  // WebSocket hook for real-time streaming
  const {
    isConnected: wsConnected,
    isStreaming: wsStreaming,
    streamingMessage,
    agentStatus,
    error: wsError,
    metadata: wsMetadata,
    sendQuery: wsSendQuery
  } = useWebSocket();

  // Handle streaming completion - add final message to history (only once)
  useEffect(() => {
    if (!wsStreaming && streamingMessage && wsMetadata) {
      // Check if we've already added this message (prevent infinite loop)
      const messageKey = `${streamingMessage.substring(0, 50)}-${wsMetadata.session_id}`;

      if (lastStreamedMessageRef.current !== messageKey) {
        // Streaming completed, add the final message to messages
        const assistantMessage = {
          role: 'assistant',
          content: streamingMessage,
          timestamp: new Date().toISOString(),
          metadata: wsMetadata,
        };
        setMessages((prev) => [...prev, assistantMessage]);
        onMessageAdded?.();

        // Mark this message as added
        lastStreamedMessageRef.current = messageKey;
      }
    }
  }, [wsStreaming, streamingMessage, wsMetadata, setMessages, onMessageAdded]);

  const handleSendMessage = async (content) => {
    // Add user message to UI
    const userMessage = {
      role: 'user',
      content,
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);

    // Use WebSocket streaming if enabled and connected
    if (useStreaming && wsConnected) {
      // Send via WebSocket for real-time streaming (think mode)
      const success = wsSendQuery(content, 'think', currentSessionId, true);

      if (!success) {
        // Fallback to REST API if WebSocket send fails
        console.warn('WebSocket send failed, falling back to REST API');
        await handleRestApiMessage(content);
      }
    } else {
      // Fallback to REST API
      await handleRestApiMessage(content);
    }
  };

  // Fallback REST API handler (original logic)
  const handleRestApiMessage = async (content) => {
    setIsLoading(true);

    try {
      // Create session if doesn't exist
      let sessionId = currentSessionId;
      if (!sessionId) {
        try {
          // Use 'think' mode for ThinkMode sessions
          const newSession = await createSession('think', null);
          sessionId = newSession._id;
          onSessionCreated?.(sessionId);
        } catch (error) {
          console.error('Failed to create session:', error);
          // Continue without session - messages won't be saved
        }
      }

      // Save user message to database if we have a session
      if (sessionId) {
        await addMessage(sessionId, {
          role: 'user',
          content,
          metadata: null,
          is_error: false
        });
        onMessageAdded?.();
      }

      // Send to API (with verbose=true for detailed reports)
      const response = await sendReportQuery(content, true);

      // Add assistant response to UI
      const assistantMessage = {
        role: 'assistant',
        content: response.result,
        timestamp: response.timestamp,
        metadata: response.metadata,
      };
      setMessages((prev) => [...prev, assistantMessage]);

      // Save assistant response to database
      if (sessionId) {
        await addMessage(sessionId, {
          role: 'assistant',
          content: response.result,
          metadata: response.metadata,
          is_error: false
        });
        onMessageAdded?.();
      }
    } catch (error) {
      // Add error message to UI
      const errorMessage = {
        role: 'assistant',
        content: error.message,
        timestamp: new Date().toISOString(),
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);

      // Save error to database
      if (currentSessionId) {
        await addMessage(currentSessionId, {
          role: 'assistant',
          content: error.message,
          metadata: null,
          is_error: true
        });
        onMessageAdded?.();
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleExport = () => {
    if (messages.length === 0) return;

    // Generate markdown content
    let markdown = '# Financial Analysis\n\n';
    markdown += `Generated on: ${new Date().toLocaleString()}\n\n`;
    markdown += '---\n\n';

    messages.forEach((msg, idx) => {
      if (msg.role === 'user') {
        markdown += `## Query ${Math.floor(idx / 2) + 1}\n\n`;
        markdown += `**Question:** ${msg.content}\n\n`;
      } else if (msg.role === 'assistant' && !msg.isError) {
        markdown += `**Analysis:**\n\n${msg.content}\n\n`;
        if (msg.metadata?.execution_time_seconds) {
          markdown += `*Processing time: ${msg.metadata.execution_time_seconds}s*\n\n`;
        }
        markdown += '---\n\n';
      }
    });

    // Create and download file
    const blob = new Blob([markdown], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `financial-analysis-${new Date().getTime()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="flex flex-col h-full">
      <MessageList messages={messages} isLoading={isLoading || wsStreaming} mode="think" onSendMessage={handleSendMessage} />

      {/* Show streaming message component when WebSocket is streaming */}
      {wsStreaming && (
        <StreamingMessage
          message={streamingMessage}
          agentStatus={agentStatus}
          isStreaming={wsStreaming}
        />
      )}

      {/* Show WebSocket error if any */}
      {wsError && !wsStreaming && (
        <div className="error-banner">
          <span>⚠️ Connection error: {wsError}</span>
          <button onClick={() => window.location.reload()}>Reconnect</button>
        </div>
      )}

      <InputBox
        onSendMessage={handleSendMessage}
        isLoading={isLoading || wsStreaming}
        mode="think"
      />
    </div>
  );
};

export default ThinkMode;
