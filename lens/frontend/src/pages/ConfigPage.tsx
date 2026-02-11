/**
 * Config page component.
 *
 * Main page for project configuration and management.
 * Two-column layout: list on left, form on right.
 */

import React, { useState } from 'react';
import { Project } from '../contexts/ProjectContext';
import ProjectList from '../components/ProjectList';
import ProjectForm from '../components/ProjectForm';
import FileFilterSettings from '../components/FileFilterSettings';
import './ConfigPage.css';

/**
 * ConfigPage - Main configuration page.
 */
export const ConfigPage: React.FC = () => {
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [showSettings, setShowSettings] = useState(false);

  const handleEditProject = (project: Project) => {
    setEditingProject(project);
    setShowForm(true);
    setShowSettings(false);
  };

  const handleFormSubmit = () => {
    setEditingProject(null);
    setShowForm(false);
  };

  const handleFormCancel = () => {
    setEditingProject(null);
    setShowForm(false);
  };

  const handleCreateNew = () => {
    setEditingProject(null);
    setShowForm(true);
    setShowSettings(false);
  };

  const handleShowSettings = () => {
    setEditingProject(null);
    setShowForm(false);
    setShowSettings(true);
  };

  return (
    <div className="config-page">
      <header className="config-header">
        <h1>Configuration</h1>
        <p>Manage your projects and application settings</p>
      </header>

      <div className="config-content">
        <div className="config-list-section">
          <h2 className="section-title">Projects</h2>
          <ProjectList onEditProject={handleEditProject} />
          {!showForm && !showSettings && (
            <button
              className="btn btn-primary create-btn"
              onClick={handleCreateNew}
              title="Create a new project"
            >
              + Create New Project
            </button>
          )}

          <div className="settings-section">
            <h2 className="section-title">Settings</h2>
            <button
              className={`settings-btn ${showSettings ? 'active' : ''}`}
              onClick={handleShowSettings}
            >
              <svg
                className="settings-icon"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
                width="20"
                height="20"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M3 7v10a2 2 0 002 2h14a2 2 0 002-2V9a2 2 0 00-2-2h-6l-2-2H5a2 2 0 00-2 2z"
                />
              </svg>
              File Tree Filters
            </button>
          </div>
        </div>

        <div className="config-form-section">
          {showForm ? (
            <ProjectForm
              initialProject={editingProject || undefined}
              onSubmit={handleFormSubmit}
              onCancel={handleFormCancel}
            />
          ) : showSettings ? (
            <FileFilterSettings />
          ) : (
            <div className="form-placeholder">
              <div className="placeholder-content">
                <h3>No selection</h3>
                <p>Select a project to edit, create a new one, or configure settings</p>
                <svg
                  className="placeholder-icon"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M12 6v6m0 0v6m0-6h6m-6 0H6"
                  />
                </svg>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ConfigPage;
