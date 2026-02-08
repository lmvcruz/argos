/**
 * TestFileTree - File tree view for test discovery.
 *
 * Displays a hierarchical view of folders and files containing test_*.py files.
 * Supports single and multiple selection of files and folders for test execution.
 */

import React, { useState, useMemo } from 'react';
import { ChevronRight, ChevronDown, Folder, FileCode, CheckSquare, Square } from 'lucide-react';

export interface FileTreeNode {
  id: string;
  name: string;
  path: string;
  type: 'folder' | 'file';
  children?: FileTreeNode[];
  isTestFile?: boolean;
}

export interface TestFileTreeProps {
  nodes: FileTreeNode[];
  selectedItems?: Set<string>;
  onSelectionChange?: (selected: Set<string>) => void;
  onViewChange?: (viewMode: 'tree' | 'list') => void;
}

/**
 * TestFileTree component - Hierarchical file/folder view for test discovery.
 *
 * Displays folders and test files in a tree structure. Users can select
 * multiple files and folders to run tests. Only shows folders that contain
 * test_*.py files and those files themselves.
 *
 * Args:
 *   nodes: Root-level file tree nodes
 *   selectedItems: Set of selected file/folder IDs
 *   onSelectionChange: Callback when selection changes
 *   onViewChange: Callback to switch between tree and list view
 */
export const TestFileTree: React.FC<TestFileTreeProps> = ({
  nodes,
  selectedItems = new Set(),
  onSelectionChange,
  onViewChange,
}) => {
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());

  const toggleFolder = (id: string) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(id)) {
      newExpanded.delete(id);
    } else {
      newExpanded.add(id);
    }
    setExpandedFolders(newExpanded);
  };

  const toggleSelection = (id: string, isParent: boolean = false) => {
    const newSelected = new Set(selectedItems);
    if (newSelected.has(id)) {
      newSelected.delete(id);
    } else {
      newSelected.add(id);
    }
    onSelectionChange?.(newSelected);
  };

  const TreeNode: React.FC<{ node: FileTreeNode; depth: number }> = ({ node, depth }) => {
    const isExpanded = expandedFolders.has(node.id);
    const isSelected = selectedItems.has(node.id);
    const hasChildren = node.children && node.children.length > 0;

    return (
      <div key={node.id}>
        <div
          className={`flex items-center gap-2 py-1.5 px-2 rounded cursor-pointer transition-colors ${
            isSelected
              ? 'bg-blue-100 dark:bg-blue-900/40'
              : 'hover:bg-gray-100 dark:hover:bg-gray-700'
          }`}
          style={{ marginLeft: `${depth * 16}px` }}
        >
          {node.type === 'folder' && hasChildren && (
            <button
              onClick={(e) => {
                e.stopPropagation();
                toggleFolder(node.id);
              }}
              className="p-0.5 hover:bg-gray-200 dark:hover:bg-gray-600 rounded"
            >
              {isExpanded ? (
                <ChevronDown size={16} className="text-gray-600 dark:text-gray-400" />
              ) : (
                <ChevronRight size={16} className="text-gray-600 dark:text-gray-400" />
              )}
            </button>
          )}
          {node.type === 'folder' && !hasChildren && <div className="w-4" />}

          <button
            onClick={() => toggleSelection(node.id, node.type === 'folder')}
            className="p-0 text-gray-600 dark:text-gray-400 hover:text-blue-600 dark:hover:text-blue-400"
          >
            {isSelected ? (
              <CheckSquare size={16} className="text-blue-600 dark:text-blue-400" />
            ) : (
              <Square size={16} />
            )}
          </button>

          {node.type === 'folder' ? (
            <>
              <Folder size={16} className="text-gray-500 dark:text-gray-500" />
              <span className="text-sm font-medium text-gray-700 dark:text-gray-300 flex-1 truncate">
                {node.name}
              </span>
              {hasChildren && (
                <span className="text-xs text-gray-500 dark:text-gray-500 ml-auto">
                  ({node.children!.length})
                </span>
              )}
            </>
          ) : (
            <>
              <FileCode size={16} className="text-amber-600 dark:text-amber-500" />
              <span className="text-sm text-gray-700 dark:text-gray-300 flex-1 truncate font-mono">
                {node.name}
              </span>
            </>
          )}
        </div>

        {node.type === 'folder' && isExpanded && hasChildren && (
          <div>
            {node.children!.map((child) => (
              <TreeNode key={child.id} node={child} depth={depth + 1} />
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="space-y-2">
      <div className="flex gap-1 pb-2 border-b border-gray-200 dark:border-gray-700">
        <button
          onClick={() => onViewChange?.('tree')}
          className="text-xs px-2 py-1 rounded bg-blue-600 text-white"
          title="Tree view"
        >
          Tree
        </button>
        <button
          onClick={() => onViewChange?.('list')}
          className="text-xs px-2 py-1 rounded bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300"
          title="List view"
        >
          List
        </button>
      </div>

      <div className="max-h-96 overflow-y-auto">
        {nodes.length > 0 ? (
          nodes.map((node) => <TreeNode key={node.id} node={node} depth={0} />)
        ) : (
          <div className="text-sm text-gray-500 dark:text-gray-400 py-4 text-center">
            No test files found
          </div>
        )}
      </div>

      {selectedItems.size > 0 && (
        <div className="text-xs text-gray-600 dark:text-gray-400 pt-2 border-t border-gray-200 dark:border-gray-700">
          {selectedItems.size} item{selectedItems.size !== 1 ? 's' : ''} selected
        </div>
      )}
    </div>
  );
};
