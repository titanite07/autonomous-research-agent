// Search Request Types
export interface SearchRequest {
  query: string;
  max_results?: number;
  sources?: string[];
  dedup_threshold?: number;
  full_text?: boolean;
}

// Search Submission Response (from POST /search)
export interface SearchSubmissionResponse {
  job_id: string;
  status: string;
  message: string;
  estimated_time?: string;
}

// Paper Types
export interface Paper {
  id: string;
  title: string;
  authors: string[];
  abstract: string;
  year: number;
  url: string;
  citations: number;
  relevance_score: number;
  source: string;
  pdf_url?: string;
}

// Search Response Types
export interface SearchResponse {
  job_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  query: string;
  papers: Paper[];
  total_papers: number;
  processing_time?: number;
  error?: string;
}

// Agent Status Types
export interface AgentStatus {
  agent_name: string;
  status: 'idle' | 'working' | 'completed' | 'error';
  current_task?: string;
  progress?: number;
  tokens_used?: number;
  last_update?: string;
}

// Research Status Types
export interface ResearchStatus {
  job_id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  agents: AgentStatus[];
  current_phase?: string;
  estimated_time_remaining?: number;
  message?: string;
}

// Analysis Types
export interface AnalysisRequest {
  job_id: string;
  focus_areas?: string[];
}

export interface AnalysisResponse {
  analysis_id: string;
  status: string;
  insights: {
    key_findings: string[];
    research_gaps: string[];
    future_directions: string[];
    methodology_summary: string;
  };
}

// Export Types
export interface ExportRequest {
  job_id: string;
  format: 'pdf' | 'docx' | 'latex' | 'markdown';
  include_citations?: boolean;
  include_graphs?: boolean;
}

// WebSocket Event Types
export type WebSocketEvent =
  | { type: 'search_started'; query: string }
  | { type: 'papers_found'; count: number; source: string }
  | { type: 'agent_working'; agent: string; task: string; progress: number }
  | { type: 'synthesis_complete'; summary: string }
  | { type: 'report_ready'; job_id: string }
  | { type: 'error'; message: string };

// UI State Types
export interface SearchFilters {
  sources: string[];
  yearRange: [number, number];
  minCitations: number;
  dedupThreshold: number;
}

export interface DashboardMetrics {
  total_searches: number;
  total_papers: number;
  avg_relevance: number;
  processing_time: number;
  active_agents: number;
}

// Citation Network Types
export interface CitationNode {
  id: string;
  title: string;
  year: number;
  citations: number;
  relevance: number;
}

export interface CitationEdge {
  source: string;
  target: string;
  weight: number;
}

export interface CitationNetwork {
  nodes: CitationNode[];
  edges: CitationEdge[];
}

// Knowledge Graph Types
export interface KnowledgeGraphNode {
  id: string;
  label: string;
  type: 'paper' | 'author' | 'topic' | 'method' | 'dataset';
  properties: Record<string, unknown>;
}

export interface KnowledgeGraphEdge {
  source: string;
  target: string;
  relation: string;
  weight: number;
}

export interface KnowledgeGraph {
  nodes: KnowledgeGraphNode[];
  edges: KnowledgeGraphEdge[];
}

// Additional Types for API responses

export interface SearchHistory {
  id: string;
  job_id: string;
  query: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  results_count: number;
  created_at: string;
  completed_at?: string;
  avg_relevance?: number;
  sources?: string[];
  max_results?: number;
}

export interface Report {
  id: string;
  job_id: string;
  title?: string;
  type?: string;
  query?: string;
  report_type?: string;
  content?: string;
  created_at: string;
  paper_count?: number;
  sources?: string[];
  size?: string;
  format?: string;
  status?: 'completed' | 'processing' | 'failed';
  summary?: string;
}

export interface AnalyticsData {
  stats: {
    total_searches: number;
    total_papers: number;
    avg_relevance: number;
    total_reports: number;
    searches_growth?: number;
    papers_growth?: number;
    relevance_growth?: number;
    active_days?: number;
  };
  papers_by_source: Array<{ source: string; count: number }>;
  searches_by_week: Array<{ week: string; count: number }>;
  top_queries: Array<{ query: string; count: number }>;
  relevance_distribution: Array<{ range: string; count: number }>;
  charts?: Record<string, unknown>;
}
