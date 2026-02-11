/**
 * File Filter Settings Component
 *
 * Manages file tree filter patterns that hide specified folders/files
 * from the source tree in Local Inspection and Local Tests.
 */

import React, { useState, useEffect } from 'react';
import './FileFilterSettings.css';

interface FileFilterSettingsProps {
  onClose?: () => void;
}

/**
 * FileFilterSettings - Component for managing file tree filters.
 */
export const FileFilterSettings: React.FC<FileFilterSettingsProps> = ({ onClose }) => {
  const [filters, setFilters] = useState<string[]>([]);
  const [newFilter, setNewFilter] = useState('');
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [successMessage, setSuccessMessage] = useState<string | null>(null);

  // Load filters on mount
  useEffect(() => {
    loadFilters();
  }, []);

  const loadFilters = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch('/api/settings/file-filters');
      if (!response.ok) {
        throw new Error('Failed to load file filters');
      }
      const data = await response.json();
      setFilters(data.filters || []);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Error loading filters:', err);
    } finally {
      setLoading(false);
    }
  };

  const saveFilters = async (updatedFilters: string[]) => {
    try {
      setSaving(true);
      setError(null);
      setSuccessMessage(null);

      const response = await fetch('/api/settings/file-filters', {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ filters: updatedFilters }),
      });

      if (!response.ok) {
        throw new Error('Failed to save file filters');
      }

      setFilters(updatedFilters);
      setSuccessMessage('File filters saved successfully!');
      setTimeout(() => setSuccessMessage(null), 3000);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
      console.error('Error saving filters:', err);
    } finally {
      setSaving(false);
    }
  };

  const handleAddFilter = () => {
    const trimmed = newFilter.trim();
    if (!trimmed) {
      setError('Filter pattern cannot be empty');
      return;
    }
    if (filters.includes(trimmed)) {
      setError('This filter pattern already exists');
      return;
    }
    const updatedFilters = [...filters, trimmed];
    setNewFilter('');
    setError(null);
    saveFilters(updatedFilters);
  };

  const handleRemoveFilter = (index: number) => {
    const updatedFilters = filters.filter((_, i) => i !== index);
    saveFilters(updatedFilters);
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleAddFilter();
    }
  };

  const handleResetDefaults = () => {
    const defaultFilters = [
      '__pycache__',
      'node_modules',
      '.git',
      'dist',
      'build',
      '.venv',
      'venv',
      '.env',
      '.pytest_cache',
      '.mypy_cache',
      'htmlcov',
      'coverage',
    ];
    saveFilters(defaultFilters);
  };

  if (loading) {
    return (
      <div className="file-filter-settings loading">
        <div className="spinner"></div>
        <p>Loading filters...</p>
      </div>
    );
  }

  return (
    <div className="file-filter-settings">
      <div className="filter-header">
        <div>
          <h3>File Tree Filters</h3>
          <p className="filter-description">
            Specify folder and file names to hide from the source tree.
            Hidden items won't appear in Local Inspection or Local Tests.
          </p>
        </div>
        {onClose && (
          <button className="btn-close" onClick={onClose} title="Close">
            ×
          </button>
        )}
      </div>

      {error && (
        <div className="alert alert-error">
          <strong>Error:</strong> {error}
        </div>
      )}

      {successMessage && (
        <div className="alert alert-success">
          {successMessage}
        </div>
      )}

      <div className="filter-input-section">
        <div className="input-group">
          <input
            type="text"
            className="filter-input"
            placeholder="e.g., __pycache__, node_modules, dist"
            value={newFilter}
            onChange={(e) => setNewFilter(e.target.value)}
            onKeyPress={handleKeyPress}
            disabled={saving}
          />
          <button
            className="btn btn-primary"
            onClick={handleAddFilter}
            disabled={saving || !newFilter.trim()}
          >
            Add Filter
          </button>
        </div>
        <p className="input-hint">
          Note: Files and folders starting with "." are always hidden.
        </p>
      </div>

      <div className="filter-list-section">
        <div className="filter-list-header">
          <h4>Active Filters ({filters.length})</h4>
          <button
            className="btn btn-secondary btn-sm"
            onClick={handleResetDefaults}
            disabled={saving}
            title="Reset to default filters"
          >
            Reset to Defaults
          </button>
        </div>

        {filters.length === 0 ? (
          <div className="empty-state">
            <p>No filters configured. All files and folders will be visible (except those starting with ".").</p>
          </div>
        ) : (
          <ul className="filter-list">
            {filters.map((filter, index) => (
              <li key={index} className="filter-item">
                <span className="filter-name">{filter}</span>
                <button
                  className="btn-remove"
                  onClick={() => handleRemoveFilter(index)}
                  disabled={saving}
                  title="Remove filter"
                >
                  ×
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>

      {saving && (
        <div className="saving-indicator">
          <div className="spinner-small"></div>
          <span>Saving...</span>
        </div>
      )}
    </div>
  );
};

export default FileFilterSettings;
