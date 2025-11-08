import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { User, Sparkles, AlertCircle } from 'lucide-react';

const Message = ({ message }) => {
  const isUser = message.role === 'user';
  const isError = message.isError;

  return (
    <div className={`py-6 ${isUser ? 'bg-chat-bg' : 'bg-chat-surface'} ${isError ? 'bg-red-900/20' : ''}`}>
      <div className="max-w-4xl mx-auto px-4 flex gap-4">
        {/* Avatar */}
        <div className={`flex-shrink-0 w-8 h-8 rounded-full flex items-center justify-center ${
          isUser
            ? 'bg-accent-blue'
            : isError
            ? 'bg-red-500'
            : 'bg-gradient-to-br from-accent-blue to-accent-purple'
        }`}>
          {isUser ? (
            <User size={18} className="text-gray-900" />
          ) : isError ? (
            <AlertCircle size={18} className="text-white" />
          ) : (
            <Sparkles size={18} className="text-white" />
          )}
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className={`text-sm font-medium mb-1 ${isError ? 'text-red-400' : 'text-chat-text'}`}>
            {isUser ? 'You' : isError ? 'Error' : 'Assistant'}
          </div>
          <div className={`prose prose-invert max-w-none ${isError ? 'text-red-300' : 'text-chat-text'}`}>
            {isUser ? (
              <p className="whitespace-pre-wrap">{message.content}</p>
            ) : (
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  // Custom rendering for code blocks
                  code: ({ node, inline, className, children, ...props }) => {
                    return inline ? (
                      <code className="bg-chat-input px-1.5 py-0.5 rounded text-sm" {...props}>
                        {children}
                      </code>
                    ) : (
                      <code className="block bg-chat-input p-3 rounded-lg text-sm overflow-x-auto" {...props}>
                        {children}
                      </code>
                    );
                  },
                  // Custom rendering for links
                  a: ({ node, children, ...props }) => (
                    <a className="text-accent-blue hover:underline" target="_blank" rel="noopener noreferrer" {...props}>
                      {children}
                    </a>
                  ),
                  // Custom rendering for lists
                  ul: ({ node, children, ...props }) => (
                    <ul className="list-disc list-inside space-y-1" {...props}>
                      {children}
                    </ul>
                  ),
                  ol: ({ node, children, ...props }) => (
                    <ol className="list-decimal list-inside space-y-1" {...props}>
                      {children}
                    </ol>
                  ),
                  // Custom rendering for tables
                  table: ({ node, children, ...props }) => (
                    <div className="overflow-x-auto">
                      <table className="min-w-full border border-chat-border" {...props}>
                        {children}
                      </table>
                    </div>
                  ),
                  th: ({ node, children, ...props }) => (
                    <th className="border border-chat-border px-4 py-2 bg-chat-input" {...props}>
                      {children}
                    </th>
                  ),
                  td: ({ node, children, ...props }) => (
                    <td className="border border-chat-border px-4 py-2" {...props}>
                      {children}
                    </td>
                  ),
                }}
              >
                {message.content}
              </ReactMarkdown>
            )}
          </div>

          {/* Metadata */}
          {message.metadata && (
            <div className="mt-2 text-xs text-chat-text-secondary">
              {message.metadata.execution_time_seconds && (
                <span>Completed in {message.metadata.execution_time_seconds}s</span>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default Message;
