import React, { useEffect, useState } from 'react';
import { ChevronRight, Search, Filter, Clock, GitBranch, CheckCircle, XCircle } from 'lucide-react';
import { useScout, WorkflowRun, WorkflowJob } from '../../contexts/ScoutContext';

/**
 * WorkflowBrowser
 *
 * Browse and filter CI workflow runs.
 * Shows workflow list with filtering and selection.
 * Displays job details when a workflow is selected.
 */

const WorkflowBrowser: React.FC = () => {
  const {
    workflows,
    selectedWorkflow,
    jobs,
    workflowsLoading,
    jobsLoading,
    filters,
    setFilters,
    fetchWorkflows,
    selectWorkflow,
    clearSelection,
  } = useScout();

  const [searchTerm, setSearchTerm] = useState('');
  const [expandedJob, setExpandedJob] = useState<string | null>(null);

  // Load workflows on mount and when filters change
  useEffect(() => {
    fetchWorkflows();
  }, [filters, fetchWorkflows]);

  const handleWorkflowClick = (workflow: WorkflowRun) => {
    selectWorkflow(workflow);
  };

  const handleFilterChange = (key: string, value: any) => {
    setFilters({ [key]: value } as any);
  };

  // Filter workflows by search term
  const filteredWorkflows = workflows.filter((w) =>
    w.workflow_name.toLowerCase().includes(searchTerm.toLowerCase())
  );

  const formatDuration = (seconds?: number) => {
    if (!seconds) return 'N/A';
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}m ${secs}s`;
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', {
      month: 'short',
      day: 'numeric',
      hour: '2-digit',
      minute: '2-digit',
    });
  };

  return (
    <div className="h-full flex flex-col bg-white">
      {/* Filters & Search */}
      <div className="px-8 py-4 border-b border-gray-200 bg-gray-50">
        <div className="flex items-center gap-4">
          {/* Search */}
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              placeholder="Search workflows..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="w-full pl-10 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
            />
          </div>

          {/* Filters */}
          <div className="flex items-center gap-2">
            <Filter className="w-5 h-5 text-gray-600" />
            <select
              value={filters.workflowStatus || ''}
              onChange={(e) => handleFilterChange('workflowStatus', e.target.value || undefined)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Status</option>
              <option value="completed">Completed</option>
              <option value="in_progress">In Progress</option>
              <option value="queued">Queued</option>
            </select>

            <select
              value={filters.branch || ''}
              onChange={(e) => handleFilterChange('branch', e.target.value || undefined)}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            >
              <option value="">All Branches</option>
              <option value="main">main</option>
              <option value="develop">develop</option>
            </select>

            <select
              value={filters.workflowLimit}
              onChange={(e) => handleFilterChange('workflowLimit', parseInt(e.target.value))}
              className="px-3 py-2 border border-gray-300 rounded-lg text-sm focus:ring-2 focus:ring-blue-500"
            >
              <option value={10}>Last 10</option>
              <option value={20}>Last 20</option>
              <option value={50}>Last 50</option>
            </select>
          </div>
        </div>
      </div>

      <div className="flex-1 flex overflow-hidden">
        {/* Workflow List */}
        <div className={`overflow-y-auto ${selectedWorkflow ? 'w-1/2' : 'w-full'}`}>
          {workflowsLoading ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
                <p className="text-gray-600">Loading workflows...</p>
              </div>
            </div>
          ) : filteredWorkflows.length === 0 ? (
            <div className="flex items-center justify-center h-full">
              <div className="text-center">
                <p className="text-gray-500">No workflows found</p>
                {workflows.length === 0 && (
                  <p className="text-sm text-gray-400 mt-2">Run Scout sync to load CI data</p>
                )}
              </div>
            </div>
          ) : (
            <div className="divide-y divide-gray-200">
              {filteredWorkflows.map((workflow) => {
                const isSelected = selectedWorkflow?.run_id === workflow.run_id;
                const isSuccess = workflow.conclusion === 'success';

                return (
                  <div
                    key={workflow.run_id}
                    onClick={() => handleWorkflowClick(workflow)}
                    className={`px-6 py-4 cursor-pointer transition-colors ${
                      isSelected
                        ? 'bg-blue-50 border-l-4 border-blue-500'
                        : 'hover:bg-gray-50'
                    }`}
                  >
                    <div className="flex items-start justify-between gap-4">
                      <div className="flex-1">
                        <div className="flex items-center gap-3">
                          {isSuccess ? (
                            <CheckCircle className="w-5 h-5 text-green-500 flex-shrink-0" />
                          ) : (
                            <XCircle className="w-5 h-5 text-red-500 flex-shrink-0" />
                          )}
                          <h3 className="font-semibold text-gray-900">{workflow.workflow_name}</h3>
                          <span className="text-xs px-2 py-1 bg-gray-200 text-gray-700 rounded">
                            #{workflow.run_number}
                          </span>
                        </div>

                        <div className="mt-2 flex items-center gap-4 text-sm text-gray-600">
                          <div className="flex items-center gap-1">
                            <Clock className="w-4 h-4" />
                            {formatDate(workflow.started_at)}
                          </div>

                          <div className="flex items-center gap-1">
                            <GitBranch className="w-4 h-4" />
                            {workflow.branch}
                          </div>

                          {workflow.duration_seconds && (
                            <div>{formatDuration(workflow.duration_seconds)}</div>
                          )}
                        </div>

                        {workflow.commit_sha && (
                          <div className="mt-1 text-xs text-gray-500 font-mono">
                            {workflow.commit_sha.substring(0, 8)}
                          </div>
                        )}
                      </div>

                      {isSelected && (
                        <ChevronRight className="w-5 h-5 text-blue-500 flex-shrink-0 mt-1" />
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Job Details Panel */}
        {selectedWorkflow && (
          <div className="w-1/2 border-l border-gray-200 flex flex-col bg-gray-50">
            {/* Panel Header */}
            <div className="px-6 py-4 border-b border-gray-200 bg-white flex items-center justify-between">
              <h3 className="font-semibold text-gray-900">Jobs</h3>
              <button
                onClick={clearSelection}
                className="text-gray-500 hover:text-gray-700 font-medium text-sm"
              >
                Close
              </button>
            </div>

            {/* Panel Content */}
            {jobsLoading ? (
              <div className="flex items-center justify-center flex-1">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500 mx-auto mb-2"></div>
                  <p className="text-sm text-gray-600">Loading jobs...</p>
                </div>
              </div>
            ) : jobs.length === 0 ? (
              <div className="flex items-center justify-center flex-1">
                <p className="text-gray-500">No jobs found</p>
              </div>
            ) : (
              <div className="flex-1 overflow-y-auto">
                {jobs.map((job) => {
                  const isExpanded = expandedJob === job.job_id;
                  const jobSuccess = job.conclusion === 'success';

                  return (
                    <div key={job.job_id} className="border-b border-gray-200">
                      {/* Job Header */}
                      <button
                        onClick={() =>
                          setExpandedJob(isExpanded ? null : job.job_id)
                        }
                        className="w-full px-4 py-3 hover:bg-white transition-colors text-left flex items-start justify-between gap-4"
                      >
                        <div className="flex-1">
                          <div className="flex items-center gap-2">
                            {jobSuccess ? (
                              <CheckCircle className="w-4 h-4 text-green-500 flex-shrink-0" />
                            ) : (
                              <XCircle className="w-4 h-4 text-red-500 flex-shrink-0" />
                            )}
                            <span className="font-medium text-gray-900">{job.job_name}</span>
                          </div>

                          {job.runner_os && (
                            <div className="mt-1 text-xs text-gray-600">
                              {job.runner_os}
                              {job.python_version && ` • Python ${job.python_version}`}
                            </div>
                          )}

                          {job.duration_seconds && (
                            <div className="mt-1 text-xs text-gray-600">
                              {formatDuration(job.duration_seconds)}
                            </div>
                          )}
                        </div>

                        {job.test_count && (
                          <div className="text-right flex-shrink-0">
                            <div className="text-sm font-semibold text-gray-900">
                              {job.test_count}
                            </div>
                            <div className="text-xs text-gray-600">tests</div>
                          </div>
                        )}

                        <ChevronRight
                          className={`w-4 h-4 text-gray-400 flex-shrink-0 transition-transform ${
                            isExpanded ? 'rotate-90' : ''
                          }`}
                        />
                      </button>

                      {/* Job Details */}
                      {isExpanded && (
                        <div className="px-4 py-3 bg-white border-t border-gray-200 space-y-2 text-sm">
                          {job.status && (
                            <div>
                              <span className="text-gray-600">Status:</span>
                              <span className="ml-2 font-medium text-gray-900">
                                {job.status}/{job.conclusion}
                              </span>
                            </div>
                          )}

                          {job.test_count && (
                            <div>
                              <span className="text-gray-600">Tests:</span>
                              <span className="ml-2 font-medium text-gray-900">
                                {job.passed_count || 0} passed, {job.failed_count || 0} failed
                              </span>
                            </div>
                          )}

                          {job.started_at && (
                            <div>
                              <span className="text-gray-600">Started:</span>
                              <span className="ml-2 font-medium text-gray-900">
                                {formatDate(job.started_at)}
                              </span>
                            </div>
                          )}

                          <button className="mt-3 px-3 py-1 bg-blue-50 text-blue-700 rounded text-xs font-medium hover:bg-blue-100 transition-colors">
                            View Tests
                          </button>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default WorkflowBrowser;
