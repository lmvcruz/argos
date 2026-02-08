/**
 * TestSuiteTree - Test case tree view grouped by test suites.
 *
 * Displays test cases organized hierarchically by test suite/file.
 * Supports multiple selection of tests and suites for batch execution.
 */

import React, { useState } from 'react';
import { ChevronRight, ChevronDown, CheckSquare, Square, Zap, AlertCircle, CheckCircle, FileText } from 'lucide-react';
import '../styles/TreeStyles.css';

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
    <div className="tree-view">
      {suites.length > 0 ? (
        suites.map((suite) => {
          const isExpanded = expandedSuites.has(suite.id);
          const isFullySelected = isSuiteFullySelected(suite);
          const isPartiallySelected = isSuitePartiallySelected(suite);

          return (
            <div key={suite.id} className={`tree-node ${isFullySelected || isPartiallySelected ? 'selected' : ''}`}>
              {/* Suite Header */}
              <div className="tree-node-content" style={{ paddingLeft: 0 }}>
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    toggleSuite(suite.id);
                  }}
                  className="tree-toggle"
                >
                  {isExpanded ? (
                    <ChevronDown size={16} />
                  ) : (
                    <ChevronRight size={16} />
                  )}
                </button>

                <button
                  onClick={() => toggleSelection(suite.id, true)}
                  className={`tree-checkbox ${isFullySelected ? 'checked' : ''}`}
                >
                  {isFullySelected ? (
                    <CheckSquare size={16} />
                  ) : isPartiallySelected ? (
                    <div style={{
                      width: '16px',
                      height: '16px',
                      borderRadius: '2px',
                      border: '2px solid #2196f3',
                      backgroundColor: 'rgba(33, 150, 243, 0.2)'
                    }} />
                  ) : (
                    <Square size={16} />
                  )}
                </button>

                <div className="tree-icon test-file">
                  <FileText size={16} />
                </div>

                <div style={{ flex: 1, minWidth: 0 }}>
                  <div className="tree-label bold">
                    {suite.name}
                  </div>
                  <div style={{
                    fontSize: '11px',
                    color: '#999',
                    overflow: 'hidden',
                    textOverflow: 'ellipsis',
                    whiteSpace: 'nowrap',
                    fontFamily: 'monospace'
                  }}>
                    {suite.file}
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginLeft: 'auto', paddingLeft: '8px' }}>
                  <div className={`tree-status-icon tree-status-${suite.status || 'not-run'}`}>
                    {getStatusIcon(suite.status)}
                  </div>
                  <span className="tree-badge" style={{ margin: 0 }}>
                    {suite.tests.length}
                  </span>
                </div>
              </div>

              {/* Test Cases */}
              {isExpanded && (
                <div className="tree-children">
                  {suite.tests.map((test) => {
                    const isSelected = selectedItems.has(test.id);
                    return (
                      <div
                        key={test.id}
                        className={`tree-node ${isSelected ? 'selected' : ''}`}
                        style={{ paddingLeft: `32px` }}
                      >
                        <div className="tree-node-content">
                          <div className="tree-toggle-placeholder" />

                          <button
                            onClick={() => toggleSelection(test.id)}
                            className={`tree-checkbox ${isSelected ? 'checked' : ''}`}
                          >
                            {isSelected ? (
                              <CheckSquare size={14} />
                            ) : (
                              <Square size={14} />
                            )}
                          </button>

                          <div className={`tree-status-icon tree-status-${test.status || 'not-run'}`}>
                            {getStatusIcon(test.status)}
                          </div>

                          <span className="tree-label" style={{ fontFamily: 'monospace' }}>
                            {test.name}
                          </span>

                          {test.duration !== undefined && (
                            <span className="tree-badge" style={{ margin: 0 }}>
                              {test.duration}ms
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>
              )}
            </div>
          );
        })
      ) : (
        <div className="tree-empty">
          No test suites found
        </div>
      )}

      {selectedItems.size > 0 && (
        <div className="tree-footer">
          <span>
            {selectedItems.size} test{selectedItems.size !== 1 ? 's' : ''} selected
          </span>
        </div>
      )}
    </div>
  );
};
