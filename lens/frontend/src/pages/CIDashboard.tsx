import React, { useEffect, useState } from 'react';
import {
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
} from 'recharts';
import { RefreshCw, TrendingUp, AlertCircle } from 'lucide-react';
import api from '../api/client';

/**
 * CI Health Dashboard
 *
 * Displays:
 * - CI success/failure rate trends
 * - Platform breakdown (Windows/Linux/macOS)
 * - Python version matrix
 * - Recent failures list
 */
export default function CIDashboard() {
  const [stats, setStats] = useState<any>(null);
  const [executions, setExecutions] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedWorkflow, setSelectedWorkflow] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, [selectedWorkflow]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [statsData, executionsData] = await Promise.all([
        api.getCIStatistics(selectedWorkflow || undefined),
        api.getCIExecutions(selectedWorkflow || undefined, 50),
      ]);
      setStats(statsData);
      setExecutions(executionsData.executions || []);
    } catch (error) {
      console.error('Failed to fetch CI data:', error);
    } finally {
      setLoading(false);
    }
  };

  // Generate trend data from executions
  const trendData = executions
    .slice(-20)
    .reverse()
    .map((exec, idx) => ({
      index: idx,
      pass_rate: ((exec.passed / exec.total_tests) * 100).toFixed(1),
      total: exec.total_tests,
    }));

  // Platform distribution
  const platformCounts = executions.reduce((acc: any, exec: any) => {
    acc[exec.platform] = (acc[exec.platform] || 0) + 1;
    return acc;
  }, {});

  const platformData = Object.entries(platformCounts).map(([name, count]) => ({
    name: (name as string).charAt(0).toUpperCase() + (name as string).slice(1),
    value: count,
  }));

  const COLORS = ['#3b82f6', '#10b981', '#f59e0b', '#ef4444'];

  return (
    <div className="p-8 space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-4xl font-bold mb-2">CI Health Dashboard</h1>
          <p className="text-gray-400">Real-time monitoring of CI pipeline health</p>
        </div>
        <button
          onClick={fetchData}
          disabled={loading}
          className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors disabled:opacity-50"
        >
          <RefreshCw size={20} className={loading ? 'animate-spin' : ''} />
          Refresh
        </button>
      </div>

      {/* Stats Cards */}
      {stats && (
        <div className="grid grid-cols-4 gap-4">
          <StatCard
            label="Total Runs"
            value={stats.total_runs}
            subtext={`Avg duration: ${stats.average_duration?.toFixed(1)}s`}
          />
          <StatCard
            label="Pass Rate"
            value={`${stats.pass_rate?.toFixed(1)}%`}
            subtext="Last 50 executions"
            icon={<TrendingUp size={20} />}
          />
          <StatCard
            label="Passed"
            value={stats.passed}
            subtext={`${((stats.passed / stats.total_runs) * 100).toFixed(1)}%`}
            color="text-green-500"
          />
          <StatCard
            label="Failed"
            value={stats.failed}
            subtext={`${((stats.failed / stats.total_runs) * 100).toFixed(1)}%`}
            color="text-red-500"
          />
        </div>
      )}

      {/* Charts */}
      <div className="grid grid-cols-2 gap-8">
        {/* Pass Rate Trend */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold mb-4">Pass Rate Trend</h2>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#444" />
              <XAxis dataKey="index" stroke="#888" />
              <YAxis stroke="#888" />
              <Tooltip contentStyle={{ backgroundColor: '#1f2937', border: '1px solid #444' }} />
              <Line
                type="monotone"
                dataKey="pass_rate"
                stroke="#10b981"
                strokeWidth={2}
                dot={false}
              />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Platform Distribution */}
        <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
          <h2 className="text-xl font-semibold mb-4">Platform Distribution</h2>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={platformData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={({ name, value }) => `${name}: ${value}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {platformData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip />
            </PieChart>
          </ResponsiveContainer>
        </div>
      </div>

      {/* Recent Executions */}
      <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
        <h2 className="text-xl font-semibold mb-4">Recent Executions</h2>
        <div className="overflow-x-auto">
          <table className="w-full">
            <thead>
              <tr className="border-b border-gray-700">
                <th className="text-left py-3 px-4">Workflow</th>
                <th className="text-left py-3 px-4">Platform</th>
                <th className="text-left py-3 px-4">Python</th>
                <th className="text-right py-3 px-4">Passed</th>
                <th className="text-right py-3 px-4">Failed</th>
                <th className="text-right py-3 px-4">Duration</th>
                <th className="text-right py-3 px-4">Status</th>
              </tr>
            </thead>
            <tbody>
              {executions.slice(0, 10).map((exec) => (
                <tr key={exec.id} className="border-b border-gray-700 hover:bg-gray-700">
                  <td className="py-3 px-4">{exec.workflow}</td>
                  <td className="py-3 px-4 text-sm text-gray-400">{exec.platform}</td>
                  <td className="py-3 px-4 text-sm text-gray-400">{exec.python_version}</td>
                  <td className="py-3 px-4 text-right text-green-500">{exec.passed}</td>
                  <td className="py-3 px-4 text-right text-red-500">{exec.failed}</td>
                  <td className="py-3 px-4 text-right text-gray-400">{exec.duration.toFixed(1)}s</td>
                  <td className="py-3 px-4 text-right">
                    <span
                      className={`px-3 py-1 rounded text-sm font-medium ${
                        exec.failed === 0
                          ? 'bg-green-900 text-green-200'
                          : 'bg-red-900 text-red-200'
                      }`}
                    >
                      {exec.failed === 0 ? 'PASSED' : 'FAILED'}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  subtext,
  color,
  icon,
}: {
  label: string;
  value: any;
  subtext?: string;
  color?: string;
  icon?: any;
}) {
  return (
    <div className="bg-gray-800 rounded-lg p-6 border border-gray-700">
      <div className="flex items-start justify-between mb-4">
        <span className="text-gray-400 text-sm">{label}</span>
        {icon && <div className="text-blue-500">{icon}</div>}
      </div>
      <div className={`text-3xl font-bold mb-2 ${color || 'text-white'}`}>{value}</div>
      {subtext && <p className="text-gray-500 text-sm">{subtext}</p>}
    </div>
  );
}
