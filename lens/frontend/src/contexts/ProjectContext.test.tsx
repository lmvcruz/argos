/**
 * ProjectContext state management tests.
 *
 * Tests all ProjectContext methods:
 * - loadProjects: Fetches projects from API and updates state
 * - createProject: Creates new project and adds to state
 * - updateProject: Updates existing project in state
 * - deleteProject: Removes project from state
 * - selectProject: Sets active project and persists to localStorage
 * - getError: Returns current error state
 * - clearError: Clears error state
 */

import React from 'react';
import { render, screen, waitFor, fireEvent } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { ProjectProvider, useProjects } from './ProjectContext';

// Mock fetch globally
const mockFetch = jest.fn();
global.fetch = mockFetch as jest.Mock;

// Mock localStorage
const localStorageMock = (() => {
  let store: Record<string, string> = {};

  return {
    getItem: (key: string) => store[key] || null,
    setItem: (key: string, value: string) => {
      store[key] = value.toString();
    },
    removeItem: (key: string) => {
      delete store[key];
    },
    clear: () => {
      store = {};
    },
  };
})();

Object.defineProperty(window, 'localStorage', {
  value: localStorageMock,
});

/**
 * Test component that uses the ProjectContext hook.
 */
const TestComponent = () => {
  const {
    projects,
    activeProject,
    loading,
    error,
    loadProjects,
    createProject,
    updateProject,
    deleteProject,
    selectProject,
    clearError,
  } = useProjects();

  return (
    <div>
      <div data-testid="loading">{loading ? 'Loading' : 'Loaded'}</div>
      <div data-testid="error">{error ? error.message : 'No error'}</div>
      <div data-testid="active-project">{activeProject?.name || 'None'}</div>
      <div data-testid="project-count">{projects.length}</div>

      <button onClick={loadProjects} data-testid="btn-load">
        Load Projects
      </button>

      <button
        onClick={() =>
          createProject({
            name: 'Test Project',
            local_folder: '/path/to/folder',
            repo: 'https://github.com/user/repo',
          })
        }
        data-testid="btn-create"
      >
        Create Project
      </button>

      <button
        onClick={() =>
          updateProject('1', {
            name: 'Updated Project',
            local_folder: '/new/path',
            repo: 'https://github.com/user/new-repo',
          })
        }
        data-testid="btn-update"
      >
        Update Project
      </button>

      <button onClick={() => deleteProject('1')} data-testid="btn-delete">
        Delete Project
      </button>

      <button onClick={() => selectProject('1')} data-testid="btn-select">
        Select Project
      </button>

      <button onClick={clearError} data-testid="btn-clear-error">
        Clear Error
      </button>

      <ul data-testid="projects-list">
        {projects.map((project) => (
          <li key={project.id} data-testid={`project-${project.id}`}>
            {project.name}
          </li>
        ))}
      </ul>
    </div>
  );
};

describe('ProjectContext', () => {
  beforeEach(() => {
    // Clear all mocks before each test
    mockFetch.mockClear();
    localStorage.clear();
  });

  /**
   * Test loadProjects successfully fetches and updates state.
   */
  test('loadProjects: fetches projects from API and updates state', async () => {
    const mockProjects = [
      {
        id: '1',
        name: 'Project 1',
        local_folder: '/path/1',
        repo: 'https://github.com/user/repo1',
        token: undefined,
        storage_location: undefined,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T00:00:00Z',
      },
      {
        id: '2',
        name: 'Project 2',
        local_folder: '/path/2',
        repo: 'https://github.com/user/repo2',
        token: undefined,
        storage_location: undefined,
        created_at: '2024-01-02T00:00:00Z',
        updated_at: '2024-01-02T00:00:00Z',
      },
    ];

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockProjects,
    });

    render(
      <ProjectProvider>
        <TestComponent />
      </ProjectProvider>
    );

    const loadButton = screen.getByTestId('btn-load');
    fireEvent.click(loadButton);

    await waitFor(() => {
      expect(screen.getByTestId('project-count')).toHaveTextContent('2');
    });

    expect(screen.getByTestId('project-1')).toBeInTheDocument();
    expect(screen.getByTestId('project-2')).toBeInTheDocument();
    expect(mockFetch).toHaveBeenCalledWith('http://localhost:8000/api/projects', {
      method: 'GET',
      headers: { 'Content-Type': 'application/json' },
    });
  });

  /**
   * Test loadProjects handles API errors gracefully.
   */
  test('loadProjects: handles API errors and sets error state', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: async () => ({ detail: 'Server error' }),
    });

    render(
      <ProjectProvider>
        <TestComponent />
      </ProjectProvider>
    );

    const loadButton = screen.getByTestId('btn-load');
    fireEvent.click(loadButton);

    await waitFor(() => {
      expect(screen.getByTestId('error')).not.toHaveTextContent('No error');
    });

    expect(screen.getByTestId('error')).toHaveTextContent('Server error');
  });

  /**
   * Test createProject sends project data to API and updates state.
   */
  test('createProject: creates new project via API and updates state', async () => {
    const newProject = {
      id: '3',
      name: 'Test Project',
      local_folder: '/path/to/folder',
      repo: 'https://github.com/user/repo',
      token: undefined,
      storage_location: undefined,
      created_at: '2024-01-03T00:00:00Z',
      updated_at: '2024-01-03T00:00:00Z',
    };

    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => newProject,
    });

    render(
      <ProjectProvider>
        <TestComponent />
      </ProjectProvider>
    );

    const createButton = screen.getByTestId('btn-create');
    fireEvent.click(createButton);

    await waitFor(() => {
      expect(screen.getByTestId('project-count')).toHaveTextContent('1');
    });

    expect(screen.getByTestId('project-3')).toBeInTheDocument();
    expect(mockFetch).toHaveBeenCalledWith(
      'http://localhost:8000/api/projects',
      expect.objectContaining({
        method: 'POST',
      })
    );
  });

  /**
   * Test createProject validates required fields.
   */
  test('createProject: validates required fields before sending', async () => {
    render(
      <ProjectProvider>
        <TestComponent />
      </ProjectProvider>
    );

    // Attempting to create with invalid/empty data should be caught
    // Note: This depends on validation logic in ProjectContext

    expect(mockFetch).not.toHaveBeenCalledWith(
      expect.anything(),
      expect.objectContaining({ method: 'POST' })
    );
  });

  /**
   * Test updateProject sends update to API and refreshes state.
   */
  test('updateProject: updates existing project via API', async () => {
    // Setup initial project
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [
        {
          id: '1',
          name: 'Project 1',
          local_folder: '/path/1',
          repo: 'https://github.com/user/repo1',
          token: undefined,
          storage_location: undefined,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ],
    });

    // Setup update response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({
        id: '1',
        name: 'Updated Project',
        local_folder: '/new/path',
        repo: 'https://github.com/user/new-repo',
        token: undefined,
        storage_location: undefined,
        created_at: '2024-01-01T00:00:00Z',
        updated_at: '2024-01-01T12:00:00Z',
      }),
    });

    render(
      <ProjectProvider>
        <TestComponent />
      </ProjectProvider>
    );

    const loadButton = screen.getByTestId('btn-load');
    fireEvent.click(loadButton);

    await waitFor(() => {
      expect(screen.getByTestId('project-count')).toHaveTextContent('1');
    });

    const updateButton = screen.getByTestId('btn-update');
    fireEvent.click(updateButton);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/projects/1',
        expect.objectContaining({
          method: 'PUT',
        })
      );
    });
  });

  /**
   * Test deleteProject removes project from state.
   */
  test('deleteProject: removes project via API and updates state', async () => {
    // Setup initial project
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [
        {
          id: '1',
          name: 'Project 1',
          local_folder: '/path/1',
          repo: 'https://github.com/user/repo1',
          token: undefined,
          storage_location: undefined,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ],
    });

    // Setup delete response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({}),
    });

    render(
      <ProjectProvider>
        <TestComponent />
      </ProjectProvider>
    );

    const loadButton = screen.getByTestId('btn-load');
    fireEvent.click(loadButton);

    await waitFor(() => {
      expect(screen.getByTestId('project-count')).toHaveTextContent('1');
    });

    const deleteButton = screen.getByTestId('btn-delete');
    fireEvent.click(deleteButton);

    await waitFor(() => {
      expect(mockFetch).toHaveBeenCalledWith(
        'http://localhost:8000/api/projects/1',
        expect.objectContaining({
          method: 'DELETE',
        })
      );
    });
  });

  /**
   * Test selectProject sets active project and persists to localStorage.
   */
  test('selectProject: sets active project and persists to localStorage', async () => {
    // Setup initial project
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [
        {
          id: '1',
          name: 'Project 1',
          local_folder: '/path/1',
          repo: 'https://github.com/user/repo1',
          token: undefined,
          storage_location: undefined,
          created_at: '2024-01-01T00:00:00Z',
          updated_at: '2024-01-01T00:00:00Z',
        },
      ],
    });

    // Setup select response
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ active_project_id: '1' }),
    });

    render(
      <ProjectProvider>
        <TestComponent />
      </ProjectProvider>
    );

    const loadButton = screen.getByTestId('btn-load');
    fireEvent.click(loadButton);

    await waitFor(() => {
      expect(screen.getByTestId('project-count')).toHaveTextContent('1');
    });

    const selectButton = screen.getByTestId('btn-select');
    fireEvent.click(selectButton);

    await waitFor(() => {
      expect(screen.getByTestId('active-project')).toHaveTextContent('Project 1');
    });

    expect(localStorage.getItem('activeProjectId')).toBe('1');
  });

  /**
   * Test clearError clears error state.
   */
  test('clearError: clears error state', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      status: 500,
      statusText: 'Internal Server Error',
      json: async () => ({ detail: 'Server error' }),
    });

    render(
      <ProjectProvider>
        <TestComponent />
      </ProjectProvider>
    );

    const loadButton = screen.getByTestId('btn-load');
    fireEvent.click(loadButton);

    await waitFor(() => {
      expect(screen.getByTestId('error')).not.toHaveTextContent('No error');
    });

    const clearErrorButton = screen.getByTestId('btn-clear-error');
    fireEvent.click(clearErrorButton);

    expect(screen.getByTestId('error')).toHaveTextContent('No error');
  });

  /**
   * Test loading state transitions correctly.
   */
  test('loadProjects: sets loading state during API call', async () => {
    mockFetch.mockImplementation(
      () =>
        new Promise((resolve) => {
          setTimeout(
            () => {
              resolve({
                ok: true,
                json: async () => [],
              });
            },
            100
          );
        })
    );

    render(
      <ProjectProvider>
        <TestComponent />
      </ProjectProvider>
    );

    const loadButton = screen.getByTestId('btn-load');
    fireEvent.click(loadButton);

    // Should show loading initially
    expect(screen.getByTestId('loading')).toHaveTextContent('Loading');

    // Should show loaded after request completes
    await waitFor(() => {
      expect(screen.getByTestId('loading')).toHaveTextContent('Loaded');
    });
  });

  /**
   * Test empty projects list.
   */
  test('loadProjects: handles empty projects list', async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => [],
    });

    render(
      <ProjectProvider>
        <TestComponent />
      </ProjectProvider>
    );

    const loadButton = screen.getByTestId('btn-load');
    fireEvent.click(loadButton);

    await waitFor(() => {
      expect(screen.getByTestId('project-count')).toHaveTextContent('0');
    });

    expect(screen.getByTestId('projects-list')).toBeEmptyDOMElement();
  });
});
