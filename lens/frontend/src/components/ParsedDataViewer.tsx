/**
 * ParsedDataViewer component for displaying parsed test results
 * Shows results in table format with expandable error messages
 */

import { ChevronDown, ChevronRight } from 'lucide-react';
import React, { useState } from 'react';

export interface ParsedTestResult {
  name: string;
  status: 'passed' | 'failed' | 'skipped' | 'error';
  duration?: number;
  error?: string;
  output?: string;
}

export interface ParsedDataViewerProps {
  data: ParsedTestResult[] | null;
  loading?: boolean;
  height?: string;
}

function getStatusColor(status: string): string {
  switch (status) {
    case 'passed':
      return 'bg-green-50 dark:bg-green-950';
    case 'failed':
    case 'error':
      return 'bg-red-50 dark:bg-red-950';
    case 'skipped':
      return 'bg-gray-50 dark:bg-gray-900';
    default:
      return 'bg-gray-50 dark:bg-gray-900';
  }
}

function getStatusBadgeColor(status: string): string {
  switch (status) {
    case 'passed':
      return 'text-green-600 dark:text-green-400 font-semibold';
    case 'failed':
    case 'error':
      return 'text-red-600 dark:text-red-400 font-semibold';
    case 'skipped':
      return 'text-gray-600 dark:text-gray-400';
    default:
      return 'text-gray-600 dark:text-gray-400';
  }
}

export const ParsedDataViewer: React.FC<ParsedDataViewerProps> = ({
  data = null,
  loading = false,
  height = '400px',
}) => {
  const [expandedRows, setExpandedRows] = useState<Set<number>>(new Set());

  const toggleRow = (index: number) => {
    const newExpanded = new Set(expandedRows);
    if (newExpanded.has(index)) {
      newExpanded.delete(index);
    } else {
      newExpanded.add(index);
    }
    setExpandedRows(newExpanded);
  };

  if (loading) {
    return (
      <div
        className="flex items-center justify-center bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
        style={{ height }}
      >
        <span className="text-gray-500 dark:text-gray-400">Loading parsed data...</span>
      </div>
    );
  }

  if (!data || data.length === 0) {
    return (
      <div
        className="flex items-center justify-center bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700"
        style={{ height }}
      >
        <span className="text-gray-500 dark:text-gray-400">No parsed data available</span>
      </div>
    );
  }

  return (
    <div
      className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden flex flex-col"
      style={{ height }}
    >
      {/* Header */}
      <div className="bg-gray-50 dark:bg-gray-900 px-4 py-3 border-b border-gray-200 dark:border-gray-700">
        <h3 className="font-semibold text-gray-700 dark:text-gray-300">
          Parsed Test Results ({data.length})
        </h3>
      </div>

      {/* Results Table */}
      <div className="flex-1 overflow-auto">
        <table className="w-full border-collapse text-sm">
          <thead>
            <tr className="bg-gray-100 dark:bg-gray-700 border-b border-gray-200 dark:border-gray-600">
              <th className="px-4 py-2 text-left font-semibold text-gray-700 dark:text-gray-300 w-12" />
              <th className="px-4 py-2 text-left font-semibold text-gray-700 dark:text-gray-300">
                Test Name
              </th>
              <th className="px-4 py-2 text-left font-semibold text-gray-700 dark:text-gray-300 w-24">
                Status
              </th>
              <th className="px-4 py-2 text-left font-semibold text-gray-700 dark:text-gray-300 w-20">
                Duration (ms)
              </th>
            </tr>
          </thead>
          <tbody>
            {data.map((result, index) => {
              const isExpanded = expandedRows.has(index);
              const hasError = result.error || result.output;

              return (
                <React.Fragment key={index}>
                  {/* Main Row */}
                  <tr
                    className={`border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors ${getStatusColor(
                      result.status
                    )}`}
                  >
                    <td className="px-4 py-3 text-center">
                      {hasError && (
                        <button
                          onClick={() => toggleRow(index)}
                          className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                          title={isExpanded ? 'Collapse' : 'Expand'}
                        >
                          {isExpanded ? (
                            <ChevronDown size={16} />
                          ) : (
                            <ChevronRight size={16} />
                          )}
                        </button>
                      )}
                    </td>
                    <td className="px-4 py-3 font-mono text-xs break-words">
                      {result.name}
                    </td>
                    <td className={`px-4 py-3 font-semibold text-xs ${getStatusBadgeColor(result.status)}`}>
                      {result.status.charAt(0).toUpperCase() + result.status.slice(1)}
                    </td>
                    <td className="px-4 py-3 text-gray-600 dark:text-gray-400 text-xs">
                      {result.duration ? `${result.duration}ms` : '-'}
                    </td>
                  </tr>

                  {/* Expanded Error Details */}
                  {hasError && isExpanded && (
                    <tr className={`border-b border-gray-200 dark:border-gray-700 ${getStatusColor(result.status)}`}>
                      <td colSpan={4} className="px-4 py-3">
                        <div className="space-y-2">
                          {result.error && (
                            <div>
                              <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-1 text-xs">
                                Error Message
                              </h4>
                              <div className="bg-gray-900 dark:bg-gray-950 text-gray-100 p-3 rounded font-mono text-xs whitespace-pre-wrap break-words max-h-48 overflow-auto">
                                {result.error}
                              </div>
                            </div>
                          )}
                          {result.output && (
                            <div>
                              <h4 className="font-semibold text-gray-700 dark:text-gray-300 mb-1 text-xs">
                                Output
                              </h4>
                              <div className="bg-gray-900 dark:bg-gray-950 text-gray-100 p-3 rounded font-mono text-xs whitespace-pre-wrap break-words max-h-48 overflow-auto">
                                {result.output}
                              </div>
                            </div>
                          )}
                        </div>
                      </td>
                    </tr>
                  )}
                </React.Fragment>
              );
            })}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default ParsedDataViewer;
