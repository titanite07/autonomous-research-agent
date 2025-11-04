'use client';

import { useState, useEffect } from 'react';
import { Brain, Loader2, CheckCircle2, AlertCircle, Clock, Zap, TrendingUp } from 'lucide-react';
import { ResearchWebSocket } from '@/lib/api';
import styles from './EnhancedAgentMonitor.module.css';

interface AgentEvent {
  agent: string;
  status: 'idle' | 'working' | 'completed' | 'error';
  task: string;
  progress: number;
  timestamp: string;
  details?: string;
  tokensUsed?: number;
  duration?: number;
}

interface EnhancedAgentMonitorProps {
  jobId?: string;
  isActive?: boolean;
  onComplete?: () => void;
}

export function EnhancedAgentMonitor({ jobId, isActive = false, onComplete }: EnhancedAgentMonitorProps) {
  const [agents, setAgents] = useState<Record<string, AgentEvent>>({
    scraper: { agent: 'Scraper Agent', status: 'idle', task: 'Waiting...', progress: 0, timestamp: new Date().toISOString() },
    summarization: { agent: 'Summarization Agent', status: 'idle', task: 'Waiting...', progress: 0, timestamp: new Date().toISOString() },
    synthesis: { agent: 'Synthesis Agent', status: 'idle', task: 'Waiting...', progress: 0, timestamp: new Date().toISOString() },
    citation: { agent: 'Citation Agent', status: 'idle', task: 'Waiting...', progress: 0, timestamp: new Date().toISOString() },
  });
  
  const [overallProgress, setOverallProgress] = useState(0);
  const [totalTokens, setTotalTokens] = useState(0);
  const [startTime] = useState<Date>(new Date());
  const [elapsedTime, setElapsedTime] = useState(0);

  useEffect(() => {
    if (!jobId || !isActive) return;
    
    const ws = new ResearchWebSocket(
      jobId,
      (event) => {
        const eventType = event.type as string;
        const message = event.message as string;
        const timestamp = new Date().toISOString();

        // Update agents based on event types
        if (eventType.includes('search') || eventType.includes('scraping')) {
          setAgents(prev => ({
            ...prev,
            scraper: {
              agent: 'Scraper Agent',
              status: eventType.includes('complete') ? 'completed' : eventType.includes('error') ? 'error' : 'working',
              task: message,
              progress: event.progress_percentage as number || 0,
              timestamp,
              details: `Found ${event.total as number || 0} papers`,
            }
          }));
        }

        if (eventType.includes('summarizing') || eventType.includes('summarization')) {
          setAgents(prev => ({
            ...prev,
            summarization: {
              agent: 'Summarization Agent',
              status: eventType.includes('complete') ? 'completed' : eventType.includes('error') ? 'error' : 'working',
              task: message,
              progress: event.progress_percentage as number || 0,
              timestamp,
              details: `Processing ${event.current as number || 0}/${event.total as number || 0} papers`,
              tokensUsed: event.tokens_used as number,
            }
          }));
        }

        if (eventType.includes('synthesizing') || eventType.includes('synthesis')) {
          setAgents(prev => ({
            ...prev,
            synthesis: {
              agent: 'Synthesis Agent',
              status: eventType.includes('complete') ? 'completed' : eventType.includes('error') ? 'error' : 'working',
              task: message,
              progress: event.progress_percentage as number || 0,
              timestamp,
              details: 'Analyzing findings across papers',
              tokensUsed: event.tokens_used as number,
            }
          }));
        }

        if (eventType.includes('citation') || eventType.includes('building_citations')) {
          setAgents(prev => ({
            ...prev,
            citation: {
              agent: 'Citation Agent',
              status: eventType.includes('complete') ? 'completed' : eventType.includes('error') ? 'error' : 'working',
              task: message,
              progress: event.progress_percentage as number || 0,
              timestamp,
              details: `Building citation network`,
              tokensUsed: event.tokens_used as number,
            }
          }));
        }

        // Update overall progress
        const avgProgress = Object.values(agents).reduce((sum, agent) => sum + agent.progress, 0) / Object.keys(agents).length;
        setOverallProgress(avgProgress);

        // Update total tokens
        if (event.tokens_used) {
          setTotalTokens(prev => prev + (event.tokens_used as number));
        }

        // Complete callback
        if (eventType === 'analysis_complete' || eventType === 'search_complete') {
          onComplete?.();
        }
      },
      () => {
        // Silently handle WebSocket errors - the component will work without real-time updates
        // HTTP polling will handle status updates as fallback
        console.debug('WebSocket connection unavailable, using HTTP polling fallback');
      },
      () => {
        // Silently handle WebSocket close
        console.debug('WebSocket connection closed');
      }
    );

    ws.connect();

    return () => {
      ws.disconnect();
    };
  }, [jobId, isActive, onComplete, agents]);

  // Timer effect
  useEffect(() => {
    if (!startTime || !isActive) return;

    const timer = setInterval(() => {
      setElapsedTime(Math.floor((new Date().getTime() - startTime.getTime()) / 1000));
    }, 1000);

    return () => clearInterval(timer);
  }, [startTime, isActive]);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'working':
        return <Loader2 className="w-4 h-4 animate-spin text-yellow-400" />;
      case 'completed':
        return <CheckCircle2 className="w-4 h-4 text-green-400" />;
      case 'error':
        return <AlertCircle className="w-4 h-4 text-red-400" />;
      default:
        return <Brain className="w-4 h-4 text-gray-400" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'working':
        return 'text-yellow-400 dark:text-yellow-400 light:text-yellow-600';
      case 'completed':
        return 'text-green-400 dark:text-green-400 light:text-green-600';
      case 'error':
        return 'text-red-400 dark:text-red-400 light:text-red-600';
      default:
        return 'text-gray-400 dark:text-gray-400 light:text-gray-600';
    }
  };

  const formatTime = (seconds: number) => {
    const mins = Math.floor(seconds / 60);
    const secs = seconds % 60;
    return `${mins}:${secs.toString().padStart(2, '0')}`;
  };

  if (!isActive && overallProgress === 0) {
    return null;
  }

  return (
    <div className="border border-green-500 dark:border-green-500 light:border-blue-300 p-4 space-y-4 bg-black/50 dark:bg-black/50 light:bg-white/90 backdrop-blur-sm">
      {/* Header */}
      <div className="flex items-center justify-between border-b border-green-500 dark:border-green-500 light:border-blue-300 pb-2">
        <div className="flex items-center gap-2">
          <Brain className="w-5 h-5 text-cyan-400 dark:text-cyan-400 light:text-blue-600" />
          <span className="text-green-400 dark:text-green-400 light:text-blue-700 font-bold">
            AGENT MONITOR
          </span>
        </div>
        <div className="flex gap-4 text-xs">
          <div className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            <span className="text-gray-400 dark:text-gray-400 light:text-gray-600">{formatTime(elapsedTime)}</span>
          </div>
          {totalTokens > 0 && (
            <div className="flex items-center gap-1">
              <Zap className="w-3 h-3" />
              <span className="text-gray-400 dark:text-gray-400 light:text-gray-600">{totalTokens} tokens</span>
            </div>
          )}
        </div>
      </div>

      {/* Overall Progress */}
      <div className="space-y-1">
        <div className="flex items-center justify-between text-xs">
          <span className="text-gray-400 dark:text-gray-400 light:text-gray-600">Overall Progress</span>
          <span className="text-green-400 dark:text-green-400 light:text-blue-600">{Math.round(overallProgress)}%</span>
        </div>
        <div className="w-full h-2 bg-gray-800 dark:bg-gray-800 light:bg-gray-200 rounded overflow-hidden">
          {/* eslint-disable-next-line react/forbid-dom-props */}
          <div 
            className={`h-full bg-green-500 dark:bg-green-500 light:bg-blue-500 ${styles.overallProgressBar}`}
            style={{ width: `${overallProgress}%` }}
          />
        </div>
      </div>

      {/* Agent Status */}
      <div className="space-y-2">
        {Object.entries(agents).map(([key, agent]) => (
          <div key={key} className="space-y-1">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                {getStatusIcon(agent.status)}
                <span className={`text-sm ${getStatusColor(agent.status)}`}>
                  {agent.agent}
                </span>
              </div>
              <span className="text-xs text-gray-500 dark:text-gray-500 light:text-gray-600">
                {agent.progress}%
              </span>
            </div>
            <div className="pl-6">
              <p className="text-xs text-gray-400 dark:text-gray-400 light:text-gray-600">{agent.task}</p>
              {agent.details && (
                <p className="text-xs text-gray-500 dark:text-gray-500 light:text-gray-500 mt-0.5">
                  {agent.details}
                </p>
              )}
              {agent.tokensUsed && (
                <div className="flex items-center gap-1 mt-0.5">
                  <TrendingUp className="w-3 h-3 text-cyan-400 dark:text-cyan-400 light:text-blue-500" />
                  <span className="text-xs text-cyan-400 dark:text-cyan-400 light:text-blue-500">
                    {agent.tokensUsed} tokens
                  </span>
                </div>
              )}
            </div>
            <div className="w-full h-1 bg-gray-800 dark:bg-gray-800 light:bg-gray-200 rounded overflow-hidden ml-6">
              {/* eslint-disable-next-line react/forbid-dom-props */}
              <div 
                className={`h-full ${styles.agentProgressBar} ${
                  agent.status === 'completed' ? 'bg-green-500 dark:bg-green-500 light:bg-green-600' :
                  agent.status === 'working' ? 'bg-yellow-500 dark:bg-yellow-500 light:bg-yellow-600' :
                  agent.status === 'error' ? 'bg-red-500 dark:bg-red-500 light:bg-red-600' :
                  'bg-gray-600 dark:bg-gray-600 light:bg-gray-400'
                }`}
                style={{ width: `${agent.progress}%` }}
              />
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
