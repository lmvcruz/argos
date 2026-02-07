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
import './ConfigPage.css';

/**
 * ConfigPage - Main configuration page.
 */
export const ConfigPage: React.FC = () => {
  const [editingProject, setEditingProject] = useState<Project | null>(null);
  const [showForm, setShowForm] = useState(false);

  const handleEditProject = (project: Project) => {
    setEditingProject(project);
    setShowForm(true);
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
  };

  return (
    <div className="config-page">
      <header className="config-header">
        <h1>Project Configuration</h1>
        <p>Create, edit, and manage your projects</p>
      </header>

      <div className="config-content">
        <div className="config-list-section">
          <ProjectList onEditProject={handleEditProject} />
          {!showForm && (
            <button
              className="btn btn-primary create-btn"
              onClick={handleCreateNew}
              title="Create a new project"
            >
              + Create New Project
            </button>
          )}
        </div>

        <div className="config-form-section">
          {showForm ? (
            <ProjectForm
              initialProject={editingProject || undefined}
              onSubmit={handleFormSubmit}
              onCancel={handleFormCancel}
            />
          ) : (
            <div className="form-placeholder">
              <div className="placeholder-content">
                <h3>No project selected</h3>
                <p>Select an existing project to edit or create a new one</p>
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
