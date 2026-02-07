/**
 * Project list component.
 *
 * Displays all projects with actions (select, edit, delete).
 * Shows visual indicator for active project.
 */

import React, { useState } from 'react';
import { Project, useProjects } from '../contexts/ProjectContext';
import './ProjectList.css';

interface ProjectListProps {
  onEditProject?: (project: Project) => void;
}

/**
 * ProjectListItem - Individual project row.
 */
const ProjectListItem: React.FC<{
  project: Project;
  isActive: boolean;
  onSelect: (id: number) => Promise<void>;
  onEdit: (project: Project) => void;
  onDelete: (id: number) => Promise<void>;
}> = ({ project, isActive, onSelect, onEdit, onDelete }) => {
  const [deleting, setDeleting] = useState(false);
  const [selecting, setSelecting] = useState(false);

  const handleDelete = async () => {
    if (window.confirm(`Delete project "${project.name}"?`)) {
      setDeleting(true);
      try {
        await onDelete(project.id!);
      } finally {
        setDeleting(false);
      }
    }
  };

  const handleSelect = async () => {
    setSelecting(true);
    try {
      await onSelect(project.id!);
    } finally {
      setSelecting(false);
    }
  };

  return (
    <div className={`project-list-item ${isActive ? 'active' : ''}`}>
      <div className="project-info">
        <div className="project-header">
          {isActive && <span className="active-indicator">●</span>}
          <h3 className="project-name">{project.name}</h3>
        </div>
        <p className="project-details">
          <span className="detail-label">Repo:</span>
          <span className="detail-value">{project.repo}</span>
        </p>
        <p className="project-details">
          <span className="detail-label">Folder:</span>
          <span className="detail-value">{project.local_folder}</span>
        </p>
        {project.token && (
          <p className="project-token">
            <span className="token-badge">Token configured</span>
          </p>
        )}
      </div>
      <div className="project-actions">
        {!isActive && (
          <button
            className="btn btn-primary"
            onClick={handleSelect}
            disabled={selecting}
            title="Select this project"
          >
            {selecting ? 'Selecting...' : 'Select'}
          </button>
        )}
        <button
          className="btn btn-secondary"
          onClick={() => onEdit(project)}
          title="Edit project"
        >
          Edit
        </button>
        <button
          className="btn btn-danger"
          onClick={handleDelete}
          disabled={deleting}
          title="Delete project"
        >
          {deleting ? 'Deleting...' : 'Delete'}
        </button>
      </div>
    </div>
  );
};

/**
 * ProjectList - Main project list component.
 */
export const ProjectList: React.FC<ProjectListProps> = ({ onEditProject }) => {
  const { projects, activeProject, deleteProject, selectProject, loading, error } = useProjects();

  if (loading) {
    return <div className="project-list loading">Loading projects...</div>;
  }

  if (error) {
    return (
      <div className="project-list error">
        <p>Error loading projects: {error}</p>
      </div>
    );
  }

  if (projects.length === 0) {
    return (
      <div className="project-list empty">
        <p>No projects yet. Create one to get started!</p>
      </div>
    );
  }

  return (
    <div className="project-list">
      <div className="project-list-header">
        <h2>Projects ({projects.length})</h2>
      </div>
      <div className="project-list-items">
        {projects.map((project) => (
          <ProjectListItem
            key={project.id}
            project={project}
            isActive={activeProject?.id === project.id}
            onSelect={selectProject}
            onEdit={onEditProject || (() => {})}
            onDelete={deleteProject}
          />
        ))}
      </div>
    </div>
  );
};

export default ProjectList;
