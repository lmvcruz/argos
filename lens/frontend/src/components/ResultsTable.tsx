/**
 * ResultsTable component for displaying tabular analysis results
 * Supports sorting, filtering, and pagination
 */

import { ChevronUp, ChevronDown } from 'lucide-react';
import { useState } from 'react';

export interface TableColumn {
  key: string;
  label: string;
  width?: string;
  sortable?: boolean;
  render?: (value: unknown, row: Record<string, unknown>) => React.ReactNode;
}

export interface TableRow {
  id: string;
  [key: string]: unknown;
}

interface ResultsTableProps {
  columns: TableColumn[];
  rows: TableRow[];
  pageSize?: number;
  onRowClick?: (rowId: string) => void;
  selectedRowId?: string;
}

export function ResultsTable({
  columns,
  rows,
  pageSize = 20,
  onRowClick,
  selectedRowId,
}: ResultsTableProps) {
  const [currentPage, setCurrentPage] = useState(1);
  const [sortKey, setSortKey] = useState<string | null>(null);
  const [sortAsc, setSortAsc] = useState(true);

  let displayRows = [...rows];

  if (sortKey) {
    displayRows.sort((a, b) => {
      const aVal = a[sortKey];
      const bVal = b[sortKey];

      if (aVal === undefined || bVal === undefined) return 0;

      let comparison = 0;
      if (typeof aVal === 'string' && typeof bVal === 'string') {
        comparison = aVal.localeCompare(bVal);
      } else if (typeof aVal === 'number' && typeof bVal === 'number') {
        comparison = aVal - bVal;
      }

      return sortAsc ? comparison : -comparison;
    });
  }

  const totalPages = Math.ceil(displayRows.length / pageSize);
  const startIdx = (currentPage - 1) * pageSize;
  const paginatedRows = displayRows.slice(startIdx, startIdx + pageSize);

  const handleSort = (key: string) => {
    if (sortKey === key) {
      setSortAsc(!sortAsc);
    } else {
      setSortKey(key);
      setSortAsc(true);
    }
  };

  return (
    <div className="flex flex-col gap-4">
      <div className="overflow-x-auto border rounded-lg border-gray-200 dark:border-gray-700">
        <table className="w-full text-sm">
          <thead className="bg-gray-50 dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700">
            <tr>
              {columns.map((col) => (
                <th
                  key={col.key}
                  className={`px-4 py-3 text-left font-semibold text-gray-700 dark:text-gray-300 ${
                    col.sortable ? 'cursor-pointer hover:bg-gray-100 dark:hover:bg-gray-700' : ''
                  }`}
                  onClick={() =>
                    col.sortable && handleSort(col.key)
                  }
                  style={{ width: col.width }}
                >
                  <div className="flex items-center gap-2">
                    {col.label}
                    {col.sortable && sortKey === col.key && (
                      sortAsc ? (
                        <ChevronUp size={16} />
                      ) : (
                        <ChevronDown size={16} />
                      )
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {paginatedRows.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-6 text-center text-gray-500 dark:text-gray-400"
                >
                  No results found
                </td>
              </tr>
            ) : (
              paginatedRows.map((row) => (
                <tr
                  key={row.id}
                  className={`border-b border-gray-200 dark:border-gray-700 hover:bg-gray-50 dark:hover:bg-gray-800 cursor-pointer ${
                    selectedRowId === row.id
                      ? 'bg-blue-50 dark:bg-blue-900'
                      : ''
                  }`}
                  onClick={() => onRowClick?.(row.id)}
                >
                  {columns.map((col) => (
                    <td
                      key={`${row.id}-${col.key}`}
                      className="px-4 py-3 text-gray-700 dark:text-gray-300"
                    >
                      {col.render
                        ? col.render(row[col.key], row)
                        : String(row[col.key] ?? '-')}
                    </td>
                  ))}
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-between text-sm">
          <span className="text-gray-600 dark:text-gray-400">
            Showing {startIdx + 1} to{' '}
            {Math.min(startIdx + pageSize, displayRows.length)} of{' '}
            {displayRows.length}
          </span>
          <div className="flex gap-2">
            <button
              className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-50"
              onClick={() => setCurrentPage(Math.max(1, currentPage - 1))}
              disabled={currentPage === 1}
            >
              Previous
            </button>
            <span className="px-3 py-1">
              {currentPage} / {totalPages}
            </span>
            <button
              className="px-3 py-1 border border-gray-300 dark:border-gray-600 rounded hover:bg-gray-100 dark:hover:bg-gray-800 disabled:opacity-50"
              onClick={() => setCurrentPage(Math.min(totalPages, currentPage + 1))}
              disabled={currentPage === totalPages}
            >
              Next
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
