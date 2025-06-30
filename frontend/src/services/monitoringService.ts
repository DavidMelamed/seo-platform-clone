import { apiHelpers } from './apiClient';

export enum AlertType {
  RANKING_DROP = "ranking_drop",
  RANKING_IMPROVEMENT = "ranking_improvement", 
  KEYWORD_LOST = "keyword_lost",
  KEYWORD_GAINED = "keyword_gained",
  TRAFFIC_DROP = "traffic_drop",
  TRAFFIC_SPIKE = "traffic_spike",
  COMPETITOR_CHANGE = "competitor_change",
  TECHNICAL_ISSUE = "technical_issue"
}

export enum AlertSeverity {
  LOW = "low",
  MEDIUM = "medium",
  HIGH = "high",
  CRITICAL = "critical"
}

export enum NotificationStatus {
  UNREAD = "unread",
  READ = "read",
  ARCHIVED = "archived"
}

export interface Alert {
  id: string;
  name: string;
  project_id: string;
  alert_type: AlertType;
  threshold_value: number;
  comparison_operator: string;
  severity: AlertSeverity;
  is_active: boolean;
  email_notifications: boolean;
  slack_notifications: boolean;
  webhook_url?: string;
  last_triggered_at?: string;
  created_at: string;
  updated_at: string;
}

export interface AlertCreate {
  name: string;
  project_id: string;
  alert_type: AlertType;
  threshold_value: number;
  comparison_operator: string;
  is_active?: boolean;
  email_notifications?: boolean;
  slack_notifications?: boolean;
  webhook_url?: string;
}

export interface AlertUpdate {
  name?: string;
  threshold_value?: number;
  comparison_operator?: string;
  is_active?: boolean;
  email_notifications?: boolean;
  slack_notifications?: boolean;
  webhook_url?: string;
}

export interface Notification {
  id: string;
  alert_id: string;
  project_id: string;
  title: string;
  message: string;
  severity: AlertSeverity;
  status: NotificationStatus;
  metadata: Record<string, any>;
  created_at: string;
}

export interface MonitoringOverview {
  total_alerts: number;
  active_alerts: number;
  triggered_today: number;
  unread_notifications: number;
  system_health: string;
  uptime_percentage: number;
}

export interface SystemHealth {
  status: string;
  response_time: number;
  database_status: string;
  redis_status: string;
  dataforseo_status: string;
  last_check: string;
}

export interface RealTimeUpdate {
  type: string;
  data: Record<string, any>;
  timestamp: string;
}

export const monitoringService = {
  // Get monitoring overview
  getOverview: (projectId: string): Promise<MonitoringOverview> => {
    return apiHelpers.get('/monitoring/overview', {
      params: { project_id: projectId }
    });
  },

  // Alert management
  createAlert: (alertData: AlertCreate): Promise<Alert> => {
    return apiHelpers.post('/monitoring/alerts', alertData);
  },

  getAlerts: (
    projectId: string,
    skip: number = 0,
    limit: number = 100
  ): Promise<Alert[]> => {
    return apiHelpers.get('/monitoring/alerts', {
      params: { project_id: projectId, skip, limit }
    });
  },

  updateAlert: (alertId: string, alertData: AlertUpdate): Promise<Alert> => {
    return apiHelpers.put(`/monitoring/alerts/${alertId}`, alertData);
  },

  deleteAlert: (alertId: string): Promise<{ message: string }> => {
    return apiHelpers.delete(`/monitoring/alerts/${alertId}`);
  },

  // Notification management
  getNotifications: (
    projectId: string,
    status?: NotificationStatus,
    skip: number = 0,
    limit: number = 50
  ): Promise<Notification[]> => {
    const params: any = { project_id: projectId, skip, limit };
    if (status) params.status = status;
    
    return apiHelpers.get('/monitoring/notifications', { params });
  },

  updateNotificationStatus: (
    notificationId: string,
    status: NotificationStatus
  ): Promise<{ message: string }> => {
    return apiHelpers.put(`/monitoring/notifications/${notificationId}/status`, null, {
      params: { status }
    });
  },

  // System health
  getSystemHealth: (): Promise<SystemHealth> => {
    return apiHelpers.get('/monitoring/health');
  },

  // Manual alert checking
  triggerAlertCheck: (projectId: string): Promise<{ message: string }> => {
    return apiHelpers.post('/monitoring/check-alerts', null, {
      params: { project_id: projectId }
    });
  },

  // WebSocket connection
  connectWebSocket: (userId: string, onMessage: (data: RealTimeUpdate) => void): WebSocket => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/api/monitoring/ws/${userId}`;
    
    const ws = new WebSocket(wsUrl);
    
    ws.onopen = () => {
      console.log('Monitoring WebSocket connected');
    };
    
    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        onMessage(data);
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };
    
    ws.onclose = () => {
      console.log('Monitoring WebSocket disconnected');
    };
    
    ws.onerror = (error) => {
      console.error('Monitoring WebSocket error:', error);
    };
    
    return ws;
  },

  // Utility functions
  getAlertTypeLabel: (alertType: AlertType): string => {
    const labels: Record<AlertType, string> = {
      [AlertType.RANKING_DROP]: 'Ranking Drop',
      [AlertType.RANKING_IMPROVEMENT]: 'Ranking Improvement',
      [AlertType.KEYWORD_LOST]: 'Keyword Lost',
      [AlertType.KEYWORD_GAINED]: 'Keyword Gained',
      [AlertType.TRAFFIC_DROP]: 'Traffic Drop',
      [AlertType.TRAFFIC_SPIKE]: 'Traffic Spike',
      [AlertType.COMPETITOR_CHANGE]: 'Competitor Change',
      [AlertType.TECHNICAL_ISSUE]: 'Technical Issue',
    };
    return labels[alertType] || alertType;
  },

  getSeverityColor: (severity: AlertSeverity): 'error' | 'warning' | 'info' | 'success' => {
    const colors: Record<AlertSeverity, 'error' | 'warning' | 'info' | 'success'> = {
      [AlertSeverity.CRITICAL]: 'error',
      [AlertSeverity.HIGH]: 'error',
      [AlertSeverity.MEDIUM]: 'warning',
      [AlertSeverity.LOW]: 'info',
    };
    return colors[severity] || 'info';
  },
};

export default monitoringService;