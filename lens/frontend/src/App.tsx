/**
 * Main Lens Frontend Application
 *
 * Phase 2: Config Page & State Management
 *
 * Provides project management interface with:
 * - Project configuration (create, edit, delete)
 * - Project selection and active project management
 * - Navigation between inspection/test pages
 * - State management via ProjectContext
 */

import React, { useEffect } from 'react';
import { ProjectProvider } from './contexts/ProjectContext';
import AppLayout from './layouts/AppLayout';
import logger from './utils/logger';
import './App.css';

/**
 * App - Root application component
 *
 * Wraps the entire app with ProjectProvider for global state management,
 * then renders AppLayout which provides navigation and page switching.
 */
function App() {
  useEffect(() => {
    // Initialize logger on app load
    logger.info('Lens frontend initialized');
  }, []);

  return (
    <ProjectProvider>
      <AppLayout />
    </ProjectProvider>
  );
}

export default App;
