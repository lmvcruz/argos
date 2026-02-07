/**
 * LocalInspectionPage - Main inspection page with file tree and validation.
 *
 * Two-column layout:
 * - Left: FileTree for selecting files/folders
 * - Right: ValidationForm + ValidationReport for running validation
 */

import React, { useState, useEffect } from 'react';
import { useProjects } from '../contexts/ProjectContext';
import { FileTree, FileTreeNode } from '../components/FileTree';
import { ValidationForm, ValidationResult, Validator } from '../components/ValidationForm';
import { ValidationReport, ValidationReport as ValidationReportType } from '../components/ValidationReport';
import { StatsCard } from '../components/StatsCard';
import './LocalInspection.css';

/**
 * LocalInspectionPage - File inspection and validation interface
 *
 * Allows users to:
 * 1. Browse project files in left panel
 * 2. Select files or folders
 * 3. Choose validators from right panel
 * 4. Run validation and view results
 * 5. See statistics about validation
 */
export const LocalInspection: React.FC = () => {
  const { activeProject } = useProjects();
  const [selectedNodeId, setSelectedNodeId] = useState<string>('');
  const [selectedPath, setSelectedPath] = useState<string>('');
  const [selectedFullPath, setSelectedFullPath] = useState<string>('');
  const [selectedPathType, setSelectedPathType] = useState<'file' | 'folder'>('file');
  const [isValidationExpanded, setIsValidationExpanded] = useState(true);
  const [isStatsExpanded, setIsStatsExpanded] = useState(true);
  const [isReportExpanded, setIsReportExpanded] = useState(true);
  const [fileNodes, setFileNodes] = useState<FileTreeNode[]>([]);
  const [validationResults, setValidationResults] = useState<ValidationResult[]>([]);
  const [validationReport, setValidationReport] = useState<ValidationReportType | undefined>();
  const [validators, setValidators] = useState<Validator[]>([]);
  const [languages, setLanguages] = useState<string[]>([]);
  const [lastValidationTime, setLastValidationTime] = useState<Date>();
  const [isValidating, setIsValidating] = useState(false);

  /**
   * Load file tree from project
   */
  useEffect(() => {
    if (!activeProject) {
      setFileNodes([]);
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
        setFileNodes(data.files || []);
      } catch (error) {
        console.error('Error loading file tree:', error);
        setFileNodes([]);
      }
    };

    loadFileTree();
  }, [activeProject]);

  /**
   * Load available validators and languages
   */
  useEffect(() => {
    const loadValidators = async () => {
      try {
        const [languagesRes, validatorsRes] = await Promise.all([
          fetch('/api/inspection/languages'),
          fetch('/api/inspection/validators'),
        ]);

        if (languagesRes.ok) {
          const langData = await languagesRes.json();
          setLanguages(langData.languages || []);
        }

        if (validatorsRes.ok) {
          const valData = await validatorsRes.json();
          setValidators(valData.validators || []);
        }
      } catch (error) {
        console.error('Error loading validators:', error);
      }
    };

    loadValidators();
  }, []);

  /**
   * Handle file/folder selection
   */
  const handleSelectNode = (nodeId: string) => {
    // Find the node object in the tree to get its details
    const findNode = (nodes: FileTreeNode[]): FileTreeNode | null => {
      for (const node of nodes) {
        if (node.id === nodeId) {
          return node;
        }
        if (node.children) {
          const found = findNode(node.children);
          if (found) return found;
        }
      }
      return null;
    };

    const node = findNode(fileNodes);
    if (node) {
      setSelectedNodeId(nodeId);
      setSelectedPath(node.name);
      // The node.id is the full absolute path from the backend (e.g., D:\playground\argos\scout\scout)
      // Use it directly - do NOT prepend activeProject.local_folder
      setSelectedFullPath(node.id);
      setSelectedPathType(node.type);
    }
  };

  /**
   * Handle validation execution
   */
  const handleValidate = async (
    language: string,
    validator: string,
    _path: string
  ): Promise<ValidationResult[]> => {
    if (!activeProject) {
      throw new Error('No active project');
    }

    if (!selectedFullPath) {
      throw new Error('Please select a file or folder to validate');
    }

    setIsValidating(true);
    try {
      const response = await fetch('/api/inspection/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          path: activeProject.local_folder,
          language,
          validator,
          target: selectedFullPath,
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMsg = errorData.detail || `Validation failed with status ${response.status}`;
        throw new Error(errorMsg);
      }

      const data = await response.json();
      const results = data.results || [];
      setValidationResults(results);

      // Set validation report if available
      if (data.report) {
        setValidationReport(data.report);
      }

      setLastValidationTime(new Date());
      return results;
    } catch (error) {
      console.error('Validation error:', error);
      throw error;
    } finally {
      setIsValidating(false);
    }
  };

  if (!activeProject) {
    return (
      <div className="local-inspection-page">
        <div className="no-project">
          <h2>No Project Selected</h2>
          <p>Please select a project from the Config page to start inspection.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="local-inspection-page">
      {/* Left Panel: File Tree */}
      <div className="inspection-panel left-panel">
        <div className="panel-header">
          <h2>📁 Files</h2>
          <span className="project-name">{activeProject.name}</span>
        </div>
        <FileTree
          nodes={fileNodes}
          onSelectNode={handleSelectNode}
          selectedNodeId={selectedNodeId}
        />
      </div>

      {/* Splitter */}
      <div className="panel-splitter" />

      {/* Right Panel: Validation */}
      <div className="inspection-panel right-panel">
        <div className="panel-header">
          <h2>🔍 Validation</h2>
        </div>

        <div className="validation-container">
          {/* Validation Section */}
          <div className="collapsible-section">
            <div className="section-header" onClick={() => setIsValidationExpanded(!isValidationExpanded)}>
              <span className="toggle-button">{isValidationExpanded ? '−' : '+'}</span>
              <h3>Validation</h3>
            </div>
            {isValidationExpanded && (
              <ValidationForm
                selectedPath={selectedPath}
                selectedFullPath={selectedFullPath}
                selectedPathType={selectedPathType}
                validators={validators}
                languages={languages}
                onValidate={handleValidate}
                loading={isValidating}
                results={validationResults}
                activeProject={activeProject || undefined}
              />
            )}
          </div>

          {/* Stats Section */}
          <div className="collapsible-section">
            <div className="section-header" onClick={() => setIsStatsExpanded(!isStatsExpanded)}>
              <span className="toggle-button">{isStatsExpanded ? '−' : '+'}</span>
              <h3>Statistics</h3>
            </div>
            {isStatsExpanded && (
              <StatsCard
                filesAnalyzed={fileNodes.length}
                errorCount={validationResults.filter((r) => r.severity === 'error').length}
                warningCount={validationResults.filter((r) => r.severity === 'warning').length}
                infoCount={validationResults.filter((r) => r.severity === 'info').length}
                lastUpdated={lastValidationTime}
                isLoading={isValidating}
                language="Python"
                validator="flake8"
              />
            )}
          </div>

          {/* Report Section */}
          {validationReport && (
            <div className="collapsible-section">
              <div className="section-header" onClick={() => setIsReportExpanded(!isReportExpanded)}>
                <span className="toggle-button">{isReportExpanded ? '−' : '+'}</span>
                <h3>Validation Report</h3>
              </div>
              {isReportExpanded && (
                <ValidationReport
                  report={validationReport}
                  results={validationResults}
                  onExport={() => {
                    const dataStr = JSON.stringify(
                      { report: validationReport, results: validationResults },
                      null,
                      2
                    );
                    const dataBlob = new Blob([dataStr], { type: 'application/json' });
                    const url = URL.createObjectURL(dataBlob);
                    const link = document.createElement('a');
                    link.href = url;
                    link.download = `validation-report-${Date.now()}.json`;
                    link.click();
                    URL.revokeObjectURL(url);
                  }}
                />
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LocalInspection;
