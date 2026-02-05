/**
 * OutputPanel component for displaying real-time output streams
 * Supports auto-scrolling and log level filtering
 */

import { Copy, Download, Trash2 } from 'lucide-react';
import { useRef, useEffect, useState } from 'react';

export interface LogEntry {
  timestamp: string;
  level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
}

interface OutputPanelProps {
  logs: LogEntry[];
  isLive?: boolean;
  maxHeight?: string;
  showTimestamp?: boolean;
  filterLevel?: LogEntry['level'] | 'all';
  onClear?: () => void;
}

const levelConfig: Record<LogEntry['level'], { bg: string; text: string }> = {
  debug: { bg: 'bg-gray-100 dark:bg-gray-800', text: 'text-gray-700 dark:text-gray-300' },
  info: { bg: 'bg-blue-50 dark:bg-blue-900/30', text: 'text-blue-700 dark:text-blue-300' },
  warn: { bg: 'bg-yellow-50 dark:bg-yellow-900/30', text: 'text-yellow-700 dark:text-yellow-300' },
  error: { bg: 'bg-red-50 dark:bg-red-900/30', text: 'text-red-700 dark:text-red-300' },
};

export function OutputPanel({
  logs,
  isLive = false,
  maxHeight = '500px',
  showTimestamp = true,
  filterLevel = 'all',
  onClear,
}: OutputPanelProps) {
  const scrollRef = useRef<HTMLDivElement>(null);
  const [copied, setCopied] = useState(false);

  useEffect(() => {
    if (isLive && scrollRef.current) {
      scrollRef.current.scrollTop = scrollRef.current.scrollHeight;
    }
  }, [logs, isLive]);

  const filteredLogs =
    filterLevel === 'all'
      ? logs
      : logs.filter((log) => log.level === filterLevel);

  const allText = filteredLogs
    .map((log) => {
      const parts = [];
      if (showTimestamp) parts.push(`[${log.timestamp}]`);
      parts.push(`[${log.level.toUpperCase()}]`);
      parts.push(log.message);
      return parts.join(' ');
    })
    .join('\n');

  const handleCopy = async () => {
    try {
      await navigator.clipboard.writeText(allText);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const handleDownload = () => {
    const element = document.createElement('a');
    element.setAttribute(
      'href',
      'data:text/plain;charset=utf-8,' + encodeURIComponent(allText)
    );
    element.setAttribute('download', 'output.log');
    element.style.display = 'none';
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  return (
    <div className="flex flex-col bg-white dark:bg-gray-900 border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
        <span className="text-sm font-semibold text-gray-700 dark:text-gray-300">
          Output {filteredLogs.length > 0 && `(${filteredLogs.length})`}
        </span>
        <div className="flex gap-2">
          <button
            onClick={handleCopy}
            className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
            title="Copy to clipboard"
          >
            <Copy size={16} className="text-gray-600 dark:text-gray-400" />
          </button>
          <button
            onClick={handleDownload}
            className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
            title="Download logs"
          >
            <Download size={16} className="text-gray-600 dark:text-gray-400" />
          </button>
          {onClear && (
            <button
              onClick={onClear}
              className="p-1 hover:bg-gray-200 dark:hover:bg-gray-700 rounded transition-colors"
              title="Clear logs"
            >
              <Trash2 size={16} className="text-gray-600 dark:text-gray-400" />
            </button>
          )}
        </div>
      </div>
      <div
        ref={scrollRef}
        className="overflow-auto font-mono text-xs flex-1"
        style={{ maxHeight }}
      >
        {filteredLogs.length === 0 ? (
          <div className="p-4 text-gray-500 dark:text-gray-400">
            No logs available
          </div>
        ) : (
          filteredLogs.map((log, idx) => {
            const config = levelConfig[log.level];
            return (
              <div
                key={idx}
                className={`px-4 py-2 border-b border-gray-200 dark:border-gray-800 ${config.bg} ${config.text} whitespace-pre-wrap break-words`}
              >
                {showTimestamp && (
                  <span className="text-gray-500 dark:text-gray-500">
                    [{log.timestamp}]{' '}
                  </span>
                )}
                <span className="font-semibold">
                  [{log.level.toUpperCase()}]{' '}
                </span>
                {log.message}
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
