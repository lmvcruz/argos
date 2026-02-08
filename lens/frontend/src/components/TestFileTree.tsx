/**
 * TestFileTree - File tree view for test discovery.
 *
 * Displays a hierarchical view of folders and files containing test_*.py files.
 * Supports single and multiple selection of files and folders for test execution.
 */

import React, { useState, useMemo } from 'react';
import { ChevronRight, ChevronDown, Folder, FileCode, CheckSquare, Square } from 'lucide-react';
import '../styles/TreeStyles.css';

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
          className={`tree-node ${isSelected ? 'selected' : ''}`}
          style={{ paddingLeft: `${depth * 16}px` }}
          onClick={() => {
            if (node.type === 'folder' && hasChildren) {
              toggleFolder(node.id);
            }
          }}
        >
          <div className="tree-node-content">
            {node.type === 'folder' && hasChildren && (
              <button
                onClick={(e) => {
                  e.stopPropagation();
                  toggleFolder(node.id);
                }}
                className="tree-toggle"
              >
                {isExpanded ? (
                  <ChevronDown size={16} />
                ) : (
                  <ChevronRight size={16} />
                )}
              </button>
            )}
            {node.type === 'folder' && !hasChildren && <div className="tree-toggle-placeholder" />}

            <button
              onClick={(e) => {
                e.stopPropagation();
                toggleSelection(node.id, node.type === 'folder');
              }}
              className={`tree-checkbox ${isSelected ? 'checked' : ''}`}
            >
              {isSelected ? (
                <CheckSquare size={16} />
              ) : (
                <Square size={16} />
              )}
            </button>

            {node.type === 'folder' ? (
              <>
                <div className="tree-icon folder">
                  <Folder size={16} />
                </div>
                <span className="tree-label bold">
                  {node.name}
                </span>
                {hasChildren && (
                  <span className="tree-badge">
                    {node.children!.length}
                  </span>
                )}
              </>
            ) : (
              <>
                <div className="tree-icon test-file">
                  <FileCode size={16} />
                </div>
                <span className="tree-label">
                  {node.name}
                </span>
              </>
            )}
          </div>
        </div>

        {node.type === 'folder' && isExpanded && hasChildren && (
          <div className="tree-children">
            {node.children!.map((child) => (
              <TreeNode key={child.id} node={child} depth={depth + 1} />
            ))}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="tree-view">
      {nodes.length > 0 ? (
        nodes.map((node) => <TreeNode key={node.id} node={node} depth={0} />)
      ) : (
        <div className="tree-empty">
          No test files found
        </div>
      )}

      {selectedItems.size > 0 && (
        <div className="tree-footer">
          <span>
            {selectedItems.size} item{selectedItems.size !== 1 ? 's' : ''} selected
          </span>
        </div>
      )}
    </div>
  );
};
