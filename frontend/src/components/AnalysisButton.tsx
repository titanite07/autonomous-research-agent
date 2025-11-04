'use client';

import { useState } from 'react';
import { Loader2, Brain, CheckCircle2, AlertCircle } from 'lucide-react';
import { researchAPI, ResearchWebSocket } from '@/lib/api';
import styles from './AnalysisButton.module.css';

interface AnalysisButtonProps {
  paperIds: string[];
  searchId?: number;
  onAnalysisComplete?: (result: Record<string, unknown>) => void;
}

interface AnalysisEvent {
  type: string;
  message: string;
  timestamp?: string;
  progress_percentage?: number;
  current?: number;
  total?: number;
}

export function AnalysisButton({ paperIds, onAnalysisComplete }: AnalysisButtonProps) {
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [currentEvent, setCurrentEvent] = useState<AnalysisEvent | null>(null);
  const [events, setEvents] = useState<AnalysisEvent[]>([]);
  const [analysisResult, setAnalysisResult] = useState<Record<string, unknown> | null>(null);
  const [error, setError] = useState<string | null>(null);

  const startAnalysis = async () => {
    if (paperIds.length === 0) {
      setError('No papers selected for analysis');
      return;
    }

    setIsAnalyzing(true);
    setProgress(0);
    setCurrentEvent(null);
    setEvents([]);
    setError(null);
    setAnalysisResult(null);

    // Generate unique job ID for WebSocket tracking
    const jobId = `analysis-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;

    // Convert string IDs to integers for backend
    const paperIdsAsNumbers = paperIds.map(id => parseInt(id, 10)).filter(id => !isNaN(id));

    // Connect WebSocket for real-time updates
    const ws = new ResearchWebSocket(
      jobId,
      (event) => {
        const normalizedEvent: AnalysisEvent = {
          type: event.type as string,
          message: (event.message as string) || '',
          timestamp: event.timestamp as string | undefined,
          progress_percentage: event.progress_percentage as number | undefined,
          current: event.current as number | undefined,
          total: event.total as number | undefined,
        };
        
        setCurrentEvent(normalizedEvent);
        setEvents((prev) => [...prev, normalizedEvent]);

        // Update progress based on event type
        if (event.type === 'analysis_started') {
          setProgress(5);
        } else if (event.type === 'summarizing') {
          setProgress(20);
        } else if (event.type === 'summarizing_progress') {
          const progressPct = event.progress_percentage as number || 0;
          setProgress(20 + progressPct * 0.3); // 20-50%
        } else if (event.type === 'summarizing_complete') {
          setProgress(50);
        } else if (event.type === 'synthesizing') {
          setProgress(60);
        } else if (event.type === 'synthesis_complete') {
          setProgress(70);
        } else if (event.type === 'building_citations') {
          setProgress(80);
        } else if (event.type === 'citations_complete') {
          setProgress(85);
        } else if (event.type === 'extracting_knowledge_graph') {
          setProgress(90);
        } else if (event.type === 'knowledge_graph_complete') {
          setProgress(95);
        } else if (event.type === 'analysis_complete') {
          setProgress(100);
        } else if (event.type === 'analysis_error') {
          setError(event.message as string || 'Analysis failed');
        }
      },
      (error) => {
        console.warn('WebSocket error (will use HTTP fallback):', error);
      }
    );

    ws.connect();

    try {
      // Trigger analysis via API
      const result = await researchAPI.analyze({
        paper_ids: paperIdsAsNumbers,
        include_citations: true,
        include_knowledge_graph: true,
        job_id: jobId,
      });

      setAnalysisResult(result);
      setProgress(100);
      setIsAnalyzing(false);

      if (onAnalysisComplete) {
        onAnalysisComplete(result);
      }
    } catch (err) {
      console.error('Analysis failed:', err);

      // Better error messages
      let errorMessage = 'Analysis failed';
      if (err instanceof Error) {
        if (err.message.includes('timeout')) {
          errorMessage = 'Analysis timeout - the operation took too long. Try analyzing fewer papers or check backend logs.';
        } else if (err.message.includes('Network Error')) {
          errorMessage = 'Network error - check if backend is running on http://localhost:8000';
        } else {
          errorMessage = err.message;
        }
      }

      setError(errorMessage);
      setIsAnalyzing(false);
    } finally {
      ws.disconnect();
    }
  };

  return (
    <div className="space-y-4">
      <button
        onClick={startAnalysis}
        disabled={isAnalyzing || paperIds.length === 0}
        className={`
          w-full border px-6 py-3 font-mono transition-colors
          flex items-center justify-center gap-2
          ${isAnalyzing 
            ? 'border-yellow-500 text-yellow-400 bg-yellow-950/20 cursor-not-allowed' 
            : 'border-green-500 text-green-400 hover:bg-green-950/30'
          }
        `}
      >
        {isAnalyzing ? (
          <>
            <Loader2 className="w-5 h-5 animate-spin" />
            Analyzing... {progress.toFixed(0)}%
          </>
        ) : (
          <>
            <Brain className="w-5 h-5" />
            Analyze Papers ({paperIds.length} selected)
          </>
        )}
      </button>

      {/* Progress Bar */}
      {isAnalyzing && (
        <div className="p-4 bg-black border border-green-500">
          <div className="flex justify-between mb-2 text-sm">
            <span className="text-green-400">Progress:</span>
            <span className="text-green-300">{progress.toFixed(0)}%</span>
          </div>
          <div className="h-2 bg-gray-900 border border-green-500/30">
            {/* eslint-disable-next-line react/forbid-dom-props */}
            <div 
              className={`h-full bg-green-500 ${styles.progressBar}`}
              style={{ width: `${progress}%` }}
              role="progressbar"
              aria-label="Analysis progress"
              aria-valuenow={Math.round(progress)}
              aria-valuemin={0}
              aria-valuemax={100}
            />
          </div>

          {/* Current Event */}
          {currentEvent && (
            <div className="mt-4 text-sm text-green-300">
              <div className="flex items-center gap-2">
                <Loader2 className="w-4 h-4 animate-spin" />
                <span>{currentEvent.message}</span>
              </div>
              {currentEvent.current && currentEvent.total && (
                <div className="mt-1 text-xs text-green-500/70">
                  ({currentEvent.current} / {currentEvent.total})
                </div>
              )}
            </div>
          )}

          {/* Event Log */}
          <details className="mt-4">
            <summary className="text-xs text-green-500 cursor-pointer hover:text-green-400">
              View detailed log ({events.length} events)
            </summary>
            <div className="mt-2 space-y-1 overflow-y-auto max-h-48">
              {events.map((event, idx) => (
                <div key={idx} className="font-mono text-xs text-green-600">
                  [{new Date(event.timestamp || '').toLocaleTimeString()}] {event.type}: {event.message}
                </div>
              ))}
            </div>
          </details>
        </div>
      )}

      {/* Error Display */}
      {error && (
        <div className="p-4 border border-red-500 bg-red-950/20">
          <div className="flex items-center gap-2 text-red-400">
            <AlertCircle className="w-5 h-5" />
            <span>Error: {error}</span>
          </div>
        </div>
      )}

      {/* Success Display */}
      {analysisResult && !isAnalyzing && (
        <div className="p-4 border border-green-500 bg-green-950/20">
          <div className="flex items-center gap-2 mb-3 text-green-400">
            <CheckCircle2 className="w-5 h-5" />
            <span>Analysis Complete!</span>
          </div>
          <div className="space-y-2 text-sm text-green-300">
            <div>
              <span className="text-green-500">Papers Analyzed:</span>{' '}
              {(analysisResult as { total_papers?: number }).total_papers || paperIds.length}
            </div>
            <div>
              <span className="text-green-500">Job ID:</span>{' '}
              <code className="px-2 py-1 text-xs bg-black border border-green-500/30">
                {(analysisResult as { job_id?: string }).job_id}
              </code>
            </div>
          </div>
        </div>
      )}
    </div>
  );

}