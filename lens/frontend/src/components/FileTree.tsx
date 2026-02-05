/**
 * FileTree component for displaying hierarchical file structures
 * Supports collapsible folders and file icons
 */

import { ChevronDown, ChevronRight, Folder, File } from 'lucide-react';
import { useState } from 'react';

export interface FileTreeNode {
  id: string;
  name: string;
  type: 'file' | 'folder';
  children?: FileTreeNode[];
  icon?: React.ReactNode;
  onClick?: (id: string) => void;
}

interface FileTreeProps {
  nodes: FileTreeNode[];
  level?: number;
  onSelectNode?: (nodeId: string) => void;
  selectedNodeId?: string;
  onSetAnalysisTarget?: (nodeId: string) => void;
  analysisTargetId?: string;
}

export function FileTree({
  nodes,
  level = 0,
  onSelectNode,
  selectedNodeId,
  onSetAnalysisTarget,
  analysisTargetId,
}: FileTreeProps) {
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(
    new Set()
  );

  const toggleFolder = (nodeId: string) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
    }
    setExpandedFolders(newExpanded);
  };

  const handleSelectNode = (nodeId: string) => {
    onSelectNode?.(nodeId);
  };

  const handleDoubleClick = (nodeId: string, nodeType: string) => {
    if (nodeType === 'folder') {
      onSetAnalysisTarget?.(nodeId);
    }
  };

  return (
    <div className="font-mono text-sm">
      {nodes.map((node) => (
        <div key={node.id}>
          <div
            className={`flex items-center gap-2 py-1 px-2 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 rounded ${
              selectedNodeId === node.id
                ? 'bg-blue-100 dark:bg-blue-900'
                : ''
            } ${
              analysisTargetId === node.id
                ? 'bg-green-100 dark:bg-green-900 border-l-2 border-green-600'
                : ''
            }`}
            style={{ paddingLeft: `${level * 16 + 8}px` }}
            onClick={() => {
              if (node.type === 'folder') {
                toggleFolder(node.id);
              }
              handleSelectNode(node.id);
            }}
            onDoubleClick={() => handleDoubleClick(node.id, node.type)}
            title={node.type === 'folder' ? 'Double-click to set as analysis target' : undefined}
          >
            {node.type === 'folder' ? (
              <>
                {expandedFolders.has(node.id) ? (
                  <ChevronDown size={16} className="text-gray-600" />
                ) : (
                  <ChevronRight size={16} className="text-gray-600" />
                )}
                <Folder size={16} className="text-yellow-600" />
              </>
            ) : (
              <>
                <div className="w-4" />
                {node.icon || <File size={16} className="text-gray-600" />}
              </>
            )}
            <span className="truncate">{node.name}</span>
            {analysisTargetId === node.id && (
              <span className="ml-auto text-xs bg-green-600 text-white px-2 py-0.5 rounded">
                Analysis Target
              </span>
            )}
          </div>

          {node.type === 'folder' &&
            expandedFolders.has(node.id) &&
            node.children && (
              <FileTree
                nodes={node.children}
                level={level + 1}
                onSelectNode={onSelectNode}
                selectedNodeId={selectedNodeId}
                onSetAnalysisTarget={onSetAnalysisTarget}
                analysisTargetId={analysisTargetId}
              />
            )}
        </div>
      ))}
    </div>
  );
}
