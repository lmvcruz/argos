/**
 * LogViewer component for displaying raw log content
 * Supports line numbers, scrolling, copying, and downloading
 */

import { Copy, Download } from 'lucide-react';
import { useState } from 'react';

export interface LogViewerProps {
  content: string | null;
  loading?: boolean;
  height?: string;
}

export const LogViewer: React.FC<LogViewerProps> = ({
  content = '',
  loading = false,
  height = '400px',
}) => {
  const [copied, setCopied] = useState(false);

  const handleCopy = () => {
    if (content) {
      navigator.clipboard.writeText(content);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const handleDownload = () => {
    if (!content) return;

    const element = document.createElement('a');
    const file = new Blob([content], { type: 'text/plain' });
    element.href = URL.createObjectURL(file);
    element.download = `log-${new Date().toISOString()}.txt`;
    document.body.appendChild(element);
    element.click();
    document.body.removeChild(element);
  };

  const lines = content ? content.split('\n') : [];

  return (
    <div className="flex flex-col h-full border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between bg-gray-50 dark:bg-gray-900 px-4 py-2 border-b border-gray-200 dark:border-gray-700">
        <h3 className="font-semibold text-gray-700 dark:text-gray-300">Raw Log Output</h3>
        <div className="flex gap-2">
          <button
            onClick={handleCopy}
            title="Copy log content"
            className="p-2 hover:bg-gray-200 dark:hover:bg-gray-800 rounded transition-colors"
          >
            <Copy size={16} className={copied ? 'text-green-600' : 'text-gray-600'} />
          </button>
          <button
            onClick={handleDownload}
            title="Download log file"
            className="p-2 hover:bg-gray-200 dark:hover:bg-gray-800 rounded transition-colors"
          >
            <Download size={16} className="text-gray-600 dark:text-gray-400" />
          </button>
        </div>
      </div>

      {/* Log Content */}
      <div
        className="flex-1 overflow-auto bg-gray-950 text-gray-100 font-mono text-sm"
        style={{ height }}
      >
        {loading ? (
          <div className="flex items-center justify-center h-full text-gray-400">
            <span>Loading log content...</span>
          </div>
        ) : !content || lines.length === 0 ? (
          <div className="flex items-center justify-center h-full text-gray-500">
            <span>No log content available</span>
          </div>
        ) : (
          <div className="p-4">
            <table className="w-full border-collapse">
              <tbody>
                {lines.map((line, index) => (
                  <tr key={index} className="hover:bg-gray-800 transition-colors">
                    <td className="text-right pr-4 text-gray-600 select-none w-12">
                      {index + 1}
                    </td>
                    <td className="font-mono break-words">
                      {line || '\u00A0'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};

export default LogViewer;
