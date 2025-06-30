import { apiHelpers } from './apiClient';

export interface TrafficMetrics {
  date: string;
  organic_traffic: number;
  organic_clicks: number;
  impressions: number;
  ctr: number;
  avg_position: number;
}

export interface KeywordPerformance {
  keyword: string;
  current_position: number;
  previous_position?: number;
  position_change: number;
  search_volume: number;
  estimated_traffic: number;
  difficulty: number;
}

export interface CompetitorAnalysis {
  domain: string;
  total_keywords: number;
  top_10_keywords: number;
  estimated_traffic: number;
  common_keywords: number;
  avg_position: number;
}

export interface ConversionMetrics {
  date: string;
  sessions: number;
  conversions: number;
  conversion_rate: number;
  goal_completions: number;
  revenue: number;
}

export interface AnalyticsOverview {
  total_keywords: number;
  avg_position: number;
  organic_traffic: number;
  top_10_count: number;
  visibility_score: number;
  traffic_change: number;
  position_change: number;
  keyword_opportunities: number;
}

export interface DetailedReport {
  project_id: string;
  date_range: string;
  overview: AnalyticsOverview;
  traffic_metrics: TrafficMetrics[];
  keyword_performance: KeywordPerformance[];
  competitor_analysis: CompetitorAnalysis[];
  conversion_metrics: ConversionMetrics[];
}

export const analyticsService = {
  // Get analytics overview
  getOverview: (projectId: string, days: number = 30): Promise<AnalyticsOverview> => {
    return apiHelpers.get('/analytics/overview', {
      params: { project_id: projectId, days }
    });
  },

  // Get traffic analytics
  getTrafficAnalytics: (projectId: string, days: number = 30): Promise<TrafficMetrics[]> => {
    return apiHelpers.get('/analytics/traffic', {
      params: { project_id: projectId, days }
    });
  },

  // Get keyword performance
  getKeywordPerformance: (
    projectId: string,
    limit: number = 50,
    orderBy: string = 'position_change'
  ): Promise<KeywordPerformance[]> => {
    return apiHelpers.get('/analytics/keywords/performance', {
      params: { project_id: projectId, limit, order_by: orderBy }
    });
  },

  // Get competitor analysis
  getCompetitorAnalysis: (projectId: string): Promise<CompetitorAnalysis[]> => {
    return apiHelpers.get('/analytics/competitors', {
      params: { project_id: projectId }
    });
  },

  // Get conversion analytics
  getConversionAnalytics: (projectId: string, days: number = 30): Promise<ConversionMetrics[]> => {
    return apiHelpers.get('/analytics/conversions', {
      params: { project_id: projectId, days }
    });
  },

  // Get detailed report
  getDetailedReport: (projectId: string, days: number = 30): Promise<DetailedReport> => {
    return apiHelpers.get('/analytics/report', {
      params: { project_id: projectId, days }
    });
  },

  // Refresh analytics data
  refreshData: (projectId: string): Promise<{ message: string }> => {
    return apiHelpers.post('/analytics/refresh', {}, {
      params: { project_id: projectId }
    });
  },
};

export default analyticsService;