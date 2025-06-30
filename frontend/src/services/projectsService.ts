import { apiHelpers } from './apiClient';

export interface ProjectStats {
  keywords_count: number;
  avg_position: number;
  top_10_count: number;
  total_rankings: number;
  last_updated?: string;
}

export interface Project {
  id: string;
  name: string;
  domain: string;
  description?: string;
  settings: Record<string, any>;
  is_active: boolean;
  created_at: string;
  updated_at: string;
  stats?: ProjectStats;
}

export interface ProjectCreate {
  name: string;
  domain: string;
  description?: string;
  settings?: Record<string, any>;
}

export interface ProjectUpdate {
  name?: string;
  domain?: string;
  description?: string;
  settings?: Record<string, any>;
  is_active?: boolean;
}

export interface DomainAnalysis {
  domain: string;
  is_accessible: boolean;
  has_ssl: boolean;
  page_title?: string;
  meta_description?: string;
  status_code?: number;
  response_time_ms?: number;
}

export const projectsService = {
  // Get all projects
  getProjects: (includeStats: boolean = true, skip: number = 0, limit: number = 100): Promise<Project[]> => {
    return apiHelpers.get('/projects/', {
      params: { include_stats: includeStats, skip, limit }
    });
  },

  // Get a specific project
  getProject: (projectId: string, includeStats: boolean = true): Promise<Project> => {
    return apiHelpers.get(`/projects/${projectId}`, {
      params: { include_stats: includeStats }
    });
  },

  // Create a new project
  createProject: (projectData: ProjectCreate): Promise<Project> => {
    return apiHelpers.post('/projects/', projectData);
  },

  // Update a project
  updateProject: (projectId: string, projectData: ProjectUpdate): Promise<Project> => {
    return apiHelpers.put(`/projects/${projectId}`, projectData);
  },

  // Delete a project
  deleteProject: (projectId: string): Promise<{ message: string }> => {
    return apiHelpers.delete(`/projects/${projectId}`);
  },

  // Analyze project domain
  analyzeDomain: (projectId: string): Promise<DomainAnalysis> => {
    return apiHelpers.post(`/projects/${projectId}/analyze`);
  },
};

export default projectsService;