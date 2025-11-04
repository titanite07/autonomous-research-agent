-- Autonomous Research Agent - PostgreSQL Database Schema
-- Version: 1.0.0
-- Date: 2025-11-04

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Users Table
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    username VARCHAR(100) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255),
    avatar_url TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMP WITH TIME ZONE
);

-- Create index on email for faster lookups
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_username ON users(username);

-- Research Jobs Table (persistent storage instead of in-memory)
CREATE TABLE IF NOT EXISTS research_jobs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    query TEXT NOT NULL,
    status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    progress INTEGER DEFAULT 0,
    total_papers INTEGER DEFAULT 0,
    processing_time FLOAT,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    completed_at TIMESTAMP WITH TIME ZONE
);

CREATE INDEX idx_research_jobs_user_id ON research_jobs(user_id);
CREATE INDEX idx_research_jobs_status ON research_jobs(status);
CREATE INDEX idx_research_jobs_created_at ON research_jobs(created_at DESC);

-- Papers Table
CREATE TABLE IF NOT EXISTS papers (
    id VARCHAR(255) PRIMARY KEY, -- arXiv ID or DOI
    title TEXT NOT NULL,
    abstract TEXT,
    authors TEXT[], -- Array of author names
    year INTEGER,
    citations INTEGER DEFAULT 0,
    url TEXT,
    source VARCHAR(50), -- arxiv, semantic_scholar, springer
    doi VARCHAR(255),
    pdf_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_papers_year ON papers(year);
CREATE INDEX idx_papers_citations ON papers(citations DESC);
CREATE INDEX idx_papers_source ON papers(source);
CREATE INDEX idx_papers_title_gin ON papers USING gin(to_tsvector('english', title));
CREATE INDEX idx_papers_abstract_gin ON papers USING gin(to_tsvector('english', abstract));

-- Research Job Papers (many-to-many relationship)
CREATE TABLE IF NOT EXISTS research_job_papers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES research_jobs(id) ON DELETE CASCADE,
    paper_id VARCHAR(255) REFERENCES papers(id) ON DELETE CASCADE,
    relevance_score FLOAT,
    rank INTEGER,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(job_id, paper_id)
);

CREATE INDEX idx_research_job_papers_job_id ON research_job_papers(job_id);
CREATE INDEX idx_research_job_papers_paper_id ON research_job_papers(paper_id);
CREATE INDEX idx_research_job_papers_relevance ON research_job_papers(relevance_score DESC);

-- Saved Searches Table
CREATE TABLE IF NOT EXISTS saved_searches (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL,
    query TEXT NOT NULL,
    filters JSONB, -- Store advanced filters as JSON
    is_favorite BOOLEAN DEFAULT FALSE,
    search_count INTEGER DEFAULT 0,
    last_searched TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_saved_searches_user_id ON saved_searches(user_id);
CREATE INDEX idx_saved_searches_created_at ON saved_searches(created_at DESC);
CREATE INDEX idx_saved_searches_favorite ON saved_searches(user_id, is_favorite);

-- Saved Papers Table (Bookmarks)
CREATE TABLE IF NOT EXISTS saved_papers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    paper_id VARCHAR(255) REFERENCES papers(id) ON DELETE CASCADE,
    folder VARCHAR(255) DEFAULT 'default',
    notes TEXT,
    tags TEXT[],
    is_read BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, paper_id)
);

CREATE INDEX idx_saved_papers_user_id ON saved_papers(user_id);
CREATE INDEX idx_saved_papers_paper_id ON saved_papers(paper_id);
CREATE INDEX idx_saved_papers_folder ON saved_papers(user_id, folder);
CREATE INDEX idx_saved_papers_created_at ON saved_papers(created_at DESC);

-- Paper Summaries Table (AI-generated)
CREATE TABLE IF NOT EXISTS paper_summaries (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    paper_id VARCHAR(255) REFERENCES papers(id) ON DELETE CASCADE,
    summary TEXT NOT NULL,
    key_findings TEXT[],
    methodology TEXT,
    model_used VARCHAR(100), -- e.g., 'llama-3.1-8b-instant'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(paper_id)
);

CREATE INDEX idx_paper_summaries_paper_id ON paper_summaries(paper_id);

-- Analysis Results Table
CREATE TABLE IF NOT EXISTS analysis_results (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    job_id UUID REFERENCES research_jobs(id) ON DELETE CASCADE,
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    paper_ids TEXT[],
    synthesis TEXT,
    trends JSONB,
    recommendations TEXT[],
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_analysis_results_job_id ON analysis_results(job_id);
CREATE INDEX idx_analysis_results_user_id ON analysis_results(user_id);

-- Chat History Table (AI Chatbot conversations)
CREATE TABLE IF NOT EXISTS chat_history (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    session_id UUID NOT NULL,
    role VARCHAR(20) NOT NULL, -- 'user' or 'assistant'
    message TEXT NOT NULL,
    context JSONB, -- Store any additional context
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_chat_history_user_id ON chat_history(user_id);
CREATE INDEX idx_chat_history_session_id ON chat_history(session_id);
CREATE INDEX idx_chat_history_created_at ON chat_history(created_at DESC);

-- User Preferences Table
CREATE TABLE IF NOT EXISTS user_preferences (
    user_id UUID PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
    theme VARCHAR(20) DEFAULT 'dark', -- 'light' or 'dark'
    default_sources TEXT[] DEFAULT ARRAY['arxiv', 'semantic_scholar', 'springer'],
    notifications_enabled BOOLEAN DEFAULT TRUE,
    email_notifications BOOLEAN DEFAULT FALSE,
    search_history_enabled BOOLEAN DEFAULT TRUE,
    auto_save_searches BOOLEAN DEFAULT FALSE,
    preferences JSONB, -- Additional custom preferences
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- API Keys Table (for future Phase 3)
CREATE TABLE IF NOT EXISTS api_keys (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    key_hash VARCHAR(255) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    scopes TEXT[], -- permissions
    is_active BOOLEAN DEFAULT TRUE,
    last_used TIMESTAMP WITH TIME ZONE,
    expires_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_api_keys_user_id ON api_keys(user_id);
CREATE INDEX idx_api_keys_key_hash ON api_keys(key_hash);

-- Update timestamp trigger function
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Apply update trigger to relevant tables
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_research_jobs_updated_at BEFORE UPDATE ON research_jobs
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_papers_updated_at BEFORE UPDATE ON papers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_saved_searches_updated_at BEFORE UPDATE ON saved_searches
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_saved_papers_updated_at BEFORE UPDATE ON saved_papers
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_user_preferences_updated_at BEFORE UPDATE ON user_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- Create view for user statistics
CREATE OR REPLACE VIEW user_stats AS
SELECT 
    u.id as user_id,
    u.username,
    u.email,
    COUNT(DISTINCT rj.id) as total_searches,
    COUNT(DISTINCT sp.id) as saved_papers_count,
    COUNT(DISTINCT ss.id) as saved_searches_count,
    MAX(rj.created_at) as last_search_date,
    u.created_at as member_since
FROM users u
LEFT JOIN research_jobs rj ON u.id = rj.user_id
LEFT JOIN saved_papers sp ON u.id = sp.user_id
LEFT JOIN saved_searches ss ON u.id = ss.user_id
GROUP BY u.id, u.username, u.email, u.created_at;

-- Insert default admin user (password: admin123 - hashed with bcrypt)
-- NOTE: Change this password in production!
INSERT INTO users (email, username, password_hash, full_name, is_verified)
VALUES (
    'admin@research-agent.com',
    'admin',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5/P3xFqzRUKgG', -- admin123
    'System Administrator',
    TRUE
) ON CONFLICT (email) DO NOTHING;

COMMENT ON TABLE users IS 'Registered users of the research agent';
COMMENT ON TABLE research_jobs IS 'Research query jobs with their status and results';
COMMENT ON TABLE papers IS 'Academic papers from various sources';
COMMENT ON TABLE saved_searches IS 'User-saved search queries for quick access';
COMMENT ON TABLE saved_papers IS 'User bookmarked papers with notes and tags';
COMMENT ON TABLE paper_summaries IS 'AI-generated summaries of papers';
COMMENT ON TABLE analysis_results IS 'Results from multi-paper analysis';
