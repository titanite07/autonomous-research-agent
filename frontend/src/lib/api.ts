import axios from 'axios';
import type { 
  SearchRequest, 
  SearchSubmissionResponse, 
  SearchResponse, 
  ResearchStatus, 
  ExportRequest, 
  Paper,
  SearchHistory,
  Report,
  AnalyticsData
} from '@/types';

// Backend result response type
interface BackendResultResponse {
  job_id: string;
  status: string;
  query: string;
  results: {
    query: string;
    total_papers: number;
    papers: Paper[];
    sources: string[];
    dedup_threshold: number;
  };
  created_at: string;
  completed_at: string;
}

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Create axios instance with default config
export const apiClient = axios.create({
  baseURL: API_BASE_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 300000, // 5 minutes (300 seconds) for long-running operations
});

// Add request interceptor for auth (if needed)
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('api_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// Add response interceptor for error handling
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      // Handle unauthorized
      localStorage.removeItem('api_token');
    }
    
    // Log timeout errors for debugging
    if (error.code === 'ECONNABORTED') {
      console.error('Request timeout:', error.config?.url);
      console.error('Timeout duration:', error.config?.timeout);
    }
    
    // Log network errors
    if (!error.response) {
      console.error('Network error:', error.message);
    }
    
    return Promise.reject(error);
  }
);

// API Methods
export const researchAPI = {
  // Submit a new search
  async search(request: SearchRequest): Promise<SearchSubmissionResponse> {
    const { data } = await apiClient.post<SearchSubmissionResponse>('/api/v1/search', request);
    return data;
  },

  // Get search status
  async getStatus(jobId: string): Promise<ResearchStatus> {
    const { data } = await apiClient.get<ResearchStatus>(`/api/v1/status/${jobId}`);
    return data;
  },

  // Get search results
  async getResults(jobId: string): Promise<SearchResponse> {
    const { data } = await apiClient.get<BackendResultResponse>(`/api/v1/results/${jobId}`);
    // Backend returns { job_id, status, query, results: {...}, created_at, completed_at }
    // We need to extract the results object and add processing_time
    const processingTime = data.completed_at && data.created_at
      ? (new Date(data.completed_at).getTime() - new Date(data.created_at).getTime()) / 1000
      : 0;
    
    return {
      job_id: data.job_id,
      status: data.status as 'pending' | 'processing' | 'completed' | 'failed',
      query: data.results.query || data.query,
      papers: data.results.papers || [],
      total_papers: data.results.total_papers || 0,
      processing_time: processingTime,
    };
  },

  // Delete results
  async deleteResults(jobId: string): Promise<void> {
    await apiClient.delete(`/api/v1/results/${jobId}`);
  },

  // Request deep analysis on selected papers
  async analyze(request: { 
    paper_ids: number[]; 
    include_citations?: boolean; 
    include_knowledge_graph?: boolean;
    job_id?: string;
  }): Promise<{ 
    job_id: string; 
    search_id: number;
    total_papers: number;
    status: string;
    summaries?: Record<string, unknown>[];
    synthesis?: Record<string, unknown>;
    citations_data?: Record<string, unknown>;
    knowledge_graph?: Record<string, unknown>;
  }> {
    const { data } = await apiClient.post('/api/v1/analyze', {
      paper_ids: request.paper_ids,
      include_citations: request.include_citations ?? true,
      include_knowledge_graph: request.include_knowledge_graph ?? true,
      job_id: request.job_id,
    });
    return data;
  },

  // Export report in various formats
  async exportReport(request: ExportRequest): Promise<{
    job_id: string;
    report_id: number;
    format: string;
    content: string;
    title: string;
    metadata?: {
      word_count: number;
      paper_count: number;
      citation_style?: string;
      created_at?: string;
    };
  }> {
    const { data } = await apiClient.get(
      `/api/v1/export/${request.job_id}/${request.format}`
    );
    return data;
  },

  // Generate a new report using ResearchService (with WebSocket support)
  async generateReportWithWebSocket(request: {
    job_id: string;
    format?: string;
  }): Promise<{
    job_id: string;
    status: string;
    format: string;
    content: string;
  }> {
    const { data } = await apiClient.post('/api/v1/report', {
      job_id: request.job_id,
      format: request.format || 'markdown',
    });
    return data;
  },

  // Health check
  async healthCheck(): Promise<{ status: string; service: string }> {
    const { data } = await apiClient.get('/api/v1/health');
    return data;
  },

  // Get search history
  async getHistory(limit: number = 50, status?: string): Promise<{ items: SearchHistory[]; total: number }> {
    const { data } = await apiClient.get('/api/v1/history', {
      params: { limit, status }
    });
    return data;
  },

  // Get analytics
  async getAnalytics(): Promise<AnalyticsData> {
    const { data } = await apiClient.get('/api/v1/analytics');
    return data;
  },

  // Get analytics summary
  async getAnalyticsSummary(): Promise<{ total_searches: number; total_papers: number; avg_relevance: number }> {
    const { data } = await apiClient.get('/api/v1/analytics/summary');
    return data;
  },

  // Get reports
  async getReports(limit: number = 50, reportType?: string): Promise<{ reports: Report[]; total: number }> {
    const { data } = await apiClient.get('/api/v1/reports', {
      params: { limit, report_type: reportType }
    });
    return data;
  },

  // Get specific report
  async getReport(reportId: number): Promise<Report> {
    const { data } = await apiClient.get(`/api/v1/report/${reportId}`);
    return data;
  },

  // Generate report from search (legacy endpoint - uses ReportGenerator)
  async generateReport(request: { 
    job_id: string; 
    citation_style?: string;
    format?: string;
  }): Promise<{ 
    message: string;
    report_id: number;
    report: Report;
  }> {
    const { data } = await apiClient.post(`/api/v1/reports/generate/${request.job_id}`, {
      citation_style: request.citation_style || 'APA',
      format: request.format || 'markdown',
    });
    return data;
  },

  // Delete history item
  async deleteHistory(jobId: string): Promise<void> {
    await apiClient.delete(`/api/v1/history/${jobId}`);
  },

  // Delete report
  async deleteReport(reportId: number): Promise<void> {
    await apiClient.delete(`/api/v1/report/${reportId}`);
  },

  // Get citation network data
  async getCitationNetwork(jobId: string): Promise<{
    job_id: string;
    papers: Array<{
      id: string;
      title: string;
      authors: string[];
      citations: number;
      year: number;
      url: string;
      abstract?: string;
      relevance_score?: number;
      source?: string;
    }>;
    links: Array<{
      source: string;
      target: string;
      weight: number;
    }>;
    stats: {
      total_papers: number;
      total_connections: number;
      total_citations: number;
      avg_citations: number;
    };
  }> {
    const { data } = await apiClient.get(`/api/v1/network/${jobId}`);
    return data;
  },
};

// WebSocket connection helper
export class ResearchWebSocket {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 2000;

  constructor(
    private jobId: string,
    private onMessage: (event: { type: string; message?: string; [key: string]: unknown }) => void,
    private onError?: (error: Event) => void,
    private onClose?: () => void
  ) {}

  connect(): void {
    const wsUrl = `${API_BASE_URL.replace('http', 'ws')}/ws/research/${this.jobId}`;
    
    try {
      this.ws = new WebSocket(wsUrl);

      this.ws.onopen = () => {
        console.log('✅ WebSocket connected - Real-time updates enabled');
        this.reconnectAttempts = 0;
      };

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data) as { type: string; message?: string; [key: string]: unknown };
          this.onMessage(data);
        } catch {
          // Silently ignore parse errors
        }
      };

      this.ws.onerror = () => {
        // Silently ignore - backend may not be running
        // HTTP polling will handle updates
        this.onError?.(new Event('error'));
      };

      this.ws.onclose = () => {
        // Silently close - no reconnection needed
        this.onClose?.();
      };
    } catch (error) {
      // Silently ignore - backend may not be running
      this.onError?.(error as Event);
    }
  }

  private attemptReconnect(): void {
    // Disabled - HTTP polling handles all updates
  }

  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
  }

  send(data: Record<string, unknown>): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    }
  }
}

export default researchAPI;
