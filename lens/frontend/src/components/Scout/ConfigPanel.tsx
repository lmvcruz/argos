import React, { useState, useEffect } from 'react';
import { Settings, Save } from 'lucide-react';

/**
 * ConfigPanel
 *
 * Scout configuration and settings management.
 */

const ConfigPanel: React.FC = () => {
  const [config, setConfig] = useState({
    githubToken: '',
    githubRepo: '',
    ciDbPath: 'scout.db',
    analysisDbPath: 'scout-analysis.db',
    fetchTimeout: 30,
    enableCache: true,
  });

  const [isSaving, setIsSaving] = useState(false);
  const [saved, setSaved] = useState(false);

  // Load config on mount
  useEffect(() => {
    const loadConfig = async () => {
      try {
        const response = await fetch('/api/scout/config');
        if (response.ok) {
          const data = await response.json();
          setConfig((prev) => ({ ...prev, ...data.settings }));
        }
      } catch (error) {
        console.error('Failed to load config:', error);
      }
    };

    loadConfig();
  }, []);

  const handleSave = async () => {
    setIsSaving(true);
    try {
      const response = await fetch('/api/scout/config', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(config),
      });

      if (response.ok) {
        setSaved(true);
        setTimeout(() => setSaved(false), 3000);
      }
    } catch (error) {
      console.error('Failed to save config:', error);
    } finally {
      setIsSaving(false);
    }
  };

  const handleChange = (key: string, value: any) => {
    setConfig((prev) => ({ ...prev, [key]: value }));
  };

  return (
    <div className="h-full flex flex-col bg-white">
      <div className="px-8 py-6 border-b border-gray-200 bg-gradient-to-r from-gray-50 to-gray-100">
        <h2 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
          <Settings className="w-6 h-6" />
          Configuration
        </h2>
        <p className="text-sm text-gray-600 mt-1">
          Manage Scout settings and integration options
        </p>
      </div>

      <div className="flex-1 overflow-y-auto p-8">
        <div className="max-w-2xl mx-auto space-y-8">
          {/* GitHub Settings */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">GitHub Integration</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  GitHub Token
                </label>
                <input
                  type="password"
                  value={config.githubToken}
                  onChange={(e) => handleChange('githubToken', e.target.value)}
                  placeholder="Enter your GitHub personal access token"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                />
                <p className="text-xs text-gray-600 mt-1">
                  You can also set GITHUB_TOKEN environment variable
                </p>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Repository (owner/repo)
                </label>
                <input
                  type="text"
                  value={config.githubRepo}
                  onChange={(e) => handleChange('githubRepo', e.target.value)}
                  placeholder="e.g., lmvcruz/argos"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-600 mt-1">
                  Or set GITHUB_REPO environment variable
                </p>
              </div>
            </div>
          </div>

          {/* Database Settings */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Database Settings</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  CI Database Path
                </label>
                <input
                  type="text"
                  value={config.ciDbPath}
                  onChange={(e) => handleChange('ciDbPath', e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Analysis Database Path
                </label>
                <input
                  type="text"
                  value={config.analysisDbPath}
                  onChange={(e) => handleChange('analysisDbPath', e.target.value)}
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                />
              </div>
            </div>
          </div>

          {/* Advanced Settings */}
          <div className="bg-white border border-gray-200 rounded-lg p-6">
            <h3 className="text-lg font-semibold text-gray-900 mb-4">Advanced Settings</h3>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Fetch Timeout (seconds)
                </label>
                <input
                  type="number"
                  value={config.fetchTimeout}
                  onChange={(e) => handleChange('fetchTimeout', parseInt(e.target.value))}
                  min="5"
                  max="300"
                  className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <p className="text-xs text-gray-600 mt-1">
                  Maximum time to wait for GitHub API responses
                </p>
              </div>

              <div className="flex items-center gap-3">
                <input
                  type="checkbox"
                  id="enableCache"
                  checked={config.enableCache}
                  onChange={(e) => handleChange('enableCache', e.target.checked)}
                  className="w-4 h-4 rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                />
                <label htmlFor="enableCache" className="text-sm font-medium text-gray-700">
                  Enable result caching
                </label>
              </div>
            </div>
          </div>

          {/* Info */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-blue-800">
              💡 Most settings can also be configured via environment variables for CI/CD
              integration.
            </p>
          </div>

          {/* Save Button */}
          <div className="flex items-center gap-3">
            <button
              onClick={handleSave}
              disabled={isSaving}
              className="flex items-center gap-2 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 transition-colors font-medium"
            >
              <Save className={`w-4 h-4 ${isSaving ? 'animate-spin' : ''}`} />
              {isSaving ? 'Saving...' : 'Save Settings'}
            </button>

            {saved && (
              <div className="text-green-700 text-sm font-medium">
                ✓ Settings saved successfully
              </div>
            )}
          </div>
        </div>
      </div>
    </div>
  );
};

export default ConfigPanel;
