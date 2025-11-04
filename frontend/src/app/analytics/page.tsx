'use client';

import { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { ArrowLeft, TrendingUp, FileText, Users, Calendar, Loader2, Download, RefreshCw } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { BarChart, Bar, LineChart, Line, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { researchAPI } from '@/lib/api';
import type { AnalyticsData } from '@/types';
import { ThemeToggle } from '@/components/ThemeToggle';

export default function AnalyticsPage() {
  const router = useRouter();
  const [isLoading, setIsLoading] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [analyticsData, setAnalyticsData] = useState<AnalyticsData | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<Date>(new Date());

  const fetchAnalytics = async (refresh = false) => {
    if (refresh) setIsRefreshing(true);
    else setIsLoading(true);
    
    try {
      const data = await researchAPI.getAnalytics();
      setAnalyticsData(data);
      setLastUpdate(new Date());
    } catch (error) {
      console.error('Failed to fetch analytics:', error);
      // Set default empty data on error
      setAnalyticsData({
        stats: {
          total_searches: 0,
          total_papers: 0,
          avg_relevance: 0,
          total_reports: 0,
          active_days: 0,
          searches_growth: 0,
          papers_growth: 0,
          relevance_growth: 0,
        },
        papers_by_source: [],
        searches_by_week: [],
        top_queries: [],
        relevance_distribution: [],
        charts: {
          search_history_data: [],
          papers_per_source_data: [],
          relevance_score_data: [],
          top_searches_data: []
        }
      });
    } finally {
      setIsLoading(false);
      setIsRefreshing(false);
    }
  };

  useEffect(() => {
    fetchAnalytics();
  }, []);

  // Auto-refresh every 30 seconds
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      fetchAnalytics(true);
    }, 30000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  const exportData = () => {
    if (!analyticsData) return;

    const dataStr = JSON.stringify(analyticsData, null, 2);
    const dataBlob = new Blob([dataStr], { type: 'application/json' });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement('a');
    link.href = url;
    link.download = `analytics-${new Date().toISOString().split('T')[0]}.json`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-slate-50 dark:bg-slate-950 flex items-center justify-center">
        <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
      </div>
    );
  }

  // Sample data for charts (will be replaced with real data from API)
  const stats = analyticsData?.stats || {
    total_searches: 0,
    total_papers: 0,
    avg_relevance: 0,
    total_reports: 0,
    searches_growth: 0,
    papers_growth: 0,
    relevance_growth: 0,
    active_days: 0
  };
  
  const charts = analyticsData?.charts || {};
  const searchHistoryData = (charts.search_history_data as Array<{ date: string; searches: number }>) || [];
  const papersPerSourceData = (charts.papers_per_source_data as Array<{ source: string; papers: number; color: string }>) || [];
  const relevanceScoreData = (charts.relevance_score_data as Array<{ query: string; avgScore: number }>) || [];
  const topSearchesData = (charts.top_searches_data as Array<{ topic: string; searches: number }>) || [];

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950 p-8 transition-colors">
      <div className="max-w-7xl mx-auto space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-gray-300 dark:border-gray-700 pb-4">
          <div>
            <div className="flex items-center gap-4 mb-4">
              <Button variant="ghost" onClick={() => router.push('/')}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back to Home
              </Button>
              <ThemeToggle />
            </div>
            <h1 className="text-4xl font-bold text-gray-900 dark:text-white">Research Analytics</h1>
            <p className="text-slate-600 dark:text-slate-400 mt-2">
              Real-time insights and statistics from your research activities
            </p>
            <p className="text-xs text-slate-500 dark:text-slate-500 mt-1">
              Last updated: {lastUpdate.toLocaleTimeString()}
            </p>
          </div>
          <div className="flex gap-2">
            <Button
              onClick={() => fetchAnalytics(true)}
              disabled={isRefreshing}
              variant="outline"
              size="sm"
            >
              {isRefreshing ? (
                <Loader2 className="w-4 h-4 mr-2 animate-spin" />
              ) : (
                <RefreshCw className="w-4 h-4 mr-2" />
              )}
              Refresh
            </Button>
            <Button
              onClick={() => setAutoRefresh(!autoRefresh)}
              variant={autoRefresh ? "default" : "outline"}
              size="sm"
            >
              {autoRefresh ? "Auto-Refresh ON" : "Auto-Refresh OFF"}
            </Button>
            <Button
              onClick={exportData}
              variant="outline"
              size="sm"
              disabled={!analyticsData}
            >
              <Download className="w-4 h-4 mr-2" />
              Export
            </Button>
          </div>
        </div>

        {/* Stats Cards */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Total Searches</CardTitle>
              <TrendingUp className="h-4 w-4 text-slate-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_searches || 0}</div>
              <p className="text-xs text-slate-500 mt-1">
                {(stats.searches_growth ?? 0) > 0 ? '+' : ''}{stats.searches_growth ?? 0}% from last month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Papers Analyzed</CardTitle>
              <FileText className="h-4 w-4 text-slate-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.total_papers || 0}</div>
              <p className="text-xs text-slate-500 mt-1">
                {(stats.papers_growth ?? 0) > 0 ? '+' : ''}{stats.papers_growth ?? 0}% from last month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Avg. Relevance</CardTitle>
              <Users className="h-4 w-4 text-slate-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.avg_relevance || 0}%</div>
              <p className="text-xs text-slate-500 mt-1">
                {(stats.relevance_growth ?? 0) > 0 ? '+' : ''}{stats.relevance_growth ?? 0}% from last month
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">Active Days</CardTitle>
              <Calendar className="h-4 w-4 text-slate-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{stats.active_days || 0}</div>
              <p className="text-xs text-slate-500 mt-1">
                Out of last 30 days
              </p>
            </CardContent>
          </Card>
        </div>

        {/* Charts Row 1 */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Search History */}
          <Card>
            <CardHeader>
              <CardTitle>Weekly Search Activity</CardTitle>
              <CardDescription>Number of searches per day this week</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={searchHistoryData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <Tooltip />
                  <Bar dataKey="searches" fill="#3b82f6" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>

          {/* Papers per Source */}
          <Card>
            <CardHeader>
              <CardTitle>Papers by Source</CardTitle>
              <CardDescription>Distribution of papers across different sources</CardDescription>
            </CardHeader>
            <CardContent>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={papersPerSourceData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="papers"
                  >
                    {papersPerSourceData.map((entry: { source: string; papers: number; color: string }, index: number) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </div>

        {/* Charts Row 2 */}
        <Card>
          <CardHeader>
            <CardTitle>Average Relevance Scores</CardTitle>
            <CardDescription>Average relevance scores for recent queries</CardDescription>
          </CardHeader>
          <CardContent>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={relevanceScoreData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="query" />
                <YAxis domain={[0, 1]} />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="avgScore" stroke="#10b981" strokeWidth={2} name="Avg. Relevance" />
              </LineChart>
            </ResponsiveContainer>
          </CardContent>
        </Card>

        {/* Top Searches */}
        <Card>
          <CardHeader>
            <CardTitle>Top Research Topics</CardTitle>
            <CardDescription>Most searched topics this month</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              {topSearchesData.map((item: { topic: string; searches: number }, index: number) => (
                <div key={item.topic} className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900 flex items-center justify-center text-sm font-semibold">
                      {index + 1}
                    </div>
                    <span className="font-medium">{item.topic}</span>
                  </div>
                  <div className="text-sm text-slate-500">
                    {item.searches} searches
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
