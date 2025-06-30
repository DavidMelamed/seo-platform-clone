import { apiHelpers } from './apiClient';

export interface DashboardMetrics {
  total_keywords: number;
  avg_position: number;
  top_ten_keywords: number;
  organic_traffic: number;
  keyword_changes: {
    improved: number;
    declined: number;
    new: number;
  };
  projects_count: number;
  alerts_count: number;
}

export interface TrafficDataset {
  label: string;
  data: number[];
  borderColor: string;
  backgroundColor: string;
  fill: boolean;
}

export interface TrafficData {
  labels: string[];
  datasets: TrafficDataset[];
}

export interface PositionDataset {
  data: number[];
  backgroundColor: string[];
}

export interface PositionData {
  labels: string[];
  datasets: PositionDataset[];
}

export interface RecentActivity {
  id: string;
  type: string;
  title: string;
  description: string;
  timestamp: string;
  status: string;
}

export interface DashboardData {
  metrics: DashboardMetrics;
  traffic_data: TrafficData;
  position_data: PositionData;
  recent_activities: RecentActivity[];
}

export const dashboardService = {
  // Get dashboard metrics
  getMetrics: (projectId?: string): Promise<DashboardMetrics> => {
    const params = projectId ? { project_id: projectId } : {};
    return apiHelpers.get('/dashboard/metrics', { params });
  },

  // Get traffic data for charts
  getTrafficData: (projectId?: string, days: number = 30): Promise<TrafficData> => {
    const params = { days, ...(projectId ? { project_id: projectId } : {}) };
    return apiHelpers.get('/dashboard/traffic-data', { params });
  },

  // Get position distribution data
  getPositionData: (projectId?: string): Promise<PositionData> => {
    const params = projectId ? { project_id: projectId } : {};
    return apiHelpers.get('/dashboard/position-data', { params });
  },

  // Get recent activities
  getRecentActivities: (limit: number = 10): Promise<RecentActivity[]> => {
    return apiHelpers.get('/dashboard/recent-activities', { params: { limit } });
  },

  // Get complete dashboard data in one request
  getCompleteDashboard: (projectId?: string): Promise<DashboardData> => {
    const params = projectId ? { project_id: projectId } : {};
    return apiHelpers.get('/dashboard/complete', { params });
  },
};

export default dashboardService;