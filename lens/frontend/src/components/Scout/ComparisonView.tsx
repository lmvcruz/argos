import React, { useState } from 'react';
import { GitBranch, RefreshCw } from 'lucide-react';

/**
 * ComparisonView
 *
 * Compare test results between two workflow runs.
 * Identifies regressions and improvements.
 */

const ComparisonView: React.FC = () => {
  const [workflow1, setWorkflow1] = useState('');
  const [workflow2, setWorkflow2] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const handleCompare = async () => {
    if (!workflow1 || !workflow2) return;

    setIsLoading(true);
    try {
      const response = await fetch('/api/scout/compare', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          workflow_id_1: parseInt(workflow1),
          workflow_id_2: parseInt(workflow2),
        }),
      });

      if (!response.ok) throw new Error('Comparison failed');
      const data = await response.json();
      // Handle comparison result
      console.log('Comparison:', data);
    } catch (error) {
      console.error('Error:', error);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="h-full flex flex-col bg-white">
      <div className="px-8 py-6 border-b border-gray-200 bg-gradient-to-r from-purple-50 to-pink-50">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <GitBranch className="w-6 h-6" />
          Workflow Comparison
        </h2>
        <p className="text-sm text-gray-600 mt-1">
          Compare test results between two workflow runs
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-8">
        <div className="max-w-2xl mx-auto">
          <div className="bg-white border border-gray-200 rounded-lg p-8">
            <div className="space-y-6">
              {/* Workflow 1 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  First Workflow Run ID
                </label>
                <input
                  type="number"
                  value={workflow1}
                  onChange={(e) => setWorkflow1(e.target.value)}
                  placeholder="Enter run ID"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Workflow 2 */}
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Second Workflow Run ID
                </label>
                <input
                  type="number"
                  value={workflow2}
                  onChange={(e) => setWorkflow2(e.target.value)}
                  placeholder="Enter run ID"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              {/* Compare Button */}
              <button
                onClick={handleCompare}
                disabled={!workflow1 || !workflow2 || isLoading}
                className="w-full py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors font-medium flex items-center justify-center gap-2"
              >
                <RefreshCw className={`w-4 h-4 ${isLoading ? 'animate-spin' : ''}`} />
                {isLoading ? 'Comparing...' : 'Compare Workflows'}
              </button>

              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
                <p className="text-sm text-blue-800">
                  💡 Select two workflow runs to compare their test results. You'll see:
                </p>
                <ul className="mt-2 text-sm text-blue-800 space-y-1">
                  <li>✓ Tests that passed in both</li>
                  <li>✓ Tests that failed in only one</li>
                  <li>✓ Flaky tests (different outcomes)</li>
                </ul>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default ComparisonView;
