/**
 * Local Tests scenario page
 *
 * Two-column layout for test discovery and execution:
 * - Left: Switchable view between file tree and test suites
 * - Right: Test runner with execution and statistics
 */

import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  XCircle,
  BarChart3,
  ListIcon,
} from 'lucide-react';
import {
  TestFileTree,
  TestSuiteTree,
  TestRunner,
  TestStatistics,
  type FileTreeNode,
  type TestSuite,
  type TestCase,
  type TestResult,
} from '../components';
import { useConfig } from '../config/ConfigContext';
import './LocalTests.css';

type LeftViewMode = 'tree' | 'suites';
type RightViewMode = 'runner' | 'statistics';

/**
 * LocalTests page - Test discovery, execution, and analysis
 *
 * Provides two-column interface:
 * - Left panel: Switch between file tree view and test suite view
 * - Right panel: Switch between test runner and statistics view
 */
export default function LocalTests() {
  const { isFeatureEnabled, getConfig } = useConfig();

  // State management
  const [leftView, setLeftView] = useState<LeftViewMode>('suites');
  const [rightView, setRightView] = useState<RightViewMode>('runner');
  const [selectedTests, setSelectedTests] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string>('');

  // Data state
  const [fileTree, setFileTree] = useState<FileTreeNode[]>([]);
  const [testSuites, setTestSuites] = useState<TestSuite[]>([]);
  const [loading, setLoading] = useState(false);

  // Load test data on mount
  useEffect(() => {
    const loadTests = async () => {
      setLoading(true);
      setError('');

      try {
        const projectPath = getConfig('tools.verdict.projectPath') || 'd:\\playground\\argos';

        // TODO: Replace with actual API calls to test_service
        // For now, we'll use mock data
        const mockSuites: TestSuite[] = [
          {
            id: 'suite-1',
            name: 'test_validators',
            file: 'tests/test_validators.py',
            tests: [
              { id: 'test-1', name: 'test_black_validator', status: 'not-run' },
              { id: 'test-2', name: 'test_flake8_validator', status: 'not-run' },
              { id: 'test-3', name: 'test_isort_validator', status: 'not-run' },
            ],
            status: 'not-run',
          },
          {
            id: 'suite-2',
            name: 'test_storage',
            file: 'tests/test_storage.py',
            tests: [
              { id: 'test-4', name: 'test_database_connection', status: 'not-run' },
              { id: 'test-5', name: 'test_save_configuration', status: 'not-run' },
            ],
            status: 'not-run',
          },
        ];

        setTestSuites(mockSuites);

        // Mock file tree
        const mockFileTree: FileTreeNode[] = [
          {
            id: 'folder-tests',
            name: 'tests',
            path: 'tests',
            type: 'folder',
            children: [
              {
                id: 'file-validators',
                name: 'test_validators.py',
                path: 'tests/test_validators.py',
                type: 'file',
                isTestFile: true,
              },
              {
                id: 'file-storage',
                name: 'test_storage.py',
                path: 'tests/test_storage.py',
                type: 'file',
                isTestFile: true,
              },
            ],
          },
        ];

        setFileTree(mockFileTree);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load tests');
      } finally {
        setLoading(false);
      }
    };

    if (isFeatureEnabled('localTests')) {
      loadTests();
    }
  }, [isFeatureEnabled, getConfig]);

  // Handle test execution
  const handleRunTests = async (selectedIds: Set<string>): Promise<TestResult[]> => {
    setLoading(true);
    try {
      // TODO: Replace with actual API call to test_service.execute()
      // For now, return mock results
      const results: TestResult[] = Array.from(selectedIds).map((id, idx) => ({
        id,
        name: `test_${idx + 1}`,
        status: Math.random() > 0.2 ? 'passed' : 'failed',
        duration: Math.floor(Math.random() * 1000) + 100,
        error: Math.random() > 0.2 ? undefined : 'AssertionError: expected 2 to equal 3',
        output: 'test output...',
      }));

      return results;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Test execution failed');
      return [];
    } finally {
      setLoading(false);
    }
  };

  // Handle statistics loading
  const handleLoadStatistics = async () => {
    // TODO: Replace with actual API call to test_service.get_statistics()
    try {
      // Mock statistics
      const stats = [
        {
          date: '2024-02-01',
          totalTests: 10,
          passedTests: 8,
          failedTests: 2,
          skippedTests: 0,
          averageDuration: 150,
          totalDuration: 1500,
          passRate: 80,
        },
        {
          date: '2024-02-02',
          totalTests: 10,
          passedTests: 9,
          failedTests: 1,
          skippedTests: 0,
          averageDuration: 145,
          totalDuration: 1450,
          passRate: 90,
        },
      ];
      return stats;
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load statistics');
      return [];
    }
  };

  if (!isFeatureEnabled('localTests')) {
    return (
      <div className="p-6">
        <div className="bg-yellow-50 dark:bg-yellow-900/30 border border-yellow-200 dark:border-yellow-700 rounded-lg p-4">
          <AlertTriangle className="inline mr-2 text-yellow-600" size={20} />
          <span className="text-yellow-800 dark:text-yellow-200">
            Local Tests feature is disabled in configuration
          </span>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-4">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold mb-2">Local Tests</h1>
        <p className="text-gray-600 dark:text-gray-400">
          Discover, execute, and analyze local test execution results
        </p>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 dark:bg-red-900/30 border border-red-200 dark:border-red-700 rounded-lg p-4 flex items-start gap-3">
          <XCircle className="text-red-600 flex-shrink-0 mt-0.5" size={20} />
          <div>
            <p className="font-semibold text-red-800 dark:text-red-200">Error</p>
            <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
          </div>
        </div>
      )}

      {/* Two-Column Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* LEFT COLUMN - Test Discovery */}
        <div className="space-y-4">
          {/* View Mode Selector */}
          <div className="flex gap-2 p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
            <button
              onClick={() => setLeftView('suites')}
              className={`flex-1 px-3 py-2 rounded font-medium text-sm transition-colors flex items-center justify-center gap-2 ${
                leftView === 'suites'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              <BarChart3 size={16} />
              Test Suites
            </button>
            <button
              onClick={() => setLeftView('tree')}
              className={`flex-1 px-3 py-2 rounded font-medium text-sm transition-colors flex items-center justify-center gap-2 ${
                leftView === 'tree'
                  ? 'bg-blue-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              <ListIcon size={16} />
              File Tree
            </button>
          </div>

          {/* Left Panel Content */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            {leftView === 'suites' ? (
              <TestSuiteTree
                suites={testSuites}
                selectedItems={selectedTests}
                onSelectionChange={setSelectedTests}
              />
            ) : (
              <TestFileTree
                nodes={fileTree}
                selectedItems={selectedTests}
                onSelectionChange={setSelectedTests}
              />
            )}
          </div>
        </div>

        {/* RIGHT COLUMN - Test Execution & Statistics */}
        <div className="space-y-4">
          {/* View Mode Selector */}
          <div className="flex gap-2 p-3 bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
            <button
              onClick={() => setRightView('runner')}
              className={`flex-1 px-3 py-2 rounded font-medium text-sm transition-colors ${
                rightView === 'runner'
                  ? 'bg-green-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              Run Tests
            </button>
            <button
              onClick={() => setRightView('statistics')}
              className={`flex-1 px-3 py-2 rounded font-medium text-sm transition-colors ${
                rightView === 'statistics'
                  ? 'bg-purple-600 text-white'
                  : 'bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 hover:bg-gray-200 dark:hover:bg-gray-600'
              }`}
            >
              Statistics
            </button>
          </div>

          {/* Right Panel Content */}
          <div className="bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4">
            {rightView === 'runner' ? (
              <TestRunner
                selectedTests={selectedTests}
                testCount={testSuites.reduce((sum, s) => sum + s.tests.length, 0)}
                onRun={handleRunTests}
                loading={loading}
              />
            ) : (
              <TestStatistics
                onLoadStats={handleLoadStatistics}
                isLoading={loading}
              />
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
