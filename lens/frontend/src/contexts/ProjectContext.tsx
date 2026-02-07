/**
 * Project context for managing projects globally.
 *
 * Provides state and methods for managing projects across the Lens UI.
 * Integrates with backend API for persistence.
 */

import React, { createContext, useContext, useState, useCallback, useEffect } from 'react';
import logger from '../utils/logger';

/**
 * Project type definition.
 */
export interface Project {
  id?: number;
  name: string;
  local_folder: string;
  repo: string;
  token?: string;
  storage_location?: string;
  created_at?: string;
  updated_at?: string;
}

/**
 * Project context type definition.
 */
export interface ProjectContextType {
  projects: Project[];
  activeProject: Project | null;
  loading: boolean;
  error: string | null;

  // Actions
  createProject(project: Omit<Project, 'id' | 'created_at' | 'updated_at'>): Promise<Project>;
  updateProject(id: number, project: Partial<Project>): Promise<Project>;
  deleteProject(id: number): Promise<void>;
  selectProject(id: number): Promise<Project>;
  loadProjects(): Promise<void>;
  clearError(): void;
}

/**
 * Create project context.
 */
const ProjectContext = createContext<ProjectContextType | null>(null);

/**
 * Project provider component.
 *
 * Wraps application to provide project context.
 */
export const ProjectProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [projects, setProjects] = useState<Project[]>([]);
  const [activeProject, setActiveProject] = useState<Project | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  /**
   * Load all projects from backend.
   */
  const loadProjects = useCallback(async () => {
    logger.debug('[LOAD_PROJECTS] Starting to load projects');
    setLoading(true);
    setError(null);

    try {
      const response = await fetch('/api/projects');
      if (!response.ok) {
        throw new Error(`Failed to load projects: ${response.statusText}`);
      }

      const data = await response.json();
      setProjects(data.projects || []);
      logger.info(`[LOAD_PROJECTS] Loaded ${data.projects?.length || 0} projects`);
      logger.debug('[LOAD_PROJECTS] Projects:', { projects: data.projects });

      // Load active project
      const activeResponse = await fetch('/api/projects/active');
      if (activeResponse.ok) {
        const activeData = await activeResponse.json();
        setActiveProject(activeData.active_project || null);
        logger.info(`[LOAD_PROJECTS] Active project: ${activeData.active_project?.name || 'None'}`);
      }
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Unknown error loading projects';
      setError(message);
      logger.error(`[LOAD_PROJECTS] Error: ${message}`, { error: err });
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * Create a new project.
   */
  const createProject = useCallback(
    async (project: Omit<Project, 'id' | 'created_at' | 'updated_at'>) => {
      logger.debug('[CREATE_PROJECT] Creating project', { project });
      setError(null);

      try {
        const response = await fetch('/api/projects', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(project),
        });

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.detail || `Failed to create project: ${response.statusText}`);
        }

        const created = await response.json();
        setProjects([...projects, created]);
        logger.info(`[CREATE_PROJECT] Created project '${created.name}' with ID ${created.id}`);
        return created;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to create project';
        setError(message);
        logger.error(`[CREATE_PROJECT] Error: ${message}`, { error: err });
        throw err;
      }
    },
    [projects]
  );

  /**
   * Update an existing project.
   */
  const updateProject = useCallback(
    async (id: number, updates: Partial<Project>) => {
      setError(null);

      try {
        const response = await fetch(`/api/projects/${id}`, {
          method: 'PUT',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(updates),
        });

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.detail || `Failed to update project: ${response.statusText}`);
        }

        const updated = await response.json();

        // Update projects list
        setProjects(projects.map((p) => (p.id === id ? updated : p)));

        // Update active project if it's the one being updated
        if (activeProject?.id === id) {
          setActiveProject(updated);
        }

        return updated;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to update project';
        setError(message);
        throw err;
      }
    },
    [projects, activeProject]
  );

  /**
   * Delete a project.
   */
  const deleteProject = useCallback(
    async (id: number) => {
      setError(null);

      try {
        const response = await fetch(`/api/projects/${id}`, {
          method: 'DELETE',
        });

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.detail || `Failed to delete project: ${response.statusText}`);
        }

        // Remove from projects list
        setProjects(projects.filter((p) => p.id !== id));

        // Clear active project if it's the one being deleted
        if (activeProject?.id === id) {
          setActiveProject(null);
        }
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to delete project';
        setError(message);
        throw err;
      }
    },
    [projects, activeProject]
  );

  /**
   * Select a project as active.
   */
  const selectProject = useCallback(
    async (id: number) => {
      setError(null);

      try {
        const response = await fetch(`/api/projects/${id}/select`, {
          method: 'POST',
        });

        if (!response.ok) {
          const data = await response.json();
          throw new Error(data.detail || `Failed to select project: ${response.statusText}`);
        }

        const data = await response.json();
        setActiveProject(data.project || null);

        // Store in localStorage for persistence
        if (data.project?.id) {
          localStorage.setItem('activeProjectId', data.project.id.toString());
        }

        return data.project;
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to select project';
        setError(message);
        throw err;
      }
    },
    []
  );

  /**
   * Clear error message.
   */
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  /**
   * Load projects on mount and restore active project from localStorage.
   */
  useEffect(() => {
    loadProjects();

    // Restore active project from localStorage
    const activeProjectId = localStorage.getItem('activeProjectId');
    if (activeProjectId) {
      fetch(`/api/projects/${activeProjectId}`)
        .then((res) => res.ok ? res.json() : null)
        .then((data) => {
          if (data) setActiveProject(data);
        })
        .catch((err) => console.error('Error restoring active project:', err));
    }
  }, [loadProjects]);

  const value: ProjectContextType = {
    projects,
    activeProject,
    loading,
    error,
    createProject,
    updateProject,
    deleteProject,
    selectProject,
    loadProjects,
    clearError,
  };

  return <ProjectContext.Provider value={value}>{children}</ProjectContext.Provider>;
};

/**
 * Hook to use project context.
 *
 * @throws {Error} If used outside ProjectProvider
 * @returns {ProjectContextType} Project context
 */
export const useProjects = (): ProjectContextType => {
  const context = useContext(ProjectContext);
  if (!context) {
    throw new Error('useProjects must be used within ProjectProvider');
  }
  return context;
};

export default ProjectContext;
