/**
 * TestTree component for displaying hierarchical test structures
 * Supports collapsible test files and status indicators
 */

import { ChevronDown, ChevronRight, FileText, Circle } from 'lucide-react';
import { useState } from 'react';

export interface TestNode {
  id: string;
  name: string;
  file: string;
  type: 'file' | 'test';
  status: 'not-run' | 'passed' | 'failed' | 'skipped';
  children?: TestNode[];
}

interface TestTreeProps {
  nodes: TestNode[];
  level?: number;
  onSelectTest?: (testId: string) => void;
  selectedTestId?: string;
  onRunTest?: (testId: string) => void;
}

function getStatusColor(status: string): string {
  switch (status) {
    case 'passed':
      return 'text-green-600';
    case 'failed':
      return 'text-red-600';
    case 'skipped':
      return 'text-gray-400';
    default:
      return 'text-gray-400';
  }
}

function getStatusLabel(status: string): string {
  switch (status) {
    case 'passed':
      return '✓';
    case 'failed':
      return '✗';
    case 'skipped':
      return '⊘';
    default:
      return '◯';
  }
}

export function TestTree({
  nodes,
  level = 0,
  onSelectTest,
  selectedTestId,
  onRunTest,
}: TestTreeProps) {
  const [expandedFiles, setExpandedFiles] = useState<Set<string>>(new Set());

  const toggleFile = (nodeId: string) => {
    const newExpanded = new Set(expandedFiles);
    if (newExpanded.has(nodeId)) {
      newExpanded.delete(nodeId);
    } else {
      newExpanded.add(nodeId);
    }
    setExpandedFiles(newExpanded);
  };

  const handleSelectTest = (nodeId: string) => {
    onSelectTest?.(nodeId);
  };

  return (
    <div className="font-mono text-sm">
      {nodes.map((node) => (
        <div key={node.id}>
          <div
            className={`flex items-center gap-2 py-1 px-2 cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-800 rounded ${
              selectedTestId === node.id
                ? 'bg-blue-100 dark:bg-blue-900'
                : ''
            }`}
            style={{ paddingLeft: `${level * 16 + 8}px` }}
            onClick={() => {
              if (node.type === 'file') {
                toggleFile(node.id);
              }
              handleSelectTest(node.id);
            }}
          >
            {node.type === 'file' ? (
              <>
                {expandedFiles.has(node.id) ? (
                  <ChevronDown size={16} className="text-gray-600" />
                ) : (
                  <ChevronRight size={16} className="text-gray-600" />
                )}
                <FileText size={16} className="text-blue-600" />
              </>
            ) : (
              <>
                <div className="w-4" />
                <Circle size={12} className={`${getStatusColor(node.status)} fill-current`} />
              </>
            )}
            <span className="truncate flex-1">{node.name}</span>
            <span className={`ml-auto text-xs font-semibold ${getStatusColor(node.status)}`}>
              {getStatusLabel(node.status)}
            </span>
          </div>
          {node.type === 'file' && expandedFiles.has(node.id) && node.children && (
            <TestTree
              nodes={node.children}
              level={level + 1}
              onSelectTest={onSelectTest}
              selectedTestId={selectedTestId}
              onRunTest={onRunTest}
            />
          )}
        </div>
      ))}
    </div>
  );
}
