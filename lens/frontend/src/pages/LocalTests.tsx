/**
 * Local Tests page - Test discovery, execution, and analysis
 *
 * Two-column layout similar to LocalInspection:
 * - Left: Switchable view between file tree and test suites with collapsible sections
 * - Right: Test runner with execution and statistics
 */

import React, { useState, useEffect } from 'react';
import {
  AlertTriangle,
  XCircle,
  BarChart3,
  ListIcon,
  ChevronUp,
  ChevronDown,
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
import { useProjects } from '../contexts/ProjectContext';
import '../styles/TreeStyles.css';
import './LocalTests.css';

type LeftViewMode = 'tree' | 'suites';
type RightViewMode = 'runner' | 'statistics';

/**
 * LocalTests page - Test discovery, execution, and analysis
 *
 * Provides two-column interface with collapsible sections:
 * - Left panel: Switch between file tree view and test suite view
 * - Right panel: Switch between test runner and statistics view
 */
export default function LocalTests() {
  const { isFeatureEnabled } = useConfig();
  const { activeProject } = useProjects();

  // State management
  const [leftView, setLeftView] = useState<LeftViewMode>('suites');
  const [rightView, setRightView] = useState<RightViewMode>('runner');
  const [selectedTests, setSelectedTests] = useState<Set<string>>(new Set());
  const [error, setError] = useState<string>('');

  // Collapsible sections state
  const [leftSectionExpanded, setLeftSectionExpanded] = useState(true);
  const [rightSectionExpanded, setRightSectionExpanded] = useState(true);

  // Data state
  const [fileTree, setFileTree] = useState<FileTreeNode[]>([]);
  const [testSuites, setTestSuites] = useState<TestSuite[]>([]);
  const [loading, setLoading] = useState(false);

  /**
   * Load file tree from project
   */
  useEffect(() => {
    if (!activeProject) {
      setFileTree([]);
      return;
    }

    const loadFileTree = async () => {
      try {
        // Fetch file tree from backend
        const response = await fetch(
          `/api/inspection/files?path=${encodeURIComponent(activeProject.local_folder)}`
        );
        if (!response.ok) throw new Error('Failed to load files');

        const data = await response.json();
        setFileTree(data.files || []);
      } catch (error) {
        console.error('Error loading file tree:', error);
        setFileTree([]);
      }
    };

    loadFileTree();
  }, [activeProject]);

  /**
   * Load test data on mount
   */
  useEffect(() => {
    const loadTests = async () => {
      setLoading(true);
      setError('');

      if (!activeProject) {
        setTestSuites([]);
        setLoading(false);
        return;
      }

      try {
        // Fetch test suites from discovery endpoint
        const response = await fetch(
          `/api/tests/discover?path=${encodeURIComponent(activeProject.local_folder)}`
        );
        if (!response.ok) {
          throw new Error('Failed to discover tests');
        }

        const data = await response.json();
        setTestSuites(data.suites || []);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load tests');
        setTestSuites([]);
      } finally {
        setLoading(false);
      }
    };

    if (isFeatureEnabled('localTests')) {
      loadTests();
    }
  }, [isFeatureEnabled, activeProject]);

  // Handle test execution
  const handleRunTests = async (selectedIds: Set<string>): Promise<TestResult[]> => {
    setLoading(true);
    try {
      // Call test_service.execute() API
      const response = await fetch('/api/tests/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ test_ids: Array.from(selectedIds) }),
      });

      if (!response.ok) {
        throw new Error('Test execution failed');
      }

      const data = await response.json();
      return data.results || [];
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Test execution failed');
      return [];
    } finally {
      setLoading(false);
    }
  };

  // Handle statistics loading
  const handleLoadStatistics = async () => {
    try {
      // Call test_service.get_statistics() API
      const response = await fetch('/api/tests/statistics');
      if (!response.ok) {
        throw new Error('Failed to load statistics');
      }

      const data = await response.json();
      return data.statistics || [];
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load statistics');
      return [];
    }
  };

  if (!isFeatureEnabled('localTests')) {
    return (
      <div className="local-tests-no-feature">
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
    <div className="local-tests-page">
      {/* Header with title */}
      <div className="tests-header">
        <div>
          <h1 className="tests-title">Local Tests</h1>
          <p className="tests-subtitle">
            Discover, execute, and analyze local test execution results
          </p>
        </div>
      </div>

      {/* Error Message */}
      {error && (
        <div className="tests-error">
          <XCircle className="text-red-600 flex-shrink-0" size={20} />
          <div>
            <p className="font-semibold text-red-800 dark:text-red-200">Error</p>
            <p className="text-sm text-red-700 dark:text-red-300">{error}</p>
          </div>
        </div>
      )}

      {/* No Project Selected */}
      {!activeProject && (
        <div className="local-tests-no-feature">
          <AlertTriangle size={48} className="text-gray-400" />
          <h2>No Project Selected</h2>
          <p>Please select a project from the navigation to view and run tests.</p>
        </div>
      )}

      {/* Two-Column Layout */}
      {activeProject && (
        <div className="tests-container">
        {/* LEFT PANEL - Test Discovery */}
        <div className="left-panel">
          {/* Left Panel Header with View Mode Selector */}
          <div className="panel-header">
            <div className="header-title">
              <h2>Test Discovery</h2>
            </div>
            <div className="view-mode-buttons">
              <button
                onClick={() => setLeftView('suites')}
                className={`view-btn ${leftView === 'suites' ? 'active' : ''}`}
                title="Test Suites view"
              >
                <BarChart3 size={16} />
              </button>
              <button
                onClick={() => setLeftView('tree')}
                className={`view-btn ${leftView === 'tree' ? 'active' : ''}`}
                title="File Tree view"
              >
                <ListIcon size={16} />
              </button>
            </div>
            <button
              onClick={() => setLeftSectionExpanded(!leftSectionExpanded)}
              className="section-toggle"
            >
              {leftSectionExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>
          </div>

          {/* Left Panel Content */}
          {leftSectionExpanded && (
            <div className="panel-content">
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
          )}
        </div>

        {/* RIGHT PANEL - Test Execution & Statistics */}
        <div className="right-panel">
          {/* Right Panel Header with View Mode Selector */}
          <div className="panel-header">
            <div className="header-title">
              <h2>{rightView === 'runner' ? 'Test Runner' : 'Statistics'}</h2>
            </div>
            <div className="view-mode-buttons">
              <button
                onClick={() => setRightView('runner')}
                className={`view-btn ${rightView === 'runner' ? 'active' : ''}`}
                title="Run Tests"
              >
                ▶
              </button>
              <button
                onClick={() => setRightView('statistics')}
                className={`view-btn ${rightView === 'statistics' ? 'active' : ''}`}
                title="Statistics"
              >
                📊
              </button>
            </div>
            <button
              onClick={() => setRightSectionExpanded(!rightSectionExpanded)}
              className="section-toggle"
            >
              {rightSectionExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
            </button>
          </div>

          {/* Right Panel Content */}
          {rightSectionExpanded && (
            <div className="panel-content">
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
          )}
        </div>
      </div>
      )}
    </div>
  );
}
