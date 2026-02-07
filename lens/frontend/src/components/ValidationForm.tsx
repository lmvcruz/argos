/**
 * ValidationForm component - Form for running code validation/inspection.
 *
 * Features:
 * - Language selector (All, Python, C++, etc.)
 * - Validator selector (filtered by language)
 * - Run validation button
 * - Results display (issues list)
 * - Export results button
 */

import React, { useState, useEffect } from 'react';
import './ValidationForm.css';

/**
 * Validation result structure
 */
export interface ValidationResult {
  file: string;
  line: number;
  column: number;
  severity: 'error' | 'warning' | 'info';
  message: string;
  rule?: string;
}

/**
 * Validator metadata
 */
export interface Validator {
  id: string;
  name: string;
  description: string;
  language: string;
}

/**
 * ValidationForm props
 */
interface ValidationFormProps {
  selectedPath?: string;
  selectedFullPath?: string;
  selectedPathType?: 'file' | 'folder';
  validators: Validator[];
  languages: string[];
  onValidate: (language: string, validator: string, path: string) => Promise<ValidationResult[]>;
  loading?: boolean;
  results?: ValidationResult[];
  activeProject?: { id?: number; name: string; local_folder: string };
}

/**
 * ValidationForm - Form for running code validation
 *
 * Args:
 *   selectedPath: Currently selected file/folder name
 *   selectedFullPath: Full path to selected file/folder
 *   selectedPathType: Type of selected path (file or folder)
 *   validators: Available validators
 *   languages: Available programming languages
 *   onValidate: Callback to run validation
 *   loading: Show loading state
 *   results: Current validation results
 *   activeProject: Current active project with local_folder
 */
export const ValidationForm: React.FC<ValidationFormProps> = ({
  selectedPath,
  selectedFullPath,
  selectedPathType = 'file',
  validators = [],
  languages = [],
  onValidate,
  loading = false,
  results = [],
  activeProject,
}) => {
  const [selectedLanguage, setSelectedLanguage] = useState('python');
  const [selectedValidator, setSelectedValidator] = useState('');
  const [localResults, setLocalResults] = useState<ValidationResult[]>(results);
  const [isRunning, setIsRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Filter validators by selected language
   */
  const filteredValidators = selectedLanguage === 'all'
    ? validators
    : validators.filter((v) => v.language === selectedLanguage || v.language === 'universal');

  /**
   * Initialize validator selection
   */
  useEffect(() => {
    if (filteredValidators.length > 0 && !selectedValidator) {
      setSelectedValidator(filteredValidators[0].id);
    }
  }, [filteredValidators, selectedValidator]);

  /**
   * Handle validation execution
   */
  const handleValidate = async () => {
    if (!selectedPath) {
      setError('Please select a file or folder');
      return;
    }

    if (!selectedValidator) {
      setError('Please select a validator');
      return;
    }

    setIsRunning(true);
    setError(null);

    try {
      const results = await onValidate(selectedLanguage, selectedValidator, selectedPath);
      setLocalResults(results);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Validation failed');
      setLocalResults([]);
    } finally {
      setIsRunning(false);
    }
  };

  /**
   * Handle fixing issues with auto-fix validators (black, isort)
   */
  const handleFixIssues = async () => {
    if (!selectedPath) {
      setError('Please select a file or folder');
      return;
    }

    if (!selectedValidator) {
      setError('Please select a validator');
      return;
    }

    if (!activeProject?.local_folder) {
      setError('No active project selected');
      return;
    }

    // Check if validator supports fixing
    const fixablValidators = ['black', 'isort'];
    if (!fixablValidators.includes(selectedValidator)) {
      setError(`Validator "${selectedValidator}" does not support auto-fixing`);
      return;
    }

    setIsRunning(true);
    setError(null);

    try {
      // Call the validation endpoint with fix=true
      const payload = {
        path: activeProject.local_folder,
        language: selectedLanguage,
        validator: selectedValidator,
        target: selectedFullPath || selectedPath,  // Use full path if available
        fix: true,  // Enable fix mode
      };

      console.log('Fix Issues request:', payload);

      const response = await fetch('/api/inspection/validate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        const errorMsg = errorData.detail || `Fix failed with status ${response.status}`;
        throw new Error(errorMsg);
      }

      const data = await response.json();
      const results = data.results || [];
      setLocalResults(results);

      // Show success message
      setError(null);
      alert(`Issues fixed successfully! ${results.length} issues found after fix.`);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Fix failed');
      setLocalResults([]);
    } finally {
      setIsRunning(false);
    }
  };

  /**
   * Export results to JSON
   */
  const handleExport = () => {
    const dataStr = JSON.stringify(localResults, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `validation-results-${Date.now()}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  /**
   * Count issues by severity
   */
  const severityCounts = {
    error: localResults.filter((r) => r.severity === 'error').length,
    warning: localResults.filter((r) => r.severity === 'warning').length,
    info: localResults.filter((r) => r.severity === 'info').length,
  };

  return (
    <div className="validation-form">
      {/* Form Section */}
      <div className="form-section">
        <h3>Run Validation</h3>

        {/* Target Path */}
        <div className="form-group">
          <label htmlFor="target-path">Target Path</label>
          <div className="path-display">
            <span className={selectedPathType === 'folder' ? 'folder-icon' : 'file-icon'}>
              {selectedPathType === 'folder' ? '📁' : '📄'}
            </span>
            <span className="path-text" title={selectedFullPath || 'No selection'}>
              {selectedFullPath || 'No selection'}
            </span>
          </div>
          <small>
            {selectedPathType === 'folder'
              ? 'Analyzing directory and subdirectories'
              : 'Analyzing single file'}
          </small>
        </div>

        {/* Language Selector */}
        <div className="form-group">
          <label htmlFor="language">Language</label>
          <select
            id="language"
            value={selectedLanguage}
            onChange={(e) => setSelectedLanguage(e.target.value)}
            disabled={loading || isRunning}
            className="form-control"
          >
            <option value="all">All Languages</option>
            {languages.map((lang) => (
              <option key={lang} value={lang}>
                {lang.charAt(0).toUpperCase() + lang.slice(1)}
              </option>
            ))}
          </select>
        </div>

        {/* Validator Selector */}
        <div className="form-group">
          <label htmlFor="validator">Validator</label>
          <select
            id="validator"
            value={selectedValidator}
            onChange={(e) => setSelectedValidator(e.target.value)}
            disabled={loading || isRunning || filteredValidators.length === 0}
            className="form-control"
          >
            {filteredValidators.length === 0 ? (
              <option>No validators available</option>
            ) : (
              filteredValidators.map((v) => (
                <option key={v.id} value={v.id}>
                  {v.name}
                </option>
              ))
            )}
          </select>
          {selectedValidator && (
            <small>
              {
                filteredValidators.find((v) => v.id === selectedValidator)
                  ?.description
              }
            </small>
          )}
        </div>

        {/* Error Message */}
        {error && <div className="error-message">{error}</div>}

        {/* Action Buttons */}
        <div className="form-actions">
          <button
            className="btn btn-primary"
            onClick={handleValidate}
            disabled={isRunning || !selectedPath || !selectedValidator}
          >
            {isRunning ? 'Running...' : 'Run Validation'}
          </button>

          {['black', 'isort'].includes(selectedValidator) && (
            <button
              className="btn btn-success"
              onClick={handleFixIssues}
              disabled={isRunning || !selectedPath || !selectedValidator}
              title="Automatically fix issues in selected folder"
            >
              {isRunning ? 'Fixing...' : 'Fix Issues'}
            </button>
          )}

          {localResults.length > 0 && (
            <button className="btn btn-secondary" onClick={handleExport}>
              Export Results
            </button>
          )}
        </div>
      </div>

      {/* Results Section */}
      {localResults.length > 0 && (
        <div className="results-section">
          <div className="results-header">
            <h3>Results</h3>
            <div className="severity-summary">
              {severityCounts.error > 0 && (
                <span className="severity-badge error">
                  {severityCounts.error} Error{severityCounts.error !== 1 ? 's' : ''}
                </span>
              )}
              {severityCounts.warning > 0 && (
                <span className="severity-badge warning">
                  {severityCounts.warning} Warning{severityCounts.warning !== 1 ? 's' : ''}
                </span>
              )}
              {severityCounts.info > 0 && (
                <span className="severity-badge info">
                  {severityCounts.info} Info
                </span>
              )}
            </div>
          </div>

          <div className="results-list">
            {localResults.map((result, index) => (
              <div key={index} className={`result-item severity-${result.severity}`}>
                <div className="result-header">
                  <span className={`severity-icon severity-${result.severity}`}>
                    {result.severity === 'error' && '❌'}
                    {result.severity === 'warning' && '⚠️'}
                    {result.severity === 'info' && 'ℹ️'}
                  </span>
                  <span className="result-file">{result.file}</span>
                  <span className="result-location">
                    {result.line}:{result.column}
                  </span>
                </div>
                <div className="result-message">{result.message}</div>
                {result.rule && <div className="result-rule">Rule: {result.rule}</div>}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {localResults.length === 0 && !isRunning && (
        <div className="empty-state">
          <p>Run validation to see results</p>
          <small>Select a file or folder and choose a validator</small>
        </div>
      )}

      {/* Loading State */}
      {isRunning && (
        <div className="loading-state">
          <div className="spinner" />
          <p>Running validation...</p>
        </div>
      )}
    </div>
  );
};

export default ValidationForm;
