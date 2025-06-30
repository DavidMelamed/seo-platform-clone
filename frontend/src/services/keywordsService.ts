import { apiHelpers } from './apiClient';

export interface Keyword {
  id: string;
  keyword: string;
  search_volume?: number;
  difficulty?: number;
  cpc?: number;
  current_position?: number;
  target_position?: number;
  priority: string;
  tags: string[];
  created_at: string;
  updated_at: string;
}

export interface KeywordCreate {
  keyword: string;
  project_id: string;
  target_position?: number;
  priority?: string;
  tags?: string[];
}

export interface KeywordUpdate {
  target_position?: number;
  priority?: string;
  tags?: string[];
}

export interface KeywordAnalysis {
  keyword: string;
  search_volume: number;
  difficulty: number;
  cpc: number;
  competition: number;
  trends: Record<string, any>;
  suggestions: string[];
}

export interface Ranking {
  id: string;
  position: number;
  url: string;
  title: string;
  recorded_at: string;
  serp_features: string[];
}

export interface BulkKeywordRequest {
  keywords: string[];
  project_id: string;
}

export interface BulkKeywordResponse {
  message: string;
  added: number;
  skipped: number;
  total: number;
}

export const keywordsService = {
  // Get keywords for a project
  getKeywords: (
    projectId: string,
    skip: number = 0,
    limit: number = 100,
    search?: string,
    priority?: string
  ): Promise<Keyword[]> => {
    const params: any = { project_id: projectId, skip, limit };
    if (search) params.search = search;
    if (priority) params.priority = priority;
    
    return apiHelpers.get('/keywords/', { params });
  },

  // Get a specific keyword
  getKeyword: (keywordId: string): Promise<Keyword> => {
    return apiHelpers.get(`/keywords/${keywordId}`);
  },

  // Create a new keyword
  createKeyword: (keywordData: KeywordCreate): Promise<Keyword> => {
    return apiHelpers.post('/keywords/', keywordData);
  },

  // Update a keyword
  updateKeyword: (keywordId: string, keywordData: KeywordUpdate): Promise<Keyword> => {
    return apiHelpers.put(`/keywords/${keywordId}`, keywordData);
  },

  // Delete a keyword
  deleteKeyword: (keywordId: string): Promise<{ message: string }> => {
    return apiHelpers.delete(`/keywords/${keywordId}`);
  },

  // Analyze a keyword before adding it
  analyzeKeyword: (keyword: string): Promise<KeywordAnalysis> => {
    return apiHelpers.post('/keywords/analyze', { keyword });
  },

  // Bulk add keywords
  bulkAddKeywords: (request: BulkKeywordRequest): Promise<BulkKeywordResponse> => {
    return apiHelpers.post('/keywords/bulk', request);
  },

  // Get ranking history for a keyword
  getKeywordRankings: (keywordId: string, days: number = 30): Promise<Ranking[]> => {
    return apiHelpers.get(`/keywords/${keywordId}/rankings`, {
      params: { days }
    });
  },

  // Predict keyword ranking
  predictKeywordRanking: (keywordId: string, daysAhead: number = 90): Promise<any> => {
    return apiHelpers.post(`/keywords/${keywordId}/predict`, {
      params: { days_ahead: daysAhead }
    });
  },
};

export default keywordsService;