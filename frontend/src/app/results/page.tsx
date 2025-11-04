'use client';

import { useEffect, useState, Suspense } from 'react';
import { useSearchParams, useRouter } from 'next/navigation';
import { ArrowLeft, ExternalLink, Loader2, Download, FileText } from 'lucide-react';
import { researchAPI, ResearchWebSocket } from '@/lib/api';
import { EnhancedAgentMonitor } from '@/components/EnhancedAgentMonitor';
import { AnalysisButton } from '@/components/AnalysisButton';
import { ReportPreview } from '@/components/ReportPreview';
import { ThemeToggle } from '@/components/ThemeToggle';
import { AIChatbot } from '@/components/AIChatbot';
import type { SearchResponse, Paper, ResearchStatus } from '@/types';

function ResultsPageContent() {
  const searchParams = useSearchParams();
  const router = useRouter();
  const jobId = searchParams.get('job_id');
  
  const [status, setStatus] = useState<ResearchStatus | null>(null);
  const [results, setResults] = useState<SearchResponse | null>(null);
  const [isLoading, setIsLoading] = useState(!!jobId); // Only loading if we have a jobId
  const [error, setError] = useState(jobId ? '' : 'No job ID provided');
  const [selectedPapers, setSelectedPapers] = useState<string[]>([]);
  const [analysisResult, setAnalysisResult] = useState<Record<string, unknown> | null>(null);
  const [exportFormat, setExportFormat] = useState<'markdown' | 'latex'>('markdown');
  const [showReportPreview, setShowReportPreview] = useState(false);

  useEffect(() => {
    if (!jobId) {
      return;
    }

    console.log('🔍 Starting to poll for job_id:', jobId);
    let pollInterval: NodeJS.Timeout;

    // Function to fetch status and results
    const fetchStatus = async () => {
      try {
        console.log('📡 Fetching status for job_id:', jobId);
        const statusData = await researchAPI.getStatus(jobId);
        console.log('✅ Status received:', statusData);
        setStatus(statusData);

        if (statusData.status === 'completed') {
          console.log('🎉 Job completed! Fetching results...');
          const resultsData = await researchAPI.getResults(jobId);
          console.log('📄 Results received:', resultsData);
          setResults(resultsData);
          setIsLoading(false);
          return true; // Signal to stop polling
        } else if (statusData.status === 'failed') {
          setError('Research failed. Please try again.');
          setIsLoading(false);
          return true; // Signal to stop polling
        }
        return false; // Continue polling
      } catch (err) {
        console.error('❌ Failed to fetch status:', err);
        if (err instanceof Error) {
          setError(err.message);
        } else {
          setError('Failed to fetch status');
        }
        setIsLoading(false);
        return true; // Stop polling on error
      }
    };

    // Fetch immediately on mount
    fetchStatus().then((shouldStop) => {
      if (shouldStop) return;

      // Then poll every 2 seconds
      pollInterval = setInterval(async () => {
        const shouldStop = await fetchStatus();
        if (shouldStop) {
          clearInterval(pollInterval);
        }
      }, 2000);
    });

    // Connect to WebSocket for real-time updates (optional)
    let wsConnection: ResearchWebSocket | null = null;
    try {
      wsConnection = new ResearchWebSocket(
        jobId,
        (event: { type: string; message?: string; [key: string]: unknown }) => {
          console.log('🔄 WebSocket update:', event.type);
          
          // Update status based on WebSocket events
          if (event.type === 'papers_found') {
            fetchStatus(); // Refresh to show new papers
          } else if (event.type === 'completed') {
            fetchStatus(); // Fetch final results
            clearInterval(pollInterval);
          } else if (event.type === 'error') {
            setError(event.message || 'Search failed');
            clearInterval(pollInterval);
          }
        },
        () => {
          // Silently ignore WebSocket errors - HTTP polling will handle updates
        }
      );
      wsConnection.connect();
    } catch {
      // WebSocket not available - HTTP polling will work
    }

    return () => {
      if (pollInterval) {
        clearInterval(pollInterval);
      }
      if (wsConnection) {
        wsConnection.disconnect();
      }
    };
  }, [jobId]);

  const handleExport = async (format: 'markdown' | 'latex') => {
    // Use analysis job_id if available, otherwise search job_id
    const exportJobId = analysisResult ? (analysisResult as { job_id?: string }).job_id || jobId : jobId;
    
    if (!exportJobId) {
      console.error('No job ID available for export');
      return;
    }
    
    try {
      const response = await researchAPI.exportReport({
        job_id: exportJobId,
        format,
        include_citations: true,
        include_graphs: true,
      });
      
      // Create download from content string
      const blob = new Blob([response.content], { type: 'text/plain' });
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${response.title || `research-report-${exportJobId}`}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (err) {
      console.error('Failed to export:', err);
      alert('Export failed. Make sure analysis has been completed.');
    }
  };

  const togglePaperSelection = (paperId: string) => {
    setSelectedPapers(prev => 
      prev.includes(paperId) 
        ? prev.filter(id => id !== paperId)
        : [...prev, paperId]
    );
  };

  const selectAllPapers = () => {
    if (!results?.papers) return;
    const allIds = results.papers.map(p => p.id);
    setSelectedPapers(allIds);
  };

  const clearSelection = () => {
    setSelectedPapers([]);
  };

  if (error) {
    return (
      <div className="min-h-screen p-8 font-mono text-green-400 bg-black">
        <div className="max-w-4xl mx-auto">
          <div className="p-6 bg-black border border-red-500">
            <p className="mb-4 text-red-400">ERROR: {error}</p>
            <button 
              onClick={() => router.push('/')} 
              className="px-4 py-2 text-green-400 transition-colors border border-green-500 hover:bg-green-950/30"
            >
              <ArrowLeft className="inline w-4 h-4 mr-2" />
              [return to search]
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (isLoading || !results) {
    return (
      <div className="min-h-screen p-8 font-mono text-green-400 bg-black">
        <div className="max-w-6xl mx-auto space-y-6">
          <div className="p-6 bg-black border border-green-500">
            <div className="mb-2 text-lg text-cyan-400">$ research-agent --status</div>
            <div className="mb-4 text-green-400">Processing Research Query...</div>
            <div className="mb-6 text-sm text-gray-500">Our AI agents are searching and analyzing papers</div>
            
            <div className="space-y-4">
              <div className="flex items-center justify-center py-8">
                <Loader2 className="w-8 h-8 text-green-400 animate-spin" />
              </div>
              
              <p className="text-sm text-center text-cyan-400">
                Progress: [{status?.progress || 0}%]
              </p>
            </div>
          </div>

          {/* Enhanced Agent Monitor - shows real-time agent status with progress tracking */}
          <EnhancedAgentMonitor 
            jobId={jobId || undefined}
            isActive={isLoading}
            onComplete={() => {
              console.log('Search completed via EnhancedAgentMonitor');
            }}
          />
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-6 font-mono text-green-400 bg-black">
      {/* CLI Header */}
      <div className="mx-auto mb-6 max-w-7xl">
        <div className="p-4 border border-green-500 bg-black/80">
          <div className="flex items-center justify-between mb-4">
            <div className="flex items-center gap-3">
              <span className="text-green-500">$</span>
              <button 
                onClick={() => router.push('/')}
                className="font-mono text-green-400 bg-transparent border-none cursor-pointer hover:text-green-300 hover:bg-green-950/30"
              >
                <ArrowLeft className="inline w-4 h-4 mr-2" />
                ./new-search.sh
              </button>
            </div>
            <div className="flex gap-3">
              <ThemeToggle />
              {analysisResult && (
                <>
                  <button 
                    onClick={() => setShowReportPreview(true)}
                    className="flex items-center gap-2 px-3 py-1 text-cyan-400 transition-colors border border-cyan-500 hover:text-cyan-300 hover:bg-cyan-950/30"
                  >
                    <FileText className="w-4 h-4" />
                    [view report]
                  </button>
                  <select
                    value={exportFormat}
                    onChange={(e) => setExportFormat(e.target.value as 'markdown' | 'latex')}
                    className="px-3 py-1 text-sm text-green-400 bg-black border border-green-500 focus:outline-none focus:border-green-300"
                    aria-label="Export format"
                  >
                    <option value="markdown">Markdown</option>
                    <option value="latex">LaTeX</option>
                  </select>
                  <button 
                    onClick={() => handleExport(exportFormat)}
                    className="flex items-center gap-2 px-3 py-1 text-green-400 transition-colors border border-green-500 hover:text-green-300 hover:bg-green-950/30"
                  >
                    <Download className="w-4 h-4" />
                    [export]
                  </button>
                </>
              )}
              {!analysisResult && (
                <div className="px-3 py-1 text-sm text-gray-500 border border-gray-700">
                  Run analysis first to view report
                </div>
              )}
            </div>
          </div>
          
          {/* Command Prompt */}
          <div className="space-y-2 text-sm">
            <div className="flex items-center gap-2">
              <span className="text-green-500">→</span>
              <span className="text-cyan-400">research-agent</span>
              <span className="text-gray-500">search</span>
              <span className="text-yellow-300">&quot;{results.query}&quot;</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-green-500">✓</span>
              <span className="text-gray-400">Found:</span>
              <span className="text-white">{results.total_papers || 0}</span>
              <span className="text-gray-500">papers</span>
              <span className="text-gray-600">|</span>
              <span className="text-gray-400">Time:</span>
              <span className="text-white">{results.processing_time?.toFixed(2)}s</span>
              <span className="text-gray-600">|</span>
              <span className="text-gray-400">Selected:</span>
              <span className="text-yellow-300">{selectedPapers.length}</span>
            </div>
          </div>
        </div>
      </div>

      {/* Analysis Panel */}
      {selectedPapers.length > 0 && (
        <div className="mx-auto mb-6 max-w-7xl">
          <div className="p-4 border border-cyan-500 bg-cyan-950/10">
            <div className="flex items-center justify-between mb-4">
              <div className="font-mono text-cyan-400">
                <span className="text-green-500">$</span> research-agent analyze --papers={selectedPapers.length}
              </div>
              <div className="flex gap-2">
                <button
                  onClick={selectAllPapers}
                  className="px-3 py-1 text-xs transition-colors border border-cyan-500 text-cyan-400 hover:bg-cyan-950/30"
                >
                  Select All
                </button>
                <button
                  onClick={clearSelection}
                  className="px-3 py-1 text-xs text-red-400 transition-colors border border-red-500 hover:bg-red-950/30"
                >
                  Clear
                </button>
              </div>
            </div>
            <AnalysisButton 
              paperIds={selectedPapers}
              onAnalysisComplete={(result) => setAnalysisResult(result)}
            />
          </div>
        </div>
      )}

      {/* Analysis Results Display */}
      {analysisResult && (
        <div className="mx-auto mb-6 max-w-7xl">
          <div className="p-6 border border-green-500 bg-black/80">
            <h2 className="mb-4 font-mono text-lg text-green-400">
              <span className="text-green-500">$</span> analysis-results.json
            </h2>
            <pre className="p-4 overflow-x-auto text-xs text-green-300 bg-black border border-green-500/30">
              {JSON.stringify(analysisResult, null, 2)}
            </pre>
          </div>
        </div>
      )}

      {/* CLI Papers Output */}
      <div className="mx-auto space-y-4 max-w-7xl">
        {results.papers && results.papers.length > 0 ? (
          results.papers.map((paper: Paper, index: number) => (
            <div 
              key={paper.id} 
              className="p-4 transition-colors border border-green-500 bg-black/60 hover:bg-green-950/20 group"
            >
              {/* Paper Number & Title */}
              <div className="flex items-start gap-4 mb-3">
                <div className="flex items-center gap-3 font-bold text-green-500 shrink-0">
                  <input
                    type="checkbox"
                    checked={selectedPapers.includes(paper.id)}
                    onChange={() => togglePaperSelection(paper.id)}
                    className="w-4 h-4 cursor-pointer accent-green-500"
                    aria-label={`Select paper: ${paper.title}`}
                  />
                  <span>[{(index + 1).toString().padStart(2, '0')}]</span>
                </div>
                <div className="flex-1">
                  <h3 className="mb-2 text-lg font-semibold text-white transition-colors group-hover:text-green-300">
                    {paper.title}
                  </h3>
                  
                  {/* Metadata Line */}
                  <div className="flex flex-wrap items-center gap-4 mb-3 text-sm">
                    <span className="text-gray-400">
                      <span className="text-cyan-400">year:</span> {paper.year}
                    </span>
                    <span className="text-gray-600">|</span>
                    <span className="text-gray-400">
                      <span className="text-cyan-400">citations:</span> {paper.citations}
                    </span>
                    <span className="text-gray-600">|</span>
                    <span className={`${
                      paper.relevance_score >= 0.9 ? 'text-green-400' :
                      paper.relevance_score >= 0.75 ? 'text-yellow-400' :
                      'text-orange-400'
                    }`}>
                      <span className="text-cyan-400">relevance:</span> {(paper.relevance_score * 100).toFixed(1)}%
                    </span>
                    <span className="text-gray-600">|</span>
                    <span className="text-gray-400">
                      <span className="text-cyan-400">source:</span> {paper.source}
                    </span>
                  </div>
                  
                  {/* Authors */}
                  <div className="mb-3 text-sm text-gray-400">
                    <span className="text-cyan-400">authors:</span> {paper.authors.slice(0, 4).join(', ')}
                    {paper.authors.length > 4 && <span className="text-gray-500"> (+{paper.authors.length - 4} more)</span>}
                  </div>
                  
                  {/* Abstract */}
                  <div className="pl-4 mb-3 text-sm text-gray-300 border-l-2 border-green-900">
                    {paper.abstract.slice(0, 250)}...
                  </div>
                  
                  {/* Action Link */}
                  <div className="text-sm">
                    <a 
                      href={paper.url} 
                      target="_blank" 
                      rel="noopener noreferrer"
                      className="inline-flex items-center gap-2 text-blue-400 underline hover:text-blue-300"
                    >
                      → view paper
                      <ExternalLink className="w-3 h-3" />
                    </a>
                  </div>
                </div>
              </div>
            </div>
          ))
        ) : (
          <div className="p-6 text-center border border-yellow-500 bg-yellow-950/20">
            <span className="text-yellow-400">⚠ No papers found yet. Research in progress...</span>
          </div>
        )}
        
        {/* CLI Footer */}
        <div className="pt-4 mt-6 text-sm text-center text-gray-500 border-t border-green-500">
          <span className="text-green-500">$</span> autonomous-research-agent v1.0.0
        </div>
      </div>

      {/* Report Preview Modal */}
      {analysisResult && (
        <ReportPreview
          analysisResult={analysisResult}
          isOpen={showReportPreview}
          onClose={() => setShowReportPreview(false)}
        />
      )}

      {/* AI Chatbot */}
      <AIChatbot />
    </div>
  );
}

export default function ResultsPage() {
  return (
    <Suspense fallback={<div className="flex items-center justify-center min-h-screen bg-slate-50 dark:bg-slate-950"><Loader2 className="w-8 h-8 animate-spin" /></div>}>
      <ResultsPageContent />
    </Suspense>
  );
}
