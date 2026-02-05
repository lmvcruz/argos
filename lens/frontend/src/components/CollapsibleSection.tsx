/**
 * CollapsibleSection component for expandable/collapsible detail panels
 * Commonly used for detailed error/issue information
 */

import { ChevronDown, ChevronRight } from 'lucide-react';
import { useState } from 'react';

interface CollapsibleSectionProps {
  title: string;
  children: React.ReactNode;
  defaultExpanded?: boolean;
  icon?: React.ReactNode;
}

export function CollapsibleSection({
  title,
  children,
  defaultExpanded = false,
  icon,
}: CollapsibleSectionProps) {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);

  return (
    <div className="border border-gray-200 dark:border-gray-700 rounded-lg">
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full flex items-center gap-3 px-4 py-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition-colors"
      >
        {isExpanded ? (
          <ChevronDown size={20} className="text-gray-600 dark:text-gray-400 flex-shrink-0" />
        ) : (
          <ChevronRight size={20} className="text-gray-600 dark:text-gray-400 flex-shrink-0" />
        )}
        {icon && <div className="flex-shrink-0">{icon}</div>}
        <span className="font-semibold text-gray-900 dark:text-gray-100 text-left">
          {title}
        </span>
      </button>
      {isExpanded && (
        <div className="px-4 py-3 border-t border-gray-200 dark:border-gray-700 bg-gray-50 dark:bg-gray-800">
          {children}
        </div>
      )}
    </div>
  );
}
