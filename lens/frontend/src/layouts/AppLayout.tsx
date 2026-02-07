/**
 * Application layout component.
 *
 * Provides consistent layout structure with navigation and content area.
 * Manages page switching based on navigation tab selection.
 */

import React, { useState } from 'react';
import Navigation from '../components/Navigation';
import ConfigPage from '../pages/ConfigPage';
import LocalInspection from '../pages/LocalInspection';
import LocalTests from '../pages/LocalTests';
import CIInspection from '../pages/CIInspection';
import './AppLayout.css';

export type PageType = 'config' | 'inspection' | 'tests' | 'ci';

interface AppLayoutProps {
  children?: React.ReactNode;
  initialPage?: PageType;
}

/**
 * AppLayout - Main application layout.
 *
 * Manages page switching via Navigation tabs.
 * Renders appropriate page component based on currentPage state.
 */
export const AppLayout: React.FC<AppLayoutProps> = ({ children, initialPage = 'config' }) => {
  const [currentPage, setCurrentPage] = useState<PageType>(initialPage);

  /**
   * Render the appropriate page component based on currentPage.
   */
  const renderPage = () => {
    switch (currentPage) {
      case 'config':
        return <ConfigPage />;
      case 'inspection':
        return <LocalInspection />;
      case 'tests':
        return <LocalTests />;
      case 'ci':
        return <CIInspection />;
      default:
        return <ConfigPage />;
    }
  };

  return (
    <div className="app-layout">
      <Navigation currentPage={currentPage} onPageChange={setCurrentPage} />
      <main className="app-content">
        {children || renderPage()}
      </main>
      <footer className="app-footer">
        <p>Lens UI v2.0 | Built for CI/CD Inspection</p>
      </footer>
    </div>
  );
};

export default AppLayout;
