import React, { useEffect, useState } from 'react';
import { BarChart3, AlertTriangle, TrendingDown, RefreshCw } from 'lucide-react';
import { useScout } from '../../contexts/ScoutContext';

/**
 * AnalysisPanel
 *
 * Analyze failure patterns in CI data.
 * Shows statistics and identified patterns by type.
 */

const AnalysisPanel: React.FC = () => {
  const {
    analysis,
    analysisLoading,
    analysisError,
    filters,
    setFilters,
    fetchAnalysis,
  } = useScout();

  const [expandedPattern, setExpandedPattern] = useState<string | null>(null);

  // Load analysis on mount and when filters change
  useEffect(() => {
    fetchAnalysis();
  }, [filters.analysisWindow, fetchAnalysis]);

  const handleWindowChange = (days: number) => {
    setFilters({ analysisWindow: days });
  };

  const getPatternColor = (type: string) => {
    const colors: Record<string, string> = {
      timeout: 'bg-red-50 text-red-700 border-red-200',
      'platform-specific': 'bg-orange-50 text-orange-700 border-orange-200',
      setup: 'bg-yellow-50 text-yellow-700 border-yellow-200',
      dependency: 'bg-blue-50 text-blue-700 border-blue-200',
    };
    return colors[type] || 'bg-gray-50 text-gray-700 border-gray-200';
  };

  const getPatternIcon = (type: string) => {
    const icons: Record<string, string> = {
      timeout: '⏱️',
      'platform-specific': '🖥️',
      setup: '⚙️',
      dependency: '📦',
    };
    return icons[type] || '📊';
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Header */}
      <div className="px-8 py-6 border-b border-gray-200 bg-gradient-to-r from-blue-50 to-indigo-50">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
              <BarChart3 className="w-6 h-6" />
              Failure Analysis
            </h2>
            <p className="text-sm text-gray-600 mt-1">
              Identify failure patterns and their root causes
            </p>
          </div>

          <button
            onClick={() => fetchAnalysis()}
            disabled={analysisLoading}
            className="flex items-center gap-2 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors"
          >
            <RefreshCw className={`w-4 h-4 ${analysisLoading ? 'animate-spin' : ''}`} />
            Refresh
          </button>
        </div>
      </div>

      {/* Controls */}
      <div className="px-8 py-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center gap-4">
          <span className="text-sm font-medium text-gray-700">Analysis Window:</span>
          <div className="flex items-center gap-2">
            {[7, 14, 30, 60].map((days) => (
              <button
                key={days}
                onClick={() => handleWindowChange(days)}
                className={`px-3 py-1 rounded-lg text-sm font-medium transition-colors ${
                  filters.analysisWindow === days
                    ? 'bg-blue-600 text-white'
                    : 'bg-white border border-gray-300 text-gray-700 hover:bg-gray-50'
                }`}
              >
                {days}d
              </button>
            ))}
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="flex-1 overflow-y-auto">
        {analysisLoading ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
              <p className="text-gray-600">Analyzing failures...</p>
            </div>
          </div>
        ) : analysisError ? (
          <div className="p-8">
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <p className="text-red-700 font-medium">Error loading analysis</p>
              <p className="text-red-600 text-sm mt-1">{analysisError}</p>
            </div>
          </div>
        ) : !analysis ? (
          <div className="flex items-center justify-center h-full">
            <p className="text-gray-500">No analysis data available</p>
          </div>
        ) : (
          <div className="p-8 space-y-8">
            {/* Statistics */}
            <div className="grid grid-cols-4 gap-4">
              <div className="bg-gradient-to-br from-blue-50 to-blue-100 border border-blue-200 rounded-lg p-6">
                <div className="text-3xl font-bold text-blue-900">{analysis.total_runs}</div>
                <div className="text-sm text-blue-700 mt-2">Total Runs</div>
              </div>

              <div className="bg-gradient-to-br from-green-50 to-green-100 border border-green-200 rounded-lg p-6">
                <div className="text-3xl font-bold text-green-900">{analysis.successful_runs}</div>
                <div className="text-sm text-green-700 mt-2">Successful</div>
              </div>

              <div className="bg-gradient-to-br from-red-50 to-red-100 border border-red-200 rounded-lg p-6">
                <div className="text-3xl font-bold text-red-900">{analysis.failed_runs}</div>
                <div className="text-sm text-red-700 mt-2">Failed</div>
              </div>

              <div className="bg-gradient-to-br from-purple-50 to-purple-100 border border-purple-200 rounded-lg p-6">
                <div className="text-3xl font-bold text-purple-900">
                  {Math.round(analysis.success_rate)}%
                </div>
                <div className="text-sm text-purple-700 mt-2">Success Rate</div>
              </div>
            </div>

            {/* Failure Patterns */}
            <div>
              <h3 className="text-lg font-bold text-gray-900 mb-4 flex items-center gap-2">
                <AlertTriangle className="w-5 h-5 text-orange-500" />
                Failure Patterns
              </h3>

              <div className="space-y-3">
                {Object.entries(analysis.patterns).map(([type, patterns]) => {
                  if (!Array.isArray(patterns) || patterns.length === 0) return null;

                  const isExpanded = expandedPattern === type;
                  const patternCount = patterns.length;

                  return (
                    <div
                      key={type}
                      className={`border rounded-lg ${getPatternColor(type)}`}
                    >
                      {/* Pattern Header */}
                      <button
                        onClick={() =>
                          setExpandedPattern(isExpanded ? null : type)
                        }
                        className="w-full px-6 py-4 flex items-center justify-between hover:opacity-80 transition-opacity"
                      >
                        <div className="flex items-center gap-3">
                          <span className="text-xl">{getPatternIcon(type)}</span>
                          <div className="text-left">
                            <div className="font-semibold capitalize">
                              {type.replace('-', ' ')}
                            </div>
                            <div className="text-sm opacity-75">
                              {patternCount} pattern{patternCount !== 1 ? 's' : ''}
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center gap-2">
                          <span className="text-2xl font-bold">{patternCount}</span>
                          <svg
                            className={`w-5 h-5 transition-transform ${
                              isExpanded ? 'rotate-180' : ''
                            }`}
                            fill="none"
                            stroke="currentColor"
                            viewBox="0 0 24 24"
                          >
                            <path
                              strokeLinecap="round"
                              strokeLinejoin="round"
                              strokeWidth={2}
                              d="M19 14l-7 7m0 0l-7-7m7 7V3"
                            />
                          </svg>
                        </div>
                      </button>

                      {/* Pattern Details */}
                      {isExpanded && (
                        <div className="border-t px-6 py-4 space-y-3">
                          {patterns.map((pattern: any, idx) => (
                            <div
                              key={idx}
                              className="bg-white/50 rounded p-3"
                            >
                              <div className="font-medium text-gray-900">
                                {pattern.test_nodeid}
                              </div>
                              <div className="text-sm opacity-75 mt-1">
                                {pattern.description}
                              </div>
                              {pattern.count && (
                                <div className="text-xs opacity-60 mt-2">
                                  Occurred {pattern.count} time{pattern.count !== 1 ? 's' : ''}
                                </div>
                              )}
                              {pattern.suggested_fix && (
                                <div className="text-xs mt-2 p-2 bg-green-50/50 rounded">
                                  💡 {pattern.suggested_fix}
                                </div>
                              )}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  );
                })}

                {Object.values(analysis.patterns).every(
                  (p) => !Array.isArray(p) || p.length === 0
                ) && (
                  <div className="text-center py-8">
                    <p className="text-gray-500">
                      No failure patterns detected in this window
                    </p>
                    <p className="text-sm text-gray-400 mt-1">
                      Excellent! All tests are passing.
                    </p>
                  </div>
                )}
              </div>
            </div>

            {/* Summary */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
              <h4 className="font-semibold text-blue-900 mb-2">Summary</h4>
              <p className="text-blue-800 text-sm">
                Over the last {analysis.window_days} days, {analysis.total_runs} workflow runs
                were analyzed. {analysis.failed_runs} runs failed, resulting in {
                  Object.values(analysis.patterns).flat().length
                }{' '}
                unique failure patterns. {
                  Object.values(analysis.patterns).flat().length > 0
                    ? 'Review the patterns above to understand root causes.'
                    : 'Keep up the great work!'
                }
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default AnalysisPanel;
