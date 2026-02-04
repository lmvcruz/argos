import React, { useState } from 'react';
import { Search, Loader } from 'lucide-react';
import api from '../api/client';

/**
 * Local vs CI Comparison Page
 *
 * Displays:
 * - Side-by-side comparison of test results
 * - Platform-specific failures
 * - Local-only and CI-only failures
 */
export default function Comparison() {
  const [entityId, setEntityId] = useState('');
  const [comparison, setComparison] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleCompare = async () => {
    if (!entityId.trim()) {
      setError('Please enter a test ID or file path');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const result = await api.compareEntity(entityId, 'test');
      setComparison(result);
    } catch (err: any) {
      setError(err.message || 'Failed to compare entity');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-4xl font-bold mb-2">Local vs CI Comparison</h1>
        <p className="text-gray-400">Compare test results between local execution and CI</p>
      </div>

      {/* Search Input */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <label className="block text-sm font-medium mb-3">Test ID or File Path</label>
        <div className="flex gap-3">
          <input
            type="text"
            value={entityId}
            onChange={(e) => setEntityId(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleCompare()}
            placeholder="e.g., tests/test_example.py::test_function"
            className="flex-1 bg-gray-700 border border-gray-600 rounded px-4 py-2 focus:outline-none focus:border-blue-500"
          />
          <button
            onClick={handleCompare}
            disabled={loading}
            className="flex items-center gap-2 px-6 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50"
          >
            {loading ? <Loader size={20} className="animate-spin" /> : <Search size={20} />}
            Compare
          </button>
        </div>
        {error && <p className="text-red-500 text-sm mt-2">{error}</p>}
      </div>

      {/* Comparison Results */}
      {comparison && (
        <div className="space-y-6">
          {/* Status Cards */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-gray-400 text-sm mb-2">Local Status</h3>
              <div
                className={`text-3xl font-bold ${
                  comparison.local_status === 'PASSED'
                    ? 'text-green-500'
                    : comparison.local_status === 'FAILED'
                    ? 'text-red-500'
                    : 'text-gray-500'
                }`}
              >
                {comparison.local_status || 'Unknown'}
              </div>
            </div>

            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h3 className="text-gray-400 text-sm mb-2">CI Status</h3>
              <div
                className={`text-3xl font-bold ${
                  comparison.ci_status === 'PASSED'
                    ? 'text-green-500'
                    : comparison.ci_status === 'FAILED'
                    ? 'text-red-500'
                    : 'text-gray-500'
                }`}
              >
                {comparison.ci_status || 'Unknown'}
              </div>
            </div>
          </div>

          {/* Platform Information */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h3 className="text-xl font-semibold mb-4">Platform Information</h3>
            {comparison.platform_specific ? (
              <div className="space-y-3">
                <p className="text-yellow-500 font-medium">⚠️ This is a platform-specific issue</p>
                <p className="text-gray-400">
                  This test fails on specific platforms. Affected platforms:
                </p>
                <div className="flex flex-wrap gap-2">
                  {comparison.platforms.map((platform: string) => (
                    <span
                      key={platform}
                      className="px-3 py-1 bg-yellow-900 text-yellow-200 rounded text-sm"
                    >
                      {platform}
                    </span>
                  ))}
                </div>
              </div>
            ) : (
              <p className="text-gray-400">Not platform-specific</p>
            )}
          </div>

          {/* Details */}
          <div className="grid grid-cols-2 gap-4">
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h4 className="text-sm font-medium text-gray-400 mb-3">Entity ID</h4>
              <p className="text-sm font-mono break-all">{comparison.entity_id}</p>
            </div>
            <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
              <h4 className="text-sm font-medium text-gray-400 mb-3">Entity Type</h4>
              <p className="text-sm">{comparison.entity_type}</p>
            </div>
          </div>
        </div>
      )}

      {/* No Results */}
      {!comparison && !loading && !error && (
        <div className="bg-gray-800 rounded-lg p-12 border border-gray-700 text-center">
          <p className="text-gray-400">Enter a test ID or file path to compare</p>
        </div>
      )}
    </div>
  );
}
