import React, { useEffect, useState } from 'react';
import { AlertCircle, RefreshCw, Copy } from 'lucide-react';
import api from '../api/client';

/**
 * Failure Patterns Page
 *
 * Displays:
 * - Platform-specific failures
 * - Failure pattern analysis
 * - Reproduction commands
 */
export default function FailurePatterns() {
  const [patterns, setPatterns] = useState<any>(null);
  const [loading, setLoading] = useState(true);
  const [copied, setCopied] = useState<string | null>(null);

  useEffect(() => {
    fetchPatterns();
  }, []);

  const fetchPatterns = async () => {
    try {
      setLoading(true);
      const result = await api.getPlatformSpecificFailures();
      setPatterns(result);
    } catch (error) {
      console.error('Failed to fetch failure patterns:', error);
    } finally {
      setLoading(false);
    }
  };

  const copyToClipboard = (text: string, id: string) => {
    navigator.clipboard.writeText(text);
    setCopied(id);
    setTimeout(() => setCopied(null), 2000);
  };

  const PatternGroup = ({ title, failures }: { title: string; failures: string[] }) => (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <h3 className="text-lg font-semibold mb-4 flex items-center gap-2">
        <AlertCircle size={20} className="text-yellow-500" />
        {title}
      </h3>
      {failures.length === 0 ? (
        <p className="text-gray-400 text-sm">No failures detected</p>
      ) : (
        <div className="space-y-2">
          {failures.map((failure, idx) => (
            <div key={idx} className="p-3 bg-gray-900 rounded border border-gray-700 text-sm">
              {failure}
            </div>
          ))}
        </div>
      )}
    </div>
  );

  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-bold mb-2">Failure Patterns</h1>
          <p className="text-gray-400">Analyze platform-specific and systematic failures</p>
        </div>
        <button
          onClick={fetchPatterns}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50"
        >
          <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {patterns && (
        <>
          {/* Summary Stats */}
          <div className="grid grid-cols-4 gap-4">
            <StatCard label="Total Patterns" value={patterns.total} />
            <StatCard
              label="Windows-only"
              value={patterns.windows_only?.length || 0}
              color="text-blue-500"
            />
            <StatCard
              label="Linux-only"
              value={patterns.linux_only?.length || 0}
              color="text-red-500"
            />
            <StatCard
              label="macOS-only"
              value={patterns.macos_only?.length || 0}
              color="text-gray-400"
            />
          </div>

          {/* Platform-Specific Failure Groups */}
          <div className="space-y-6">
            {patterns.windows_only && patterns.windows_only.length > 0 && (
              <PatternGroup title="🪟 Windows-Only Failures" failures={patterns.windows_only} />
            )}

            {patterns.linux_only && patterns.linux_only.length > 0 && (
              <PatternGroup title="🐧 Linux-Only Failures" failures={patterns.linux_only} />
            )}

            {patterns.macos_only && patterns.macos_only.length > 0 && (
              <PatternGroup title="🍎 macOS-Only Failures" failures={patterns.macos_only} />
            )}
          </div>

          {/* Reproduction Guide */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h2 className="text-xl font-semibold mb-4">Reproduction Guide</h2>
            <div className="space-y-4">
              {/* Windows Reproduction */}
              <div className="bg-gray-900 rounded p-4">
                <p className="text-sm font-medium mb-2 text-blue-400">🪟 Reproduce Windows Failures</p>
                <div className="bg-gray-800 rounded p-3 text-sm font-mono text-gray-300 overflow-auto">
                  <p># Using Docker (Linux host reproducing Windows issues)</p>
                  <p className="mt-2">docker run -it python:3.11-windows</p>
                  <p>pip install -e .</p>
                  <p>pytest tests/ -v</p>
                  <button
                    onClick={() =>
                      copyToClipboard('docker run -it python:3.11-windows\npip install -e .\npytest tests/ -v', 'windows')
                    }
                    className="mt-3 text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded inline-flex items-center gap-1"
                  >
                    <Copy size={14} />
                    {copied === 'windows' ? 'Copied!' : 'Copy'}
                  </button>
                </div>
              </div>

              {/* Linux Reproduction */}
              <div className="bg-gray-900 rounded p-4">
                <p className="text-sm font-medium mb-2 text-red-400">🐧 Reproduce Linux Failures</p>
                <div className="bg-gray-800 rounded p-3 text-sm font-mono text-gray-300 overflow-auto">
                  <p># Using Docker (any host)</p>
                  <p className="mt-2">docker run -it ubuntu:22.04</p>
                  <p>apt-get update && apt-get install -y python3-pip git</p>
                  <p>git clone {'{repo}'} && cd {'{repo}'}</p>
                  <p>pip install -e .</p>
                  <p>pytest tests/ -v</p>
                  <button
                    onClick={() =>
                      copyToClipboard('docker run -it ubuntu:22.04\napt-get update && apt-get install -y python3-pip git\npytest tests/ -v', 'linux')
                    }
                    className="mt-3 text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded inline-flex items-center gap-1"
                  >
                    <Copy size={14} />
                    {copied === 'linux' ? 'Copied!' : 'Copy'}
                  </button>
                </div>
              </div>

              {/* macOS Reproduction */}
              <div className="bg-gray-900 rounded p-4">
                <p className="text-sm font-medium mb-2 text-gray-400">🍎 Reproduce macOS Failures</p>
                <div className="bg-gray-800 rounded p-3 text-sm font-mono text-gray-300 overflow-auto">
                  <p># On macOS or using cloud macOS CI</p>
                  <p className="mt-2">brew install python@3.11</p>
                  <p>git clone {'{repo}'} && cd {'{repo}'}</p>
                  <p>/usr/local/opt/python@3.11/bin/python3 -m pip install -e .</p>
                  <p>pytest tests/ -v</p>
                  <button
                    onClick={() =>
                      copyToClipboard('brew install python@3.11\npytest tests/ -v', 'macos')
                    }
                    className="mt-3 text-xs px-2 py-1 bg-gray-700 hover:bg-gray-600 rounded inline-flex items-center gap-1"
                  >
                    <Copy size={14} />
                    {copied === 'macos' ? 'Copied!' : 'Copy'}
                  </button>
                </div>
              </div>
            </div>
          </div>

          {/* Common Causes */}
          <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
            <h2 className="text-xl font-semibold mb-4">Common Causes of Platform-Specific Failures</h2>
            <div className="space-y-3 text-sm text-gray-300">
              <div className="p-3 bg-gray-900 rounded border-l-4 border-blue-500">
                <p className="font-medium text-blue-400">Windows</p>
                <ul className="list-disc list-inside mt-1 text-xs space-y-1">
                  <li>Path separators (\\ vs /)</li>
                  <li>Line endings (CRLF vs LF)</li>
                  <li>Symlink limitations</li>
                  <li>File permission differences</li>
                  <li>Case-insensitive filesystem</li>
                </ul>
              </div>

              <div className="p-3 bg-gray-900 rounded border-l-4 border-red-500">
                <p className="font-medium text-red-400">Linux</p>
                <ul className="list-disc list-inside mt-1 text-xs space-y-1">
                  <li>Performance/timeout issues</li>
                  <li>Memory constraints in CI</li>
                  <li>Linux-specific system calls</li>
                  <li>GLIBC version differences</li>
                  <li>Locale/encoding issues</li>
                </ul>
              </div>

              <div className="p-3 bg-gray-900 rounded border-l-4 border-gray-400">
                <p className="font-medium text-gray-300">macOS</p>
                <ul className="list-disc list-inside mt-1 text-xs space-y-1">
                  <li>System library path differences</li>
                  <li>Homebrew package versions</li>
                  <li>macOS-specific APIs</li>
                  <li>Signing and security constraints</li>
                  <li>Performance on limited CI resources</li>
                </ul>
              </div>
            </div>
          </div>
        </>
      )}
    </div>
  );
}

function StatCard({
  label,
  value,
  color,
}: {
  label: string;
  value: any;
  color?: string;
}) {
  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <span className="text-gray-400 text-sm">{label}</span>
      <div className={`text-3xl font-bold mt-2 ${color || 'text-white'}`}>{value}</div>
    </div>
  );
}
