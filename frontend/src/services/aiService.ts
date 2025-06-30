import { apiHelpers } from './apiClient';

export enum ContentType {
  BLOG = "blog",
  PRODUCT = "product", 
  LANDING_PAGE = "landing_page",
  EMAIL = "email",
  SOCIAL = "social"
}

export enum ToneType {
  PROFESSIONAL = "professional",
  CASUAL = "casual",
  TECHNICAL = "technical",
  SALES = "sales"
}

export enum AnalysisType {
  SERP = "serp",
  COMPETITOR = "competitor",
  LAYOUT = "layout"
}

export interface VisionAnalysisRequest {
  image_url?: string;
  keyword?: string;
  analysis_type: AnalysisType;
}

export interface VisionAnalysisResponse {
  keyword?: string;
  url?: string;
  analysis: Record<string, any>;
  timestamp: string;
}

export interface ContentGenerationRequest {
  content_type: ContentType;
  topic: string;
  keywords: string[];
  tone: ToneType;
  length: number;
  additional_instructions?: string;
}

export interface ContentGenerationResponse {
  content: string;
  meta_title?: string;
  meta_description?: string;
  word_count: number;
  reading_time: number;
  seo_score: number;
}

export interface BulkContentItem {
  topic: string;
  keywords: string[];
  custom_fields: Record<string, any>;
}

export interface ContentTemplate {
  name: string;
  content_type: string;
  structure: Record<string, any>;
  variables: string[];
}

export interface BulkContentRequest {
  items: BulkContentItem[];
  template?: ContentTemplate;
  content_type: string;
  tone: string;
}

export interface VoiceOptimizationRequest {
  content: string;
  target_queries: string[];
  location?: string;
  language: string;
}

export interface VoiceOptimizationResponse {
  optimized_content: string;
  voice_snippets: string[];
  faq_schema: Record<string, any>;
  natural_language_variations: string[];
  optimization_score: number;
}

export interface ChatMessage {
  message: string;
  context?: Record<string, any>;
  session_id?: string;
}

export interface ChatResponse {
  response: string;
  suggestions: string[];
  relevant_data: Record<string, any>;
  session_id: string;
}

export interface ChatSession {
  id: string;
  created_at: string;
  last_message?: string;
  message_count: number;
}

export interface SessionMessage {
  role: 'user' | 'assistant';
  content: string;
  created_at: string;
}

export interface SEOAnalysisRequest {
  url: string;
  keywords: string[];
  competitors?: string[];
}

export interface SEOAnalysisResponse {
  url: string;
  seo_score: number;
  technical_issues: Record<string, any>[];
  content_analysis: Record<string, any>;
  competitor_comparison: Record<string, any>;
  recommendations: string[];
}

export interface ContentOptimizationRequest {
  content: string;
  target_keywords: string[];
  content_type: string;
}

export interface ContentOptimizationResponse {
  optimized_content: string;
  keyword_density: Record<string, number>;
  readability_score: number;
  suggested_headings: string[];
  internal_linking_suggestions: Record<string, string>[];
  optimization_tips: string[];
}

export const aiService = {
  // Vision Analysis
  analyzeSerpScreenshot: (file: File, keyword?: string): Promise<VisionAnalysisResponse> => {
    const formData = new FormData();
    formData.append('file', file);
    if (keyword) formData.append('keyword', keyword);
    
    return apiHelpers.post('/ai-services/vision/analyze-serp', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  analyzeCompetitorPage: (url: string, screenshot?: File): Promise<VisionAnalysisResponse> => {
    const formData = new FormData();
    formData.append('url', url);
    if (screenshot) formData.append('screenshot', screenshot);
    
    return apiHelpers.post('/ai-services/vision/analyze-competitor', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
  },

  // Content Generation
  generateContent: (request: ContentGenerationRequest): Promise<ContentGenerationResponse> => {
    return apiHelpers.post('/ai-services/content/generate', request);
  },

  bulkGenerateContent: (request: BulkContentRequest): Promise<{
    job_id: string;
    status: string;
    total_items: number;
    message: string;
  }> => {
    return apiHelpers.post('/ai-services/content/bulk-generate', request);
  },

  // Voice Search Optimization
  optimizeForVoiceSearch: (request: VoiceOptimizationRequest): Promise<VoiceOptimizationResponse> => {
    return apiHelpers.post('/ai-services/voice/optimize', request);
  },

  // Chat
  sendChatMessage: (message: ChatMessage): Promise<ChatResponse> => {
    return apiHelpers.post('/ai-services/chat/message', message);
  },

  getChatSessions: (): Promise<{ sessions: ChatSession[] }> => {
    return apiHelpers.get('/ai-services/chat/sessions');
  },

  getSessionMessages: (sessionId: string): Promise<{
    session_id: string;
    messages: SessionMessage[];
  }> => {
    return apiHelpers.get(`/ai-services/chat/session/${sessionId}/messages`);
  },

  // Templates
  getContentTemplates: (): Promise<{ templates: ContentTemplate[] }> => {
    return apiHelpers.get('/ai-services/templates');
  },

  createContentTemplate: (template: ContentTemplate): Promise<{
    id: string;
    message: string;
  }> => {
    return apiHelpers.post('/ai-services/templates', template);
  },

  // SEO Analysis
  analyzeSEO: (request: SEOAnalysisRequest): Promise<SEOAnalysisResponse> => {
    return apiHelpers.post('/ai-services/seo/analyze', request);
  },

  // Content Optimization
  optimizeContent: (request: ContentOptimizationRequest): Promise<ContentOptimizationResponse> => {
    return apiHelpers.post('/ai-services/content/optimize', request);
  },

  // Utility functions
  getContentTypeLabel: (contentType: ContentType): string => {
    const labels: Record<ContentType, string> = {
      [ContentType.BLOG]: 'Blog Post',
      [ContentType.PRODUCT]: 'Product Description',
      [ContentType.LANDING_PAGE]: 'Landing Page',
      [ContentType.EMAIL]: 'Email',
      [ContentType.SOCIAL]: 'Social Media Post',
    };
    return labels[contentType] || contentType;
  },

  getToneLabel: (tone: ToneType): string => {
    const labels: Record<ToneType, string> = {
      [ToneType.PROFESSIONAL]: 'Professional',
      [ToneType.CASUAL]: 'Casual',
      [ToneType.TECHNICAL]: 'Technical',
      [ToneType.SALES]: 'Sales',
    };
    return labels[tone] || tone;
  },

  calculateReadingTime: (wordCount: number): number => {
    // Average reading speed is 200-250 words per minute
    return Math.ceil(wordCount / 225);
  },

  getSEOScoreColor: (score: number): 'error' | 'warning' | 'info' | 'success' => {
    if (score >= 80) return 'success';
    if (score >= 60) return 'info';
    if (score >= 40) return 'warning';
    return 'error';
  },

  getReadabilityGrade: (score: number): string => {
    if (score >= 90) return 'Very Easy';
    if (score >= 80) return 'Easy';
    if (score >= 70) return 'Fairly Easy';
    if (score >= 60) return 'Standard';
    if (score >= 50) return 'Fairly Difficult';
    if (score >= 30) return 'Difficult';
    return 'Very Difficult';
  },
};

export default aiService;