'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import { Search, Zap, Network, BarChart3, FileText, History } from 'lucide-react';
import { researchAPI } from '@/lib/api';
import type { SearchRequest } from '@/types';
import { ThemeToggle } from '@/components/ThemeToggle';
import { AIChatbot } from '@/components/AIChatbot';

export default function HomePage() {
  const router = useRouter();
  const [query, setQuery] = useState('');
  const [maxResults, setMaxResults] = useState(10);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSearch = async () => {
    if (!query.trim()) {
      setError('Please enter a research query');
      return;
    }

    if (maxResults < 1) {
      setError('Please enter a valid number of papers');
      return;
    }

    setIsLoading(true);
    setError('');

    try {
      const request: SearchRequest = {
        query: query.trim(),
        max_results: maxResults,
        sources: undefined,  // Let backend auto-detect available sources (includes Springer if API key present)
        dedup_threshold: 0.85,
        full_text: true,
      };

      const response = await researchAPI.search(request);
      
      // Redirect to results page
      router.push(`/results?job_id=${response.job_id}`);
    } catch (err: unknown) {
      console.error('Search error:', err);
      
      // Handle different error types
      let errorMessage = 'Failed to start research. Please try again.';
      
      const error = err as { response?: { data?: { detail?: string | object; message?: string } }; message?: string };
      
      if (error.response?.data) {
        // If detail is an object, stringify it
        if (typeof error.response.data.detail === 'object') {
          errorMessage = JSON.stringify(error.response.data.detail, null, 2);
        } else if (typeof error.response.data.detail === 'string') {
          errorMessage = error.response.data.detail;
        } else if (error.response.data.message) {
          errorMessage = error.response.data.message;
        }
      } else if (error.message) {
        errorMessage = error.message;
      }
      
      setError(errorMessage);
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-white dark:bg-black text-gray-900 dark:text-green-400 font-mono transition-colors">
      {/* CLI Header */}
      <header className="border-b border-gray-300 dark:border-green-500 bg-white dark:bg-black transition-colors">
        <div className="container mx-auto px-4 py-4">
          <div className="space-y-2">
            {/* ASCII Banner */}
            <pre className="text-blue-600 dark:text-green-500 text-xs leading-tight">
{`╔═══════════════════════════════════════════════════════════════════╗
║  █████╗ ██╗   ██╗████████╗ ██████╗  ██████╗ ███████╗███╗   ██╗  ║
║ ██╔══██╗██║   ██║╚══██╔══╝██╔═══██╗██╔════╝ ██╔════╝████╗  ██║  ║
║ ███████║██║   ██║   ██║   ██║   ██║██║  ███╗█████╗  ██╔██╗ ██║  ║
║ ██╔══██║██║   ██║   ██║   ██║   ██║██║   ██║██╔══╝  ██║╚██╗██║  ║
║ ██║  ██║╚██████╔╝   ██║   ╚██████╔╝╚██████╔╝███████╗██║ ╚████║  ║
║ ╚═╝  ╚═╝ ╚═════╝    ╚═╝    ╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═══╝  ║
╚═══════════════════════════════════════════════════════════════════╝`}
            </pre>
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <span className="text-blue-600 dark:text-green-500">$</span>
                <span className="text-blue-700 dark:text-cyan-400">research-agent</span>
                <span className="text-gray-600 dark:text-gray-500">v1.0.0</span>
                <span className="text-gray-400 dark:text-gray-600">|</span>
                <span className="text-orange-600 dark:text-yellow-400">Multi-Agent AI Research Assistant</span>
              </div>
              <div className="flex gap-4 items-center">
                <ThemeToggle />
                <button 
                  onClick={() => router.push('/history')}
                  className="text-blue-600 dark:text-green-400 hover:text-blue-700 dark:hover:text-green-300 transition-colors"
                >
                  [history]
                </button>
                <button 
                  onClick={() => router.push('/analytics')}
                  className="text-blue-600 dark:text-green-400 hover:text-blue-700 dark:hover:text-green-300 transition-colors"
                >
                  [analytics]
                </button>
                <button 
                  onClick={() => router.push('/reports')}
                  className="text-blue-600 dark:text-green-400 hover:text-blue-700 dark:hover:text-green-300 transition-colors"
                >
                  [reports]
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {/* Command Prompt Hero */}
        <div className="max-w-4xl mx-auto mb-8">
          <div className="border border-green-500 bg-black p-6">
            <div className="space-y-2 text-sm mb-4">
              <div className="flex items-center gap-2">
                <span className="text-green-500">$</span>
                <span className="text-cyan-400">system</span>
                <span className="text-gray-500">status</span>
              </div>
              <div className="pl-6 space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-green-500">✓</span>
                  <span className="text-gray-400">Engine:</span>
                  <span className="text-yellow-400">AutoGen + Groq</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-green-500">✓</span>
                  <span className="text-gray-400">Status:</span>
                  <span className="text-green-300">ONLINE</span>
                </div>
                <div className="flex items-center gap-2">
                  <span className="text-green-500">→</span>
                  <span className="text-white">Multi-agent AI system for comprehensive literature review</span>
                </div>
              </div>
            </div>
            <div className="border-t border-green-900 pt-4">
              <p className="text-center text-lg text-green-300">
                → Accelerate Your Research with AI Agents
              </p>
            </div>
          </div>
        </div>

        {/* Search Terminal */}
        <div className="max-w-4xl mx-auto mb-8">
          <div className="border border-green-500 bg-black">
            <div className="border-b border-green-500 px-4 py-2 bg-green-950/20">
              <div className="flex items-center gap-2 text-sm">
                <span className="text-green-500">$</span>
                <span className="text-cyan-400">research-agent</span>
                <span className="text-gray-500">--mode</span>
                <span className="text-yellow-400">search</span>
              </div>
            </div>
            <div className="p-6 space-y-4">
              <div>
                <label className="text-sm text-cyan-400 mb-2 block">
                  → QUERY:
                </label>
                <textarea
                  placeholder="Example: What are the latest advances in transformer-based models for multimodal learning?"
                  value={query}
                  onChange={(e) => setQuery(e.target.value)}
                  rows={4}
                  className="w-full bg-black border border-green-500 text-green-400 font-mono text-sm p-3 focus:outline-none focus:border-green-300 resize-none placeholder:text-green-900"
                />
              </div>

              <div>
                <label htmlFor="maxResults" className="text-sm text-cyan-400 mb-2 block">
                  → MAX_RESULTS:
                </label>
                <input
                  id="maxResults"
                  type="number"
                  min="1"
                  value={maxResults}
                  onChange={(e) => {
                    const value = parseInt(e.target.value);
                    if (!isNaN(value) && value >= 1) {
                      setMaxResults(value);
                    }
                  }}
                  className="w-full bg-black border border-green-500 text-green-400 font-mono text-sm px-3 py-2 focus:outline-none focus:border-green-300"
                  placeholder="10"
                  aria-label="Number of papers to fetch"
                />
                <p className="text-xs text-gray-500 mt-1">
                  # Number of papers to retrieve from academic sources
                </p>
              </div>

              {error && (
                <div className="border border-red-500 bg-red-950/20 p-3">
                  <div className="flex items-start gap-2">
                    <span className="text-red-500">ERROR:</span>
                    <p className="text-sm text-red-400 font-mono whitespace-pre-wrap flex-1">{error}</p>
                  </div>
                </div>
              )}

              <button
                onClick={handleSearch}
                disabled={isLoading}
                className="w-full border border-green-500 bg-green-950/30 text-green-400 py-3 hover:bg-green-900/30 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
              >
                {isLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <span className="inline-block w-4 h-4 border-2 border-green-400 border-t-transparent rounded-full animate-spin" />
                    [EXECUTING...]
                  </span>
                ) : (
                  '[EXECUTE SEARCH]'
                )}
              </button>
            </div>
          </div>
        </div>

        {/* Features Grid - CLI Style */}
        <div className="max-w-6xl mx-auto grid md:grid-cols-3 gap-4">
          <div 
            className="border border-green-500 bg-black hover:bg-green-950/20 transition-colors cursor-pointer p-4"
            onClick={() => router.push('/')}
          >
            <div className="flex items-center gap-2 mb-2 text-sm">
              <Search className="w-4 h-4 text-green-500" />
              <span className="text-cyan-400">multi_source_search</span>
            </div>
            <p className="text-xs text-gray-400 mb-2 pl-6">
              Search across arXiv, Semantic Scholar, and more. Intelligent deduplication ensures unique results.
            </p>
            <div className="pl-6 text-xs">
              <span className="text-green-500">→ status:</span>
              <span className="text-green-300"> ACTIVE</span>
            </div>
          </div>

          <div 
            className="border border-green-500 bg-black hover:bg-green-950/20 transition-colors cursor-pointer p-4"
            onClick={() => router.push('/network')}
          >
            <div className="flex items-center gap-2 mb-2 text-sm">
              <Network className="w-4 h-4 text-purple-500" />
              <span className="text-cyan-400">citation_network</span>
            </div>
            <p className="text-xs text-gray-400 mb-2 pl-6">
              Visualize paper relationships and discover influential works through citation analysis.
            </p>
            <div className="pl-6 text-xs">
              <span className="text-green-500">→</span>
              <span className="text-blue-400"> ./explore_network</span>
            </div>
          </div>

          <div 
            className="border border-green-500 bg-black hover:bg-green-950/20 transition-colors cursor-pointer p-4"
            onClick={() => router.push('/analytics')}
          >
            <div className="flex items-center gap-2 mb-2 text-sm">
              <BarChart3 className="w-4 h-4 text-green-500" />
              <span className="text-cyan-400">analytics_dashboard</span>
            </div>
            <p className="text-xs text-gray-400 mb-2 pl-6">
              Track research activity, analyze trends, and view comprehensive statistics across all queries.
            </p>
            <div className="pl-6 text-xs">
              <span className="text-green-500">→</span>
              <span className="text-blue-400"> ./view_analytics</span>
            </div>
          </div>

          <div 
            className="border border-green-500 bg-black hover:bg-green-950/20 transition-colors cursor-pointer p-4"
            onClick={() => router.push('/reports')}
          >
            <div className="flex items-center gap-2 mb-2 text-sm">
              <FileText className="w-4 h-4 text-orange-500" />
              <span className="text-cyan-400">research_reports</span>
            </div>
            <p className="text-xs text-gray-400 mb-2 pl-6">
              Generate and export comprehensive research reports with citations and summaries.
            </p>
            <div className="pl-6 text-xs">
              <span className="text-green-500">→</span>
              <span className="text-blue-400"> ./view_reports</span>
            </div>
          </div>

          <div 
            className="border border-green-500 bg-black hover:bg-green-950/20 transition-colors cursor-pointer p-4"
            onClick={() => router.push('/history')}
          >
            <div className="flex items-center gap-2 mb-2 text-sm">
              <History className="w-4 h-4 text-indigo-500" />
              <span className="text-cyan-400">search_history</span>
            </div>
            <p className="text-xs text-gray-400 mb-2 pl-6">
              Review past research queries, track progress, and revisit previous results.
            </p>
            <div className="pl-6 text-xs">
              <span className="text-green-500">→</span>
              <span className="text-blue-400"> ./view_history</span>
            </div>
          </div>

          <div 
            className="border border-green-500 bg-black hover:bg-green-950/20 transition-colors cursor-pointer p-4"
            onClick={() => window.open('https://github.com/titanite07/autonomous-research-agent', '_blank')}
          >
            <div className="flex items-center gap-2 mb-2 text-sm">
              <Zap className="w-4 h-4 text-yellow-500" />
              <span className="text-cyan-400">ai_agent_system</span>
            </div>
            <p className="text-xs text-gray-400 mb-2 pl-6">
              Multi-agent AI system powered by AutoGen for intelligent research synthesis.
            </p>
            <div className="pl-6 text-xs">
              <span className="text-green-500">→</span>
              <span className="text-blue-400"> ./learn_more</span>
            </div>
          </div>
        </div>
      </main>

      {/* CLI Footer */}
      <footer className="border-t border-green-500 mt-12 py-4">
        <div className="container mx-auto px-4 text-center text-xs text-gray-500">
          <span className="text-green-500">$</span> Built with AutoGen, Groq, Next.js, FastAPI
        </div>
      </footer>

      {/* AI Chatbot */}
      <AIChatbot />
    </div>
  );
}
