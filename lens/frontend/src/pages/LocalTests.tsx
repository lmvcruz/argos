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
  const [leftView, setLeftView] = useState<LeftViewMode>('tree');
  const [rightView, setRightView] = useState<RightViewMode>('runner');
  const [selectedFiles, setSelectedFiles] = useState<Set<string>>(new Set()); // Files/folders selected in File Tree View
  const [selectedTests, setSelectedTests] = useState<Set<string>>(new Set()); // Individual tests selected in Test Suite View
  const [error, setError] = useState<string>('');

  // Collapsible sections state
  const [leftSectionExpanded, setLeftSectionExpanded] = useState(true);
  const [rightSectionExpanded, setRightSectionExpanded] = useState(true);

  // Data state
  const [fileTree, setFileTree] = useState<FileTreeNode[]>([]);
  const [testSuites, setTestSuites] = useState<TestSuite[]>([]);
  const [loading, setLoading] = useState(false);
  const [discoveryTaskId, setDiscoveryTaskId] = useState<string | null>(null);

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
   * Start test discovery
   */
  const startDiscovery = async () => {
    if (!activeProject) return;

    setLoading(true);
    setError('');
    setTestSuites([]);
    setDiscoveryTaskId(null);

    // Determine discovery path: use selected folder if available, otherwise use project root
    let discoveryPath = activeProject.local_folder;
    if (selectedFiles.size > 0) {
      // Use the first selected file/folder
      const firstSelected = Array.from(selectedFiles)[0];
      discoveryPath = firstSelected;
    }

    console.log('[TEST_DISCOVERY] Starting discovery...');
    console.log('[TEST_DISCOVERY] Project root:', activeProject.local_folder);
    console.log('[TEST_DISCOVERY] Selected files:', Array.from(selectedFiles));
    console.log('[TEST_DISCOVERY] Discovery path:', discoveryPath);

    try {
      const response = await fetch('/api/tests/discover/start', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: discoveryPath }),
      });

      if (!response.ok) {
        throw new Error('Failed to start test discovery');
      }

      const data = await response.json();
      setDiscoveryTaskId(data.task_id);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to start discovery');
      setLoading(false);
    }
  };

  /**
   * Poll for discovery results
   */
  useEffect(() => {
    if (!discoveryTaskId) return;

    const pollInterval = setInterval(async () => {
      try {
        const response = await fetch(`/api/tests/discover/status/${discoveryTaskId}`);
        if (!response.ok) {
          throw new Error('Failed to check discovery status');
        }

        const data = await response.json();

        if (data.status === 'completed') {
          setTestSuites(data.result.suites || []);
          setLoading(false);
          setDiscoveryTaskId(null);
          clearInterval(pollInterval);
        } else if (data.status === 'failed') {
          setError(data.error || 'Test discovery failed');
          setLoading(false);
          setDiscoveryTaskId(null);
          clearInterval(pollInterval);
        }
        // If status is 'running', keep polling
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to get discovery status');
        setLoading(false);
        setDiscoveryTaskId(null);
        clearInterval(pollInterval);
      }
    }, 2000); // Poll every 2 seconds

    return () => clearInterval(pollInterval);
  }, [discoveryTaskId]);

  /**
   * Auto-start discovery when project changes
   */
  useEffect(() => {
    if (isFeatureEnabled('localTests') && activeProject) {
      startDiscovery();
    }
  }, [isFeatureEnabled, activeProject]);

  /**
   * Helper function to check if a file path is within selected files/folders
   */
  const isFileInSelection = (filePath: string, selectedFilePaths: Set<string>): boolean => {
    if (selectedFilePaths.size === 0) {
      // If no files selected, show all tests
      return true;
    }

    // Normalize paths for comparison (use forward slashes and lowercase for case-insensitive)
    const normalizedPath = filePath.replace(/\\/g, '/').toLowerCase();

    // Debug logging
    console.log('Checking file:', normalizedPath);
    console.log('Against selected paths:', Array.from(selectedFilePaths));

    for (const selected of selectedFilePaths) {
      const normalizedSelected = selected.replace(/\\/g, '/').toLowerCase();

      // The test suite paths are relative, but selected paths are absolute
      // Check if the absolute path ends with the relative test file path
      // OR if the relative path starts with the selected folder

      // Case 1: Selected path ends with the test file path (file selection)
      if (normalizedSelected.endsWith('/' + normalizedPath) || normalizedSelected.endsWith(normalizedPath)) {
        console.log('✓ Matched (case 1):', normalizedSelected);
        return true;
      }

      // Case 2: Test file path starts with a relative folder that matches end of selected path (folder selection)
      // Extract the relative portion from the selected path by removing the project root
      // For example: "D:/playground/argos/anvil/tests" -> check if test path starts with "tests/"
      const pathParts = normalizedSelected.split('/');

      // Try progressively shorter path endings to match against the relative test path
      for (let i = pathParts.length - 1; i >= 0; i--) {
        const relativePortion = pathParts.slice(i).join('/');
        if (normalizedPath.startsWith(relativePortion + '/') || normalizedPath === relativePortion) {
          console.log('✓ Matched (case 2):', relativePortion, 'from', normalizedSelected);
          return true;
        }
      }
    }

    console.log('✗ No match found');
    return false;
  };

  /**
   * Filter test suites based on selected files/folders
   */
  const filteredTestSuites = testSuites.filter(suite =>
    isFileInSelection(suite.file, selectedFiles)
  );

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
              {leftView === 'suites' && selectedFiles.size > 0 && (
                <span className="filter-badge">
                  Filtered by {selectedFiles.size} file{selectedFiles.size !== 1 ? 's' : ''}
                </span>
              )}
            </div>

            {/* Action Buttons - Show based on view */}
            {leftView === 'suites' ? (
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                <button
                  onClick={() => {
                    const allTestIds = new Set<string>();
                    filteredTestSuites.forEach(suite => {
                      suite.tests.forEach(test => allTestIds.add(test.id));
                    });
                    setSelectedTests(allTestIds);
                  }}
                  disabled={filteredTestSuites.length === 0}
                  className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Select all tests"
                >
                  Select All
                </button>
                <button
                  onClick={() => setSelectedTests(new Set())}
                  disabled={selectedTests.size === 0}
                  className="px-2 py-1 text-xs bg-gray-100 hover:bg-gray-200 dark:bg-gray-700 dark:hover:bg-gray-600 text-gray-700 dark:text-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                  title="Clear selection"
                >
                  Clear
                </button>
                <button
                  onClick={startDiscovery}
                  disabled={loading}
                  className="px-2 py-1 text-xs bg-blue-500 hover:bg-blue-600 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed"
                  title={
                    selectedFiles.size > 0
                      ? `Refresh: Discover tests in selected folder`
                      : `Refresh: Discover tests in entire project`
                  }
                >
                  {loading ? '⏳' : '🔄'}
                </button>
              </div>
            ) : (
              <button
                onClick={startDiscovery}
                disabled={loading}
                className="px-2 py-1 text-xs bg-blue-500 hover:bg-blue-600 text-white rounded disabled:opacity-50 disabled:cursor-not-allowed"
                title={
                  selectedFiles.size > 0
                    ? `Refresh: Discover tests in selected folder`
                    : `Refresh: Discover tests in entire project`
                }
              >
                {loading ? '⏳' : '🔄'}
              </button>
            )}

            <div className="view-mode-buttons">
              <button
                onClick={() => setLeftView('tree')}
                className={`view-btn ${leftView === 'tree' ? 'active' : ''}`}
                title="File Tree view"
              >
                <ListIcon size={16} />
              </button>
              <button
                onClick={() => setLeftView('suites')}
                className={`view-btn ${leftView === 'suites' ? 'active' : ''}`}
                title="Tests Suite view"
              >
                <BarChart3 size={16} />
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
                <>
                  {filteredTestSuites.length === 0 && selectedFiles.size > 0 ? (
                    <div className="tree-empty">
                      <p>No tests found in selected files.</p>
                      <p style={{ fontSize: '0.9rem', marginTop: '8px', opacity: 0.7 }}>
                        Switch to File Tree view to select different files.
                      </p>
                    </div>
                  ) : (
                    <TestSuiteTree
                      suites={filteredTestSuites}
                      selectedItems={selectedTests}
                      onSelectionChange={setSelectedTests}
                    />
                  )}
                </>
              ) : (
                <TestFileTree
                  nodes={fileTree}
                  selectedItems={selectedFiles}
                  onSelectionChange={setSelectedFiles}
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
