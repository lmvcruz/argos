/**
 * Scout Sync Status Bar Component
 * Displays CI data sync status with manual refresh button
 */

import { RefreshCw, Loader, AlertCircle, Check } from 'lucide-react';
import { useState } from 'react';
import { useAsync } from '../hooks';
import { scoutClient } from '../api/tools/scoutClient';

interface SyncStatus {
  last_sync: string | null;
  status: 'synced' | 'empty' | 'error' | 'syncing';
  workflow_count: number;
  job_count: number;
  next_sync: string | null;
  error?: string;
}

interface Props {
  onRefresh?: () => void;
  autoRefreshInterval?: number; // milliseconds, 0 to disable
}

/**
 * SyncStatusBar - Shows Scout CI sync status and provides manual refresh
 */
export function SyncStatusBar({
  onRefresh,
  autoRefreshInterval = 300000, // 5 minutes
}: Props) {
  const [isSyncing, setIsSyncing] = useState(false);
  const { data: syncStatus, fetch: fetchStatus, loading } = useAsync<SyncStatus>(
    async () => {
      const response = await fetch('/api/scout/sync-status');
      if (!response.ok) throw new Error('Failed to fetch sync status');
      return response.json();
    }
  );

  // Initial load
  const handleManualRefresh = async () => {
    setIsSyncing(true);
    try {
      await fetchStatus();
      onRefresh?.();
    } finally {
      setIsSyncing(false);
    }
  };

  // Format timestamp
  const formatTime = (isoString: string | null) => {
    if (!isoString) return 'Never';
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMinutes = Math.floor(diffMs / 60000);

    if (diffMinutes < 1) return 'Just now';
    if (diffMinutes < 60) return `${diffMinutes}m ago`;

    const diffHours = Math.floor(diffMinutes / 60);
    if (diffHours < 24) return `${diffHours}h ago`;

    return date.toLocaleDateString();
  };

  // Determine status color
  const getStatusColor = () => {
    if (isSyncing || loading) return 'text-blue-600 dark:text-blue-400';
    if (!syncStatus) return 'text-gray-600 dark:text-gray-400';

    switch (syncStatus.status) {
      case 'synced':
        return 'text-green-600 dark:text-green-400';
      case 'empty':
        return 'text-yellow-600 dark:text-yellow-400';
      case 'error':
        return 'text-red-600 dark:text-red-400';
      default:
        return 'text-gray-600 dark:text-gray-400';
    }
  };

  // Determine status icon
  const getStatusIcon = () => {
    if (isSyncing || loading) {
      return <Loader className="animate-spin" size={16} />;
    }

    if (!syncStatus) {
      return <AlertCircle size={16} />;
    }

    switch (syncStatus.status) {
      case 'synced':
        return <Check size={16} />;
      case 'empty':
        return <AlertCircle size={16} />;
      case 'error':
        return <AlertCircle size={16} />;
      default:
        return <AlertCircle size={16} />;
    }
  };

  // Get status text
  const getStatusText = () => {
    if (isSyncing) return 'Syncing...';
    if (loading) return 'Loading status...';
    if (!syncStatus) return 'Unknown';

    switch (syncStatus.status) {
      case 'synced':
        return `Synced (${syncStatus.workflow_count} workflows, ${syncStatus.job_count} jobs)`;
      case 'empty':
        return 'No CI data (sync required)';
      case 'error':
        return `Error: ${syncStatus.error || 'Unknown error'}`;
      default:
        return 'Unknown status';
    }
  };

  return (
    <div className="bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4">
      <div className="flex items-center justify-between gap-4">
        <div className="flex items-center gap-3 flex-1">
          <div className={`${getStatusColor()} flex-shrink-0`}>
            {getStatusIcon()}
          </div>
          <div className="flex-1">
            <p className={`text-sm font-medium ${getStatusColor()}`}>
              {getStatusText()}
            </p>
            {syncStatus && syncStatus.last_sync && (
              <p className="text-xs text-gray-500 dark:text-gray-400">
                Last sync: {formatTime(syncStatus.last_sync)}
              </p>
            )}
          </div>
        </div>

        <button
          onClick={handleManualRefresh}
          disabled={isSyncing || loading}
          className={`
            flex items-center gap-2 px-4 py-2 rounded-lg font-medium text-sm
            transition-all duration-200
            ${
              isSyncing || loading
                ? 'bg-gray-100 dark:bg-gray-700 text-gray-400 cursor-not-allowed'
                : 'bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 hover:bg-blue-100 dark:hover:bg-blue-900/50'
            }
          `}
          title={
            isSyncing || loading
              ? 'Syncing...'
              : 'Manually refresh CI data from GitHub'
          }
        >
          <RefreshCw
            size={16}
            className={isSyncing || loading ? 'animate-spin' : ''}
          />
          <span className="hidden sm:inline">
            {isSyncing ? 'Syncing...' : 'Refresh'}
          </span>
        </button>
      </div>
    </div>
  );
}

export default SyncStatusBar;
