/**
 * Project form component.
 *
 * Form for creating and editing projects.
 * Handles validation and API calls.
 */

import React, { useState, useEffect } from 'react';
import { Project, useProjects } from '../contexts/ProjectContext';
import './ProjectForm.css';

interface ProjectFormProps {
  initialProject?: Project;
  onSubmit?: (project: Project) => void;
  onCancel?: () => void;
}

/**
 * ProjectForm - Form for creating/editing projects.
 */
export const ProjectForm: React.FC<ProjectFormProps> = ({
  initialProject,
  onSubmit,
  onCancel,
}) => {
  const { createProject, updateProject, error } = useProjects();

  const [formData, setFormData] = useState<Omit<Project, 'id' | 'created_at' | 'updated_at'>>({
    name: initialProject?.name || '',
    local_folder: initialProject?.local_folder || '',
    repo: initialProject?.repo || '',
    token: initialProject?.token || '',
    storage_location: initialProject?.storage_location || '',
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [submitting, setSubmitting] = useState(false);
  const [submitError, setSubmitError] = useState<string | null>(null);

  /**
   * Handle field change.
   */
  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => {
    const { name, value } = e.target;
    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));
    // Clear error for this field
    if (errors[name]) {
      setErrors((prev) => ({
        ...prev,
        [name]: '',
      }));
    }
  };

  /**
   * Validate form data.
   */
  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    if (!formData.name.trim()) {
      newErrors.name = 'Project name is required';
    }

    if (!formData.local_folder.trim()) {
      newErrors.local_folder = 'Local folder is required';
    }

    if (!formData.repo.trim()) {
      newErrors.repo = 'Repository is required';
    } else if (!/^[a-zA-Z0-9_-]+\/[a-zA-Z0-9_.-]+$/.test(formData.repo)) {
      newErrors.repo = 'Repository must be in format "owner/repo"';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  /**
   * Handle form submit.
   */
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setSubmitting(true);
    setSubmitError(null);

    try {
      let result: Project;

      if (initialProject?.id) {
        // Update existing project
        result = await updateProject(initialProject.id, formData);
      } else {
        // Create new project
        result = await createProject(formData);
      }

      onSubmit?.(result);

      // Reset form if creating new project
      if (!initialProject?.id) {
        setFormData({
          name: '',
          local_folder: '',
          repo: '',
          token: '',
          storage_location: '',
        });
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Failed to save project';
      setSubmitError(message);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <form className="project-form" onSubmit={handleSubmit}>
      <h2>{initialProject ? 'Edit Project' : 'Create New Project'}</h2>

      {(submitError || error) && (
        <div className="form-error">{submitError || error}</div>
      )}

      <div className="form-group">
        <label htmlFor="name">Project Name *</label>
        <input
          id="name"
          name="name"
          type="text"
          placeholder="e.g., My Project"
          value={formData.name}
          onChange={handleChange}
          disabled={submitting}
          className={errors.name ? 'error' : ''}
        />
        {errors.name && <span className="field-error">{errors.name}</span>}
      </div>

      <div className="form-group">
        <label htmlFor="repo">GitHub Repository *</label>
        <input
          id="repo"
          name="repo"
          type="text"
          placeholder="e.g., owner/repo"
          value={formData.repo}
          onChange={handleChange}
          disabled={submitting}
          className={errors.repo ? 'error' : ''}
        />
        {errors.repo && <span className="field-error">{errors.repo}</span>}
      </div>

      <div className="form-group">
        <label htmlFor="local_folder">Local Folder *</label>
        <input
          id="local_folder"
          name="local_folder"
          type="text"
          placeholder="e.g., /path/to/project"
          value={formData.local_folder}
          onChange={handleChange}
          disabled={submitting}
          className={errors.local_folder ? 'error' : ''}
        />
        {errors.local_folder && <span className="field-error">{errors.local_folder}</span>}
      </div>

      <div className="form-group">
        <label htmlFor="token">GitHub Token (optional)</label>
        <input
          id="token"
          name="token"
          type="password"
          placeholder="Enter your GitHub token"
          value={formData.token}
          onChange={handleChange}
          disabled={submitting}
        />
        <small>For accessing private repositories</small>
      </div>

      <div className="form-group">
        <label htmlFor="storage_location">Storage Location (optional)</label>
        <input
          id="storage_location"
          name="storage_location"
          type="text"
          placeholder="e.g., ~/.scout"
          value={formData.storage_location}
          onChange={handleChange}
          disabled={submitting}
        />
        <small>Custom location for storing project data</small>
      </div>

      <div className="form-actions">
        <button
          type="submit"
          className="btn btn-primary"
          disabled={submitting}
        >
          {submitting ? 'Saving...' : initialProject ? 'Update Project' : 'Create Project'}
        </button>
        {onCancel && (
          <button
            type="button"
            className="btn btn-secondary"
            onClick={onCancel}
            disabled={submitting}
          >
            Cancel
          </button>
        )}
      </div>
    </form>
  );
};

export default ProjectForm;
