'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { researchAPI } from '@/lib/api';
import { ThemeToggle } from '@/components/ThemeToggle';
import { 
  ArrowLeft, 
  FileText, 
  Download, 
  Calendar, 
  Clock,
  CheckCircle,
  Loader2,
  Plus,
  Eye
} from 'lucide-react';

interface Report {
  id: string;
  job_id: string;
  title?: string;
  type?: string;
  query?: string;
  created_at: string;
  paper_count?: number;
  sources?: string[];
  size?: string;
  format?: string;
  status?: 'completed' | 'processing' | 'failed';
  summary?: string;
}

export default function ReportsPage() {
  const router = useRouter();
  const [reports, setReports] = useState<Report[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // Fetch real reports data from API
    const fetchReports = async () => {
      setIsLoading(true);
      try {
        const response = await researchAPI.getReports(50);
        setReports(response.reports || []);
      } catch (error) {
        console.error('Failed to fetch reports:', error);
        setReports([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchReports();
  }, []);

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString('en-US', { 
      month: 'short', 
      day: 'numeric', 
      year: 'numeric' 
    });
  };

  const getStatusBadge = (status: Report['status']) => {
    switch (status) {
      case 'completed':
        return <Badge className="bg-green-100 text-green-700 dark:bg-green-900 dark:text-green-300">
          <CheckCircle className="w-3 h-3 mr-1" />
          Completed
        </Badge>;
      case 'processing':
        return <Badge className="bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300">
          <Loader2 className="w-3 h-3 mr-1 animate-spin" />
          Processing
        </Badge>;
      case 'failed':
        return <Badge variant="destructive">Failed</Badge>;
    }
  };

  const handleDownloadReport = (reportId: string) => {
    // Implement report download logic
    console.log('Downloading report:', reportId);
    alert('Report download will be implemented with backend integration');
  };

  const handleViewReport = (reportId: string) => {
    // Navigate to detailed report view
    router.push(`/reports/${reportId}`);
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      {/* Header */}
      <header className="border-b bg-white dark:bg-slate-900">
        <div className="container mx-auto px-4 py-6">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="sm" onClick={() => router.push('/')}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-blue-600 rounded-lg">
                  <FileText className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold">Research Reports</h1>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    View and manage your research reports
                  </p>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <ThemeToggle />
              <Button onClick={() => router.push('/')}>
                <Plus className="w-4 h-4 mr-2" />
                New Research
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
          </div>
        ) : reports.length === 0 ? (
          <Card className="max-w-2xl mx-auto">
            <CardContent className="py-12 text-center">
              <FileText className="w-12 h-12 mx-auto mb-4 text-slate-400" />
              <h3 className="text-lg font-semibold mb-2">No Reports Yet</h3>
              <p className="text-sm text-slate-600 dark:text-slate-400 mb-6">
                Start a research query to generate your first report
              </p>
              <Button onClick={() => router.push('/')}>
                <Plus className="w-4 h-4 mr-2" />
                Start Research
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="max-w-6xl mx-auto space-y-6">
            {/* Stats Cards */}
            <div className="grid md:grid-cols-3 gap-4 mb-8">
              <Card>
                <CardContent className="py-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-600 dark:text-slate-400">Total Reports</p>
                      <p className="text-3xl font-bold">{reports.length}</p>
                    </div>
                    <FileText className="w-8 h-8 text-blue-600" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="py-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-600 dark:text-slate-400">Papers Analyzed</p>
                      <p className="text-3xl font-bold">
                        {reports.reduce((sum, r) => sum + (r.paper_count || 0), 0)}
                      </p>
                    </div>
                    <CheckCircle className="w-8 h-8 text-green-600" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="py-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-600 dark:text-slate-400">Completed</p>
                      <p className="text-3xl font-bold">
                        {reports.filter(r => r.status === 'completed').length}
                      </p>
                    </div>
                    <Clock className="w-8 h-8 text-purple-600" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Reports List */}
            <div className="space-y-4">
              {reports.map((report) => (
                <Card key={report.id} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <div className="flex items-start justify-between">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-2">
                          <CardTitle className="text-xl">{report.title || 'Untitled Report'}</CardTitle>
                          {getStatusBadge(report.status || 'completed')}
                        </div>
                        <CardDescription className="text-base">
                          {report.query || 'No query specified'}
                        </CardDescription>
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent>
                    <div className="flex items-center justify-between">
                      <div className="space-y-2">
                        <div className="flex items-center gap-4 text-sm text-slate-600 dark:text-slate-400">
                          <div className="flex items-center gap-1">
                            <Calendar className="w-4 h-4" />
                            {formatDate(report.created_at)}
                          </div>
                          <div className="flex items-center gap-1">
                            <FileText className="w-4 h-4" />
                            {report.paper_count || 0} papers
                          </div>
                        </div>
                        {report.summary && (
                          <p className="text-sm text-slate-600 dark:text-slate-400 max-w-2xl">
                            {report.summary}
                          </p>
                        )}
                      </div>
                      <div className="flex gap-2">
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => handleViewReport(report.id)}
                        >
                          <Eye className="w-4 h-4 mr-2" />
                          View
                        </Button>
                        <Button 
                          variant="outline" 
                          size="sm"
                          onClick={() => handleDownloadReport(report.id)}
                        >
                          <Download className="w-4 h-4 mr-2" />
                          Export
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
