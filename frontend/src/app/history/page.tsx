'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { researchAPI } from '@/lib/api';
import type { SearchHistory } from '@/types';
import { ThemeToggle } from '@/components/ThemeToggle';
import { 
  ArrowLeft, 
  History as HistoryIcon, 
  Calendar,
  FileText,
  CheckCircle,
  XCircle,
  Clock,
  Loader2,
  Eye,
  Trash2
} from 'lucide-react';

export default function HistoryPage() {
  const router = useRouter();
  const [history, setHistory] = useState<SearchHistory[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [filter, setFilter] = useState<'all' | 'completed' | 'processing' | 'failed'>('all');

  useEffect(() => {
    // Fetch real history data from API
    const fetchHistory = async () => {
      setIsLoading(true);
      try {
        const response = await researchAPI.getHistory(50);
        setHistory(response.items || []);
      } catch (error) {
        console.error('Failed to fetch history:', error);
        // Set empty history on error
        setHistory([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchHistory();
  }, []);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const calculateDuration = (start: string, end?: string) => {
    if (!end) return 'In progress';
    const duration = new Date(end).getTime() - new Date(start).getTime();
    const minutes = Math.floor(duration / 60000);
    const seconds = Math.floor((duration % 60000) / 1000);
    return `${minutes}m ${seconds}s`;
  };

  const getStatusIcon = (status: SearchHistory['status']) => {
    switch (status) {
      case 'completed':
        return <CheckCircle className="w-4 h-4 text-green-600" />;
      case 'processing':
        return <Loader2 className="w-4 h-4 text-blue-600 animate-spin" />;
      case 'failed':
        return <XCircle className="w-4 h-4 text-red-600" />;
    }
  };

  const filteredHistory = filter === 'all' 
    ? history 
    : history.filter(item => item.status === filter);

  const handleViewResults = (jobId: string) => {
    router.push(`/results?job_id=${jobId}`);
  };

  const handleDeleteHistory = async (id: string) => {
    if (confirm('Are you sure you want to delete this search history?')) {
      try {
        await researchAPI.deleteHistory(id);
        setHistory(history.filter(item => item.id !== id));
      } catch (error) {
        console.error('Failed to delete history:', error);
        alert('Failed to delete history item');
      }
    }
  };

  return (
    <div className="min-h-screen bg-black text-green-400 font-mono">
      {/* CLI Header */}
      <header className="border-b border-green-500 bg-black">
        <div className="container mx-auto px-4 py-4">
          <div className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-4">
                <button 
                  onClick={() => router.push('/')}
                  className="flex items-center gap-2 text-green-400 hover:text-green-300 transition-colors"
                >
                  <ArrowLeft className="w-4 h-4" />
                  <span>[back]</span>
                </button>
                <div className="flex items-center gap-2">
                  <span className="text-green-500">$</span>
                  <span className="text-cyan-400">research-agent</span>
                  <span className="text-gray-500">history</span>
                  <span className="text-gray-600">|</span>
                  <span className="text-yellow-400">Search History</span>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <ThemeToggle />
                <button 
                  onClick={() => router.push('/')}
                  className="border border-green-500 px-3 py-1 text-green-400 hover:bg-green-950/30 transition-colors"
                >
                  [new search]
                </button>
              </div>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <div className="flex items-center gap-2">
              <Loader2 className="w-6 h-6 animate-spin text-green-400" />
              <span className="text-green-400">Loading history...</span>
            </div>
          </div>
        ) : (
          <div className="max-w-6xl mx-auto">
            {/* Filter Tabs - CLI Style */}
            <div className="flex gap-2 mb-6 text-sm">
              <button 
                onClick={() => setFilter('all')}
                className={`px-3 py-1 border transition-colors ${
                  filter === 'all' 
                    ? 'border-green-500 bg-green-950/30 text-green-300' 
                    : 'border-green-500 text-green-400 hover:bg-green-950/20'
                }`}
              >
                [all: {history.length}]
              </button>
              <button 
                onClick={() => setFilter('completed')}
                className={`px-3 py-1 border transition-colors ${
                  filter === 'completed' 
                    ? 'border-green-500 bg-green-950/30 text-green-300' 
                    : 'border-green-500 text-green-400 hover:bg-green-950/20'
                }`}
              >
                [completed: {history.filter(h => h.status === 'completed').length}]
              </button>
              <button 
                onClick={() => setFilter('processing')}
                className={`px-3 py-1 border transition-colors ${
                  filter === 'processing' 
                    ? 'border-green-500 bg-green-950/30 text-green-300' 
                    : 'border-green-500 text-green-400 hover:bg-green-950/20'
                }`}
              >
                [processing: {history.filter(h => h.status === 'processing').length}]
              </button>
              <button 
                onClick={() => setFilter('failed')}
                className={`px-3 py-1 border transition-colors ${
                  filter === 'failed' 
                    ? 'border-green-500 bg-green-950/30 text-green-300' 
                    : 'border-green-500 text-green-400 hover:bg-green-950/20'
                }`}
              >
                [failed: {history.filter(h => h.status === 'failed').length}]
              </button>
            </div>

            {/* History List */}
            {filteredHistory.length === 0 ? (
              <div className="border border-yellow-500 bg-yellow-950/20 p-8 text-center">
                <HistoryIcon className="w-12 h-12 mx-auto mb-4 text-yellow-500" />
                <h3 className="text-lg text-yellow-400 mb-2">No History Found</h3>
                <p className="text-sm text-gray-400 mb-6">
                  {filter === 'all' 
                    ? '→ Start a research query to see your history'
                    : `→ No ${filter} searches found`}
                </p>
                <button 
                  onClick={() => router.push('/')}
                  className="border border-green-500 px-4 py-2 text-green-400 hover:bg-green-950/30 transition-colors"
                >
                  [start research]
                </button>
              </div>
            ) : (
              <div className="space-y-4">
                {filteredHistory.map((item) => (
                  <div key={item.id} className="border border-green-500 bg-black hover:bg-green-950/20 transition-colors">
                    <div className="border-b border-green-500 px-4 py-2 bg-green-950/20">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2 text-sm flex-1">
                          {getStatusIcon(item.status)}
                          <span className="text-white">{item.query}</span>
                          <span className={`text-xs ml-2 ${
                            item.status === 'completed' ? 'text-green-400' :
                            item.status === 'processing' ? 'text-yellow-400' :
                            'text-red-400'
                          }`}>
                            [{item.status}]
                          </span>
                        </div>
                      </div>
                      <div className="text-xs text-gray-500 mt-1">
                        job_id: {item.job_id}
                      </div>
                    </div>
                    <div className="p-4">
                      <div className="flex items-center justify-between">
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-xs">
                          <div>
                            <p className="text-cyan-400 mb-1">started:</p>
                            <p className="text-gray-300 flex items-center gap-1">
                              <Calendar className="w-3 h-3" />
                              {formatDate(item.created_at)}
                            </p>
                          </div>
                          <div>
                            <p className="text-cyan-400 mb-1">duration:</p>
                            <p className="text-gray-300 flex items-center gap-1">
                              <Clock className="w-3 h-3" />
                              {calculateDuration(item.created_at, item.completed_at)}
                            </p>
                          </div>
                          <div>
                            <p className="text-cyan-400 mb-1">papers:</p>
                            <p className="text-gray-300 flex items-center gap-1">
                              <FileText className="w-3 h-3" />
                              {item.results_count || 'N/A'}
                            </p>
                          </div>
                          <div>
                            <p className="text-cyan-400 mb-1">sources:</p>
                            <p className="text-gray-300">
                              {item.sources?.join(', ') || 'N/A'}
                            </p>
                          </div>
                        </div>
                        <div className="flex gap-2">
                          {item.status === 'completed' && (
                            <button 
                              onClick={() => handleViewResults(item.job_id)}
                              className="border border-green-500 px-3 py-1 text-green-400 hover:bg-green-950/30 transition-colors text-xs flex items-center gap-1"
                              aria-label="View results"
                            >
                              <Eye className="w-3 h-3" />
                              view
                            </button>
                          )}
                          <button 
                            onClick={() => handleDeleteHistory(item.id)}
                            className="border border-red-500 px-3 py-1 text-red-400 hover:bg-red-950/30 transition-colors text-xs flex items-center gap-1"
                            aria-label="Delete history"
                          >
                            <Trash2 className="w-3 h-3" />
                            <span className="sr-only">Delete</span>
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}
      </main>
    </div>
  );
}
