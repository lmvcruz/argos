/**
 * Navigation component.
 *
 * Main navigation bar with tabs and project selector.
 */

import React, { useState } from 'react';
import { useProjects } from '../contexts/ProjectContext';
import './Navigation.css';

type Page = 'config' | 'inspection' | 'tests' | 'ci' | 'logs';

interface NavigationProps {
  currentPage?: Page;
  onPageChange?: (page: Page) => void;
}

/**
 * Navigation - Main navigation bar.
 */
export const Navigation: React.FC<NavigationProps> = ({
  currentPage = 'config',
  onPageChange
}) => {
  const { activeProject, projects, selectProject } = useProjects();
  const [projectDropdownOpen, setProjectDropdownOpen] = useState(false);

  const pages: { id: Page; label: string; icon: string }[] = [
    { id: 'config', label: 'Configuration', icon: '⚙️' },
    { id: 'inspection', label: 'Local Inspection', icon: '🔍' },
    { id: 'tests', label: 'Local Tests', icon: '✓' },
    { id: 'ci', label: 'CI Inspections', icon: '🚀' },
    { id: 'logs', label: 'Logs', icon: '📋' },
  ];

  const handleProjectSelect = async (projectId: number) => {
    try {
      await selectProject(projectId);
      setProjectDropdownOpen(false);
    } catch (err) {
      console.error('Error selecting project:', err);
    }
  };

  return (
    <nav className="navigation">
      <div className="nav-container">
        <div className="nav-brand">
          <h1>Lens</h1>
          <span className="nav-version">v2.0</span>
        </div>

        <div className="nav-tabs">
          {pages.map((page) => (
            <button
              key={page.id}
              className={`nav-tab ${currentPage === page.id ? 'active' : ''}`}
              onClick={() => onPageChange?.(page.id)}
              title={page.label}
            >
              <span className="tab-icon">{page.icon}</span>
              <span className="tab-label">{page.label}</span>
            </button>
          ))}
        </div>

        <div className="nav-right">
          <div className="project-selector">
            <button
              className="project-selector-btn"
              onClick={() => setProjectDropdownOpen(!projectDropdownOpen)}
              title={activeProject?.name || 'No project selected'}
            >
              <span className="project-icon">📁</span>
              <span className="project-name">
                {activeProject?.name || 'No Project'}
              </span>
              <span className={`dropdown-icon ${projectDropdownOpen ? 'open' : ''}`}>
                ▼
              </span>
            </button>

            {projectDropdownOpen && (
              <div className="project-dropdown">
                {projects.length === 0 ? (
                  <div className="dropdown-empty">No projects available</div>
                ) : (
                  <ul className="dropdown-list">
                    {projects.map((project) => (
                      <li key={project.id}>
                        <button
                          className={`dropdown-item ${
                            activeProject?.id === project.id ? 'active' : ''
                          }`}
                          onClick={() => handleProjectSelect(project.id!)}
                        >
                          {activeProject?.id === project.id && (
                            <span className="active-indicator">✓</span>
                          )}
                          <span className="project-item-name">{project.name}</span>
                          <span className="project-item-repo">{project.repo}</span>
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
              </div>
            )}
          </div>

          <button
            className="nav-button"
            title="Settings"
            onClick={() => alert('Settings coming in Phase 2.5')}
          >
            ⚙️
          </button>

          <button
            className="nav-button"
            title="Help"
            onClick={() => alert('Help coming in Phase 2.5')}
          >
            ?
          </button>
        </div>
      </div>
    </nav>
  );
};

export default Navigation;
