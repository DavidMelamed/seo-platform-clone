import { apiHelpers } from './apiClient';

export enum WorkflowStatus {
  PENDING = "pending",
  RUNNING = "running", 
  COMPLETED = "completed",
  FAILED = "failed",
  CANCELLED = "cancelled"
}

export enum ActionType {
  KEYWORD_RESEARCH = "keyword_research",
  RANK_TRACKING = "rank_tracking",
  CONTENT_OPTIMIZATION = "content_optimization",
  TECHNICAL_AUDIT = "technical_audit",
  BACKLINK_ANALYSIS = "backlink_analysis",
  COMPETITOR_ANALYSIS = "competitor_analysis",
  SERP_ANALYSIS = "serp_analysis",
  BULK_KEYWORD_UPDATE = "bulk_keyword_update",
  REPORT_GENERATION = "report_generation",
  EMAIL_NOTIFICATION = "email_notification"
}

export interface WorkflowStep {
  name: string;
  action: ActionType;
  parameters: Record<string, any>;
  condition?: string;
  retry_count: number;
  timeout_seconds: number;
}

export interface WorkflowCreate {
  name: string;
  description: string;
  project_id: string;
  steps: WorkflowStep[];
  schedule?: string;
  enabled: boolean;
  tags: string[];
}

export interface WorkflowUpdate {
  name?: string;
  description?: string;
  steps?: WorkflowStep[];
  schedule?: string;
  enabled?: boolean;
  tags?: string[];
}

export interface Workflow {
  id: string;
  name: string;
  description: string;
  project_id: string;
  steps: WorkflowStep[];
  schedule?: string;
  enabled: boolean;
  tags: string[];
  last_executed?: string;
  execution_count: number;
  success_rate: number;
  created_at: string;
  updated_at: string;
}

export interface WorkflowExecution {
  id: string;
  workflow_id: string;
  workflow_name: string;
  status: WorkflowStatus;
  progress: number;
  current_step?: string;
  started_at: string;
  completed_at?: string;
  duration_seconds?: number;
  output_data: Record<string, any>;
  error_log?: string;
}

export interface BulkOperationRequest {
  operation_type: ActionType;
  items: Record<string, any>[];
  batch_size: number;
  parallel_execution: boolean;
}

export interface ScheduledTask {
  id: string;
  workflow_id: string;
  workflow_name: string;
  schedule: string;
  next_run: string;
  enabled: boolean;
  last_run?: string;
  run_count: number;
}

export interface AutomationStats {
  total_workflows: number;
  active_workflows: number;
  total_executions: number;
  executions_today: number;
  success_rate: number;
  avg_execution_time: number;
  scheduled_tasks: number;
}

export interface WorkflowTemplate {
  id: string;
  name: string;
  description: string;
  steps: WorkflowStep[];
  schedule?: string;
  category: string;
}

export const automationService = {
  // Workflow management
  getWorkflows: (projectId: string): Promise<Workflow[]> => {
    return apiHelpers.get(`/automation/workflows/${projectId}`);
  },

  createWorkflow: (workflowData: WorkflowCreate): Promise<Workflow> => {
    return apiHelpers.post(`/automation/workflows/${workflowData.project_id}`, workflowData);
  },

  updateWorkflow: (projectId: string, workflowId: string, workflowData: WorkflowUpdate): Promise<Workflow> => {
    return apiHelpers.put(`/automation/workflows/${projectId}/${workflowId}`, workflowData);
  },

  deleteWorkflow: (projectId: string, workflowId: string): Promise<{ message: string }> => {
    return apiHelpers.delete(`/automation/workflows/${projectId}/${workflowId}`);
  },

  // Workflow execution
  executeWorkflow: (projectId: string, workflowId: string): Promise<{ execution_id: string; message: string; status: string }> => {
    return apiHelpers.post(`/automation/workflows/${projectId}/${workflowId}/execute`);
  },

  getWorkflowExecutions: (projectId: string, limit: number = 50): Promise<WorkflowExecution[]> => {
    return apiHelpers.get(`/automation/executions/${projectId}`, {
      params: { limit }
    });
  },

  getExecutionStatus: (executionId: string): Promise<WorkflowExecution> => {
    return apiHelpers.get(`/automation/executions/${executionId}/status`);
  },

  // Bulk operations
  createBulkOperation: (projectId: string, request: BulkOperationRequest): Promise<{ execution_id: string; message: string; status: string }> => {
    return apiHelpers.post(`/automation/bulk-operations/${projectId}`, request);
  },

  // Templates
  getWorkflowTemplates: (): Promise<{ templates: WorkflowTemplate[] }> => {
    return apiHelpers.get('/automation/templates');
  },

  // Statistics
  getAutomationStats: (projectId: string): Promise<AutomationStats> => {
    return apiHelpers.get('/automation/stats', {
      params: { project_id: projectId }
    });
  },

  // Utility functions
  getActionTypeLabel: (actionType: ActionType): string => {
    const labels: Record<ActionType, string> = {
      [ActionType.KEYWORD_RESEARCH]: 'Keyword Research',
      [ActionType.RANK_TRACKING]: 'Rank Tracking', 
      [ActionType.CONTENT_OPTIMIZATION]: 'Content Optimization',
      [ActionType.TECHNICAL_AUDIT]: 'Technical Audit',
      [ActionType.BACKLINK_ANALYSIS]: 'Backlink Analysis',
      [ActionType.COMPETITOR_ANALYSIS]: 'Competitor Analysis',
      [ActionType.SERP_ANALYSIS]: 'SERP Analysis',
      [ActionType.BULK_KEYWORD_UPDATE]: 'Bulk Keyword Update',
      [ActionType.REPORT_GENERATION]: 'Report Generation',
      [ActionType.EMAIL_NOTIFICATION]: 'Email Notification',
    };
    return labels[actionType] || actionType;
  },

  getStatusColor: (status: WorkflowStatus): 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning' => {
    const colors: Record<WorkflowStatus, 'default' | 'primary' | 'secondary' | 'error' | 'info' | 'success' | 'warning'> = {
      [WorkflowStatus.PENDING]: 'default',
      [WorkflowStatus.RUNNING]: 'primary',
      [WorkflowStatus.COMPLETED]: 'success',
      [WorkflowStatus.FAILED]: 'error',
      [WorkflowStatus.CANCELLED]: 'warning',
    };
    return colors[status] || 'default';
  },

  // Cron expression helpers
  parseCronExpression: (cron: string): string => {
    const cronPatterns: Record<string, string> = {
      '0 2 * * 1': 'Weekly on Monday at 2:00 AM',
      '0 6 * * *': 'Daily at 6:00 AM',
      '0 9 * * 1-5': 'Weekdays at 9:00 AM',
      '0 0 1 * *': 'Monthly on the 1st at midnight',
      '*/15 * * * *': 'Every 15 minutes',
      '0 */6 * * *': 'Every 6 hours',
    };
    return cronPatterns[cron] || 'Custom schedule';
  },

  validateCronExpression: (cron: string): boolean => {
    // Basic cron validation (5 fields: minute hour day month dayofweek)
    const cronRegex = /^(\*|(?:[0-9]|[1-5][0-9])) (\*|(?:[0-9]|1[0-9]|2[0-3])) (\*|(?:[0-9]|[12][0-9]|3[01])) (\*|(?:[0-9]|1[0-2])) (\*|(?:[0-6]))$/;
    return cronRegex.test(cron);
  },
};

export default automationService;