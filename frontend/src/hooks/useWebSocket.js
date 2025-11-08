/**
 * Custom React hook for WebSocket connection and streaming
 *
 * Provides real-time streaming from the backend agent
 */

import { useState, useEffect, useRef, useCallback } from 'react';

const WS_URL = 'ws://localhost:8000/ws/chat';

export const useWebSocket = (userId = 'default_user') => {
  const [isConnected, setIsConnected] = useState(false);
  const [streamingMessage, setStreamingMessage] = useState('');
  const [agentStatus, setAgentStatus] = useState(null);
  const [isStreaming, setIsStreaming] = useState(false);
  const [error, setError] = useState(null);
  const [metadata, setMetadata] = useState(null);

  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const streamingTextRef = useRef('');

  // Connect to WebSocket
  const connect = useCallback(() => {
    try {
      const ws = new WebSocket(`${WS_URL}?user_id=${userId}`);

      ws.onopen = () => {
        console.log('WebSocket connected');
        setIsConnected(true);
        setError(null);
      };

      ws.onmessage = (event) => {
        try {
          const message = JSON.parse(event.data);
          handleWebSocketMessage(message);
        } catch (err) {
          console.error('Error parsing WebSocket message:', err);
        }
      };

      ws.onerror = (error) => {
        console.error('WebSocket error:', error);
        setError('WebSocket connection error');
      };

      ws.onclose = () => {
        console.log('WebSocket disconnected');
        setIsConnected(false);

        // Attempt to reconnect after 3 seconds
        reconnectTimeoutRef.current = setTimeout(() => {
          console.log('Attempting to reconnect...');
          connect();
        }, 3000);
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('Error creating WebSocket:', err);
      setError('Failed to connect to WebSocket');
    }
  }, [userId]);

  // Handle incoming WebSocket messages
  const handleWebSocketMessage = (message) => {
    const { type, data } = message;

    switch (type) {
      case 'agent_start':
        setIsStreaming(true);
        setStreamingMessage('');
        streamingTextRef.current = '';
        setAgentStatus(data.status);
        setError(null);
        setMetadata(null);
        break;

      case 'agent_step':
        setAgentStatus(data.details || data.step);
        break;

      case 'tool_call':
        setAgentStatus(`🔧 Using tool: ${data.tool}`);
        break;

      case 'tool_result':
        if (data.success) {
          setAgentStatus(`✓ Tool completed: ${data.tool}`);
        } else {
          setAgentStatus(`✗ Tool failed: ${data.tool}`);
        }
        break;

      case 'llm_start':
        setAgentStatus(data.status || '💭 Generating response...');
        break;

      case 'llm_token':
        // Accumulate tokens for smooth streaming
        streamingTextRef.current += data.token;
        setStreamingMessage(streamingTextRef.current);
        break;

      case 'llm_end':
        setAgentStatus('✓ Response complete');
        break;

      case 'agent_complete':
        setIsStreaming(false);
        setAgentStatus(null);
        setStreamingMessage(data.result);
        setMetadata(data.metadata);
        break;

      case 'error':
        setIsStreaming(false);
        setError(data.error);
        setAgentStatus(`Error: ${data.error_type}`);
        break;

      default:
        console.log('Unknown message type:', type);
    }
  };

  // Send a query via WebSocket
  const sendQuery = useCallback((query, mode = 'chat', sessionId = null, saveHistory = true) => {
    if (!wsRef.current || wsRef.current.readyState !== WebSocket.OPEN) {
      setError('WebSocket is not connected');
      return false;
    }

    try {
      wsRef.current.send(JSON.stringify({
        query,
        mode,
        session_id: sessionId,
        save_history: saveHistory
      }));
      return true;
    } catch (err) {
      console.error('Error sending query:', err);
      setError('Failed to send query');
      return false;
    }
  }, []);

  // Disconnect WebSocket
  const disconnect = useCallback(() => {
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
    }
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    setIsConnected(false);
  }, []);

  // Connect on mount, disconnect on unmount
  useEffect(() => {
    connect();

    return () => {
      disconnect();
    };
  }, [connect, disconnect]);

  return {
    isConnected,
    isStreaming,
    streamingMessage,
    agentStatus,
    error,
    metadata,
    sendQuery,
    reconnect: connect,
    disconnect
  };
};
