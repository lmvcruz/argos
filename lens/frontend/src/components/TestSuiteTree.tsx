/**
 * TestSuiteTree - Test case tree view grouped by test suites.
 *
 * Displays test cases organized hierarchically by test suite/file.
 * Supports multiple selection of tests and suites for batch execution.
 */

import React, { useState } from 'react';
import { ChevronRight, ChevronDown, CheckSquare, Square, Zap, AlertCircle, CheckCircle } from 'lucide-react';

export interface TestCase {
  id: string;
  name: string;
  status?: 'passed' | 'failed' | 'skipped' | 'not-run';
  duration?: number;
}

export interface TestSuite {
  id: string;
  name: string;
  file: string;
  tests: TestCase[];
  totalDuration?: number;
  status?: 'passed' | 'failed' | 'mixed' | 'not-run';
}

export interface TestSuiteTreeProps {
  suites: TestSuite[];
  selectedItems?: Set<string>;
  onSelectionChange?: (selected: Set<string>) => void;
}

/**
 * TestSuiteTree component - Test cases grouped by suite.
 *
 * Displays test suites and their test cases in a collapsible tree structure.
 * Users can select individual tests or entire suites. Selection state is
 * tracked and returned via callback.
 *
 * Args:
 *   suites: Array of test suite objects with test cases
 *   selectedItems: Set of selected test/suite IDs
 *   onSelectionChange: Callback when selection changes
 */
export const TestSuiteTree: React.FC<TestSuiteTreeProps> = ({
  suites,
  selectedItems = new Set(),
  onSelectionChange,
}) => {
  const [expandedSuites, setExpandedSuites] = useState<Set<string>>(new Set());

  const toggleSuite = (id: string) => {
    const newExpanded = new Set(expandedSuites);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedSuites(newExpanded);
  };

  const toggleSelection = (id: string, isSuite: boolean = false) => {
    const newSelected = new Set(selectedItems);

    if (isSuite) {
      const suite = suites.find((s) => s.id === id);
      if (suite) {
        const testsInSuite = new Set(suite.tests.map((t) => t.id));
        const allSelected = suite.tests.every((t) => newSelected.has(t.id));

        if (allSelected) {
          testsInSuite.forEach((tid) => newSelected.delete(tid));
        } else {
          testsInSuite.forEach((tid) => newSelected.add(tid));
        }
      }
    } else {
      if (newSelected.has(id)) {
        newSelected.delete(id);
      } else {
        newSelected.add(id);
      }
    }

    onSelectionChange?.(newSelected);
  };

  const getStatusIcon = (status?: string) => {
    switch (status) {
      case 'passed':
        return <CheckCircle size={14} className="text-green-600 dark:text-green-400" />;
      case 'failed':
        return <AlertCircle size={14} className="text-red-600 dark:text-red-400" />;
      case 'skipped':
        return <Zap size={14} className="text-yellow-600 dark:text-yellow-400" />;
      default:
        return <div className="w-3.5 h-3.5 rounded border border-gray-400 dark:border-gray-600" />;
    }
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case 'passed':
        return 'text-green-700 dark:text-green-300';
      case 'failed':
        return 'text-red-700 dark:text-red-300';
      case 'skipped':
        return 'text-yellow-700 dark:text-yellow-300';
      default:
        return 'text-gray-700 dark:text-gray-300';
    }
  };

  const isSuiteFullySelected = (suite: TestSuite) => {
    return suite.tests.every((t) => selectedItems.has(t.id));
  };

  const isSuitePartiallySelected = (suite: TestSuite) => {
    return suite.tests.some((t) => selectedItems.has(t.id)) && !isSuiteFullySelected(suite);
  };

  return (
    <div className="space-y-1">
      {suites.length > 0 ? (
        suites.map((suite) => {
          const isExpanded = expandedSuites.has(suite.id);
          const isFullySelected = isSuiteFullySelected(suite);
          const isPartiallySelected = isSuitePartiallySelected(suite);

          return (
            <div key={suite.id} className="border border-gray-200 dark:border-gray-700 rounded">
              {/* Suite Header */}
              <div
                className={`flex items-center gap-2 py-2 px-3 rounded-t transition-colors ${
                  isFullySelected || isPartiallySelected
                    ? 'bg-blue-50 dark:bg-blue-900/20'
                    : 'bg-gray-50 dark:bg-gray-700/50 hover:bg-gray-100 dark:hover:bg-gray-700'
                }`}
              >
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleSuite(suite.id);
                  }}
                  className="p-0.5 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
                >
                  {isExpanded ? (
                    <ChevronDown size={16} className="text-gray-600 dark:text-gray-400" />
                  ) : (
                    <ChevronRight size={16} className="text-gray-600 dark:text-gray-400" />
                  )}
                </button>

                <button
                  onClick={() => toggleSelection(suite.id, true)}
                  className="p-0 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400"
                >
                  {isFullySelected ? (
                    <CheckSquare size={16} className="text-blue-600 dark:text-blue-400" />
                  ) : isPartiallySelected ? (
                    <div className="w-4 h-4 rounded border-2 border-blue-600 dark:border-blue-400 bg-blue-100 dark:bg-blue-900/40" />
                  ) : (
                    <Square size={16} />
                  )}
                </button>

                <div className="flex-1 min-w-0">
                  <div className="font-medium text-sm text-gray-900 dark:text-gray-100 truncate">
                    {suite.name}
                  </div>
                  <div className="text-xs text-gray-600 dark:text-gray-400 truncate font-mono">
                    {suite.file}
                  </div>
                </div>

                <div className="flex items-center gap-1 ml-auto pl-2">
                  {getStatusIcon(suite.status)}
                  <span className="text-xs text-gray-600 dark:text-gray-400">
                    {suite.tests.length}
                  </span>
                </div>
              </div>

              {/* Test Cases */}
              {isExpanded && (
                <div className="bg-white dark:bg-gray-800 border-t border-gray-200 dark:border-gray-700">
                  {suite.tests.map((test, idx) => {
                    const isSelected = selectedItems.has(test.id);
                    return (
                      <div
                        key={test.id}
                        className={`flex items-center gap-2 py-1.5 px-3 pl-8 text-sm ${
                          idx !== suite.tests.length - 1
                            ? 'border-b border-gray-100 dark:border-gray-700'
                            : ''
                        } ${
                          isSelected
                            ? 'bg-blue-50 dark:bg-blue-900/20'
                            : 'hover:bg-gray-50 dark:hover:bg-gray-700/50'
                        }`}
                      >
                        <button
                          onClick={() => toggleSelection(test.id)}
                          className="p-0 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400"
                        >
                          {isSelected ? (
                            <CheckSquare size={14} className="text-blue-600 dark:text-blue-400" />
                          ) : (
                            <Square size={14} />
                          )}
                        </button>

                        {getStatusIcon(test.status)}

                        <span className={`flex-1 truncate font-mono ${getStatusColor(test.status)}`}>
                          {test.name}
                        </span>

                        {test.duration !== undefined && (
                          <span className="text-xs text-gray-600 dark:text-gray-400 ml-auto">
                            {test.duration}ms
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })
      ) : (
        <div className="text-sm text-gray-500 dark:text-gray-400 py-6 text-center">
          No test suites found
        </div>
      )}

      {selectedItems.size > 0 && (
        <div className="text-xs text-gray-600 dark:text-gray-400 pt-2 border-t border-gray-200 dark:border-gray-700">
          {selectedItems.size} test{selectedItems.size !== 1 ? 's' : ''} selected
        </div>
      )}
    </div>
  );
};
