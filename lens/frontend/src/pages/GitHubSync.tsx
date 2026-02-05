import React, { useState } from 'react';
import { Download, AlertCircle, CheckCircle, Loader } from 'lucide-react';
import api from '../api/client';

/**
 * GitHub CI Data Sync Page
 *
 * Allows users to sync CI workflow runs from GitHub to Anvil database.
 * Provides input for GitHub token and repository information.
 */
function GitHubSync() {
  const [githubToken, setGithubToken] = useState('');
  const [owner, setOwner] = useState('');
  const [repo, setRepo] = useState('');
  const [limit, setLimit] = useState<number | string>('');
  const [workflow, setWorkflow] = useState('');
  const [forceDownload, setForceDownload] = useState(false);
  const [forceParse, setForceParse] = useState(false);
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<'idle' | 'success' | 'error'>('idle');
  const [message, setMessage] = useState('');
  const [output, setOutput] = useState('');

  const handleSync = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setStatus('idle');
    setMessage('');
    setOutput('');

    try {
      const response = await api.syncCIData({
        github_token: githubToken || undefined,
        owner: owner || undefined,
        repo: repo || undefined,
        limit: limit ? parseInt(limit as string) : undefined,
        workflow: workflow || undefined,
        force_download: forceDownload,
        force_parse: forceParse,
      });

      setStatus('success');
      setMessage('CI data synced successfully!');
      setOutput(response.output || '');

      // Clear inputs on success
      setGithubToken('');
      setOwner('');
      setRepo('');
      setLimit('');
      setWorkflow('');
      setForceDownload(false);
      setForceParse(false);
    } catch (error: any) {
      setStatus('error');
      setMessage(error.response?.data?.detail || 'Failed to sync CI data');
      setOutput(error.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 max-w-2xl mx-auto">
      <div className="flex items-center gap-3 mb-8">
        <Download size={32} className="text-blue-500" />
        <h1 className="text-3xl font-bold text-gray-900">GitHub CI Sync</h1>
      </div>

      <div className="bg-white rounded-lg shadow p-6 mb-6">
        <p className="text-gray-700 mb-6">
          Import CI workflow runs from GitHub into Anvil database. This allows Lens to analyze
          your CI/CD pipeline performance, detect flaky tests, and compare local vs CI execution results.
        </p>

        <form onSubmit={handleSync} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              GitHub Personal Access Token
            </label>
            <input
              type="password"
              value={githubToken}
              onChange={(e) => setGithubToken(e.target.value)}
              placeholder="ghp_xxxxxxxxxxxx or set GITHUB_TOKEN env var"
              className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
            />
            <p className="text-xs text-gray-500 mt-1">
              Create a token at https://github.com/settings/tokens with repo access
            </p>
          </div>

          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Repository Owner
              </label>
              <input
                type="text"
                value={owner}
                onChange={(e) => setOwner(e.target.value)}
                placeholder="e.g., lmvcruz"
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-1">
                Repository Name
              </label>
              <input
                type="text"
                value={repo}
                onChange={(e) => setRepo(e.target.value)}
                placeholder="e.g., argos"
                className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
              />
            </div>
          </div>

          <div className="border-t pt-4 mt-4">
            <h3 className="text-sm font-semibold text-gray-900 mb-3">Filtering Options (Optional)</h3>
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Limit to N recent runs
                </label>
                <input
                  type="number"
                  value={limit}
                  onChange={(e) => setLimit(e.target.value)}
                  placeholder="e.g., 5, 10, 20 (leave empty for all)"
                  min="1"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">Download only the last N workflow runs</p>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Filter by workflow name
                </label>
                <input
                  type="text"
                  value={workflow}
                  onChange={(e) => setWorkflow(e.target.value)}
                  placeholder="e.g., Anvil Tests (optional)"
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-blue-500 focus:border-blue-500"
                />
                <p className="text-xs text-gray-500 mt-1">Only download this workflow</p>
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4 mt-4">
              <label className="flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={forceDownload}
                  onChange={(e) => setForceDownload(e.target.checked)}
                  className="w-4 h-4 border border-gray-300 rounded focus:ring-blue-500"
                />
                Force re-download logs
              </label>
              <label className="flex items-center gap-2 text-sm text-gray-700">
                <input
                  type="checkbox"
                  checked={forceParse}
                  onChange={(e) => setForceParse(e.target.checked)}
                  className="w-4 h-4 border border-gray-300 rounded focus:ring-blue-500"
                />
                Force re-parse data
              </label>
            </div>
            <p className="text-xs text-gray-500 mt-2">Normally skips already downloaded/parsed data for speed</p>
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white font-medium py-2 px-4 rounded-md transition-colors flex items-center justify-center gap-2"
          >
            {loading ? (
              <>
                <Loader size={20} className="animate-spin" />
                Syncing CI Data...
              </>
            ) : (
              <>
                <Download size={20} />
                Sync CI Data from GitHub
              </>
            )}
          </button>
        </form>

        {status === 'success' && (
          <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-md">
            <div className="flex items-center gap-2 mb-2">
              <CheckCircle size={20} className="text-green-600" />
              <p className="text-green-800 font-medium">{message}</p>
            </div>
            {output && (
              <pre className="text-xs text-green-700 bg-white p-2 rounded border border-green-200 overflow-auto max-h-48">
                {output}
              </pre>
            )}
          </div>
        )}

        {status === 'error' && (
          <div className="mt-6 p-4 bg-red-50 border border-red-200 rounded-md">
            <div className="flex items-center gap-2 mb-2">
              <AlertCircle size={20} className="text-red-600" />
              <p className="text-red-800 font-medium">{message}</p>
            </div>
            {output && (
              <pre className="text-xs text-red-700 bg-white p-2 rounded border border-red-200 overflow-auto max-h-48">
                {output}
              </pre>
            )}
          </div>
        )}
      </div>

      <div className="bg-blue-50 border border-blue-200 rounded-lg p-6">
        <h3 className="font-semibold text-blue-900 mb-3">How to use:</h3>
        <ol className="list-decimal list-inside space-y-2 text-sm text-blue-800">
          <li>Create a GitHub Personal Access Token at https://github.com/settings/tokens with repo access</li>
          <li>Enter your token, repository owner, and repository name</li>
          <li>Click "Sync CI Data from GitHub"</li>
          <li>Wait for the sync to complete (may take a few minutes)</li>
          <li>View CI data in the CI Dashboard</li>
        </ol>
      </div>
    </div>
  );
}

export default GitHubSync;
