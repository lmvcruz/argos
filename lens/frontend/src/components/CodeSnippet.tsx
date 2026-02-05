/**
 * CodeSnippet component for displaying syntax-highlighted code blocks
 * Supports copy-to-clipboard functionality
 */

import { Copy, Check } from 'lucide-react';
import { useState } from 'react';

interface CodeSnippetProps {
  code: string;
  language?: string;
  lineNumbers?: boolean;
  maxHeight?: string;
}

export function CodeSnippet({
  code,
  language = 'text',
  lineNumbers = false,
  maxHeight = '400px',
}: CodeSnippetProps) {
  const [copied, setCopied] = useState(false);

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(code);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const lines = code.split('\n');

  return (
    <div className="bg-gray-900 text-gray-100 rounded-lg overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 bg-gray-800 border-b border-gray-700">
        <span className="text-sm font-semibold text-gray-400">{language}</span>
        <button
          onClick={handleCopy}
          className="p-1 hover:bg-gray-700 rounded transition-colors"
          title="Copy to clipboard"
        >
          {copied ? (
            <Check size={18} className="text-green-400" />
          ) : (
            <Copy size={18} className="text-gray-400" />
          )}
        </button>
      </div>
      <pre
        className="overflow-auto p-4 font-mono text-sm"
        style={{ maxHeight }}
      >
        {lineNumbers ? (
          <div className="flex gap-4">
            <div className="text-gray-600 select-none">
              {lines.map((_, i) => (
                <div key={i}>{i + 1}</div>
              ))}
            </div>
            <code>{code}</code>
          </div>
        ) : (
          <code>{code}</code>
        )}
      </pre>
    </div>
  );
}
