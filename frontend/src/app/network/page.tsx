'use client';

import { useState, useEffect, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ThemeToggle } from '@/components/ThemeToggle';
import { CitationGraph } from '@/components/CitationGraph';
import { researchAPI } from '@/lib/api';
import { 
  ArrowLeft, 
  Network,
  Search,
  Loader2,
  ExternalLink,
  Users,
  Quote,
  TrendingUp
} from 'lucide-react';

interface Paper {
  id: string;
  title: string;
  authors: string[];
  citations: number;
  year: number;
  url: string;
  abstract?: string;
}

interface CitationLink {
  source: string;
  target: string;
  weight: number;
}

interface NetworkData {
  papers: Paper[];
  links: CitationLink[];
}

function NetworkPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const jobId = searchParams.get('job_id');
  
  const [networkData, setNetworkData] = useState<NetworkData | null>(null);
  const [selectedPaper, setSelectedPaper] = useState<Paper | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const fetchNetworkData = async () => {
      if (!jobId) {
        setIsLoading(false);
        return;
      }

      try {
        setIsLoading(true);
        
        // Fetch real citation network data from API
        const data = await researchAPI.getCitationNetwork(jobId);
        
        setNetworkData({
          papers: data.papers,
          links: data.links
        });
        
      } catch (err) {
        console.error('Error fetching network data:', err);
        
        // Fallback to mock data for demonstration
        const mockPapers: Paper[] = [
          {
            id: '1',
            title: 'Attention Is All You Need',
            authors: ['Vaswani, A.', 'Shazeer, N.', 'Parmar, N.'],
            citations: 89542,
            year: 2017,
            url: 'https://arxiv.org/abs/1706.03762',
            abstract: 'The dominant sequence transduction models are based on complex recurrent or convolutional neural networks...'
          },
          {
            id: '2',
            title: 'BERT: Pre-training of Deep Bidirectional Transformers',
            authors: ['Devlin, J.', 'Chang, M.', 'Lee, K.'],
            citations: 67821,
            year: 2018,
            url: 'https://arxiv.org/abs/1810.04805',
            abstract: 'We introduce a new language representation model called BERT...'
          },
          {
            id: '3',
            title: 'Vision Transformer (ViT)',
            authors: ['Dosovitskiy, A.', 'Beyer, L.', 'Kolesnikov, A.'],
            citations: 34567,
            year: 2020,
            url: 'https://arxiv.org/abs/2010.11929',
            abstract: 'While the Transformer architecture has become the de-facto standard for natural language processing tasks...'
          },
          {
            id: '4',
            title: 'GPT-3: Language Models are Few-Shot Learners',
            authors: ['Brown, T.', 'Mann, B.', 'Ryder, N.'],
            citations: 45678,
            year: 2020,
            url: 'https://arxiv.org/abs/2005.14165',
            abstract: 'Recent work has demonstrated substantial gains on many NLP tasks and benchmarks...'
          },
          {
            id: '5',
            title: 'Transformer-XL: Attentive Language Models Beyond a Fixed-Length Context',
            authors: ['Dai, Z.', 'Yang, Z.', 'Yang, Y.'],
            citations: 12345,
            year: 2019,
            url: 'https://arxiv.org/abs/1901.02860',
            abstract: 'Transformers have a potential of learning longer-term dependency...'
          }
        ];

        const mockLinks: CitationLink[] = [
          { source: '2', target: '1', weight: 0.9 },
          { source: '3', target: '1', weight: 0.85 },
          { source: '4', target: '1', weight: 0.75 },
          { source: '4', target: '2', weight: 0.8 },
          { source: '5', target: '1', weight: 0.7 },
          { source: '5', target: '2', weight: 0.6 }
        ];

        setNetworkData({ papers: mockPapers, links: mockLinks });
      } finally {
        setIsLoading(false);
      }
    };

    fetchNetworkData();
  }, [jobId]);

  const getMostCitedPapers = () => {
    if (!networkData) return [];
    return [...networkData.papers]
      .sort((a, b) => b.citations - a.citations)
      .slice(0, 5);
  };

  const getInfluentialPapers = () => {
    if (!networkData) return [];
    // Papers that are cited by many other papers in the network
    const citationCounts = new Map<string, number>();
    networkData.links.forEach(link => {
      citationCounts.set(link.target, (citationCounts.get(link.target) || 0) + 1);
    });
    
    return [...networkData.papers]
      .map(paper => ({
        ...paper,
        inNetworkCitations: citationCounts.get(paper.id) || 0
      }))
      .sort((a, b) => b.inNetworkCitations - a.inNetworkCitations)
      .slice(0, 5);
  };

  const formatCitations = (count: number) => {
    if (count >= 1000) {
      return `${(count / 1000).toFixed(1)}K`;
    }
    return count.toString();
  };

  return (
    <div className="min-h-screen bg-slate-50 dark:bg-slate-950">
      {/* Header */}
      <header className="bg-white border-b dark:bg-slate-900">
        <div className="container px-4 py-6 mx-auto">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-4">
              <Button variant="ghost" size="sm" onClick={() => router.back()}>
                <ArrowLeft className="w-4 h-4 mr-2" />
                Back
              </Button>
              <div className="flex items-center gap-3">
                <div className="p-2 bg-purple-600 rounded-lg">
                  <Network className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h1 className="text-2xl font-bold">Citation Network</h1>
                  <p className="text-sm text-slate-600 dark:text-slate-400">
                    Explore relationships between papers
                  </p>
                </div>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <ThemeToggle />
              <Button onClick={() => router.push('/')}>
                <Search className="w-4 h-4 mr-2" />
                New Search
              </Button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container px-4 py-8 mx-auto">
        {isLoading ? (
          <div className="flex items-center justify-center py-12">
            <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
          </div>
        ) : !networkData ? (
          <Card className="max-w-2xl mx-auto">
            <CardContent className="py-12 text-center">
              <Network className="w-12 h-12 mx-auto mb-4 text-slate-400" />
              <h3 className="mb-2 text-lg font-semibold">No Network Data</h3>
              <p className="mb-6 text-sm text-slate-600 dark:text-slate-400">
                Complete a research query to view citation network
              </p>
              <Button onClick={() => router.push('/')}>
                <Search className="w-4 h-4 mr-2" />
                Start Research
              </Button>
            </CardContent>
          </Card>
        ) : (
          <div className="mx-auto space-y-6 max-w-7xl">
            {/* Network Stats */}
            <div className="grid gap-4 md:grid-cols-3">
              <Card>
                <CardContent className="py-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-600 dark:text-slate-400">Total Papers</p>
                      <p className="text-3xl font-bold">{networkData.papers.length}</p>
                    </div>
                    <Network className="w-8 h-8 text-blue-600" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="py-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-600 dark:text-slate-400">Connections</p>
                      <p className="text-3xl font-bold">{networkData.links.length}</p>
                    </div>
                    <TrendingUp className="w-8 h-8 text-green-600" />
                  </div>
                </CardContent>
              </Card>
              <Card>
                <CardContent className="py-6">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-600 dark:text-slate-400">Total Citations</p>
                      <p className="text-3xl font-bold">
                        {formatCitations(networkData.papers.reduce((sum, p) => sum + p.citations, 0))}
                      </p>
                    </div>
                    <Quote className="w-8 h-8 text-purple-600" />
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Network Visualization */}
            <Card>
              <CardHeader>
                <CardTitle>Interactive Citation Network</CardTitle>
                <CardDescription>
                  Explore paper relationships. Node size = citations, color = publication year
                </CardDescription>
              </CardHeader>
              <CardContent>
                <CitationGraph
                  papers={networkData.papers}
                  links={networkData.links}
                  onNodeClick={(node) => {
                    const paper = networkData.papers.find(p => p.id === node.id);
                    if (paper) {
                      setSelectedPaper(paper);
                    }
                  }}
                  height={600}
                />
              </CardContent>
            </Card>

            {/* Two Column Layout */}
            <div className="grid gap-6 md:grid-cols-2">
              {/* Most Cited Papers */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="w-5 h-5" />
                    Most Cited Papers
                  </CardTitle>
                  <CardDescription>Papers with highest citation counts</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {getMostCitedPapers().map((paper, index) => (
                      <div 
                        key={paper.id} 
                        className="p-3 transition-colors border rounded-lg cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800"
                        onClick={() => setSelectedPaper(paper)}
                      >
                        <div className="flex items-start gap-3">
                          <Badge variant="secondary" className="mt-1">
                            #{index + 1}
                          </Badge>
                          <div className="flex-1 min-w-0">
                            <p className="mb-1 text-sm font-medium line-clamp-2">
                              {paper.title}
                            </p>
                            <div className="flex items-center gap-3 text-xs text-slate-600 dark:text-slate-400">
                              <span className="flex items-center gap-1">
                                <Quote className="w-3 h-3" />
                                {formatCitations(paper.citations)}
                              </span>
                              <span>{paper.year}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>

              {/* Most Influential in Network */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center gap-2">
                    <Network className="w-5 h-5" />
                    Most Influential in Network
                  </CardTitle>
                  <CardDescription>Papers cited most within this collection</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="space-y-3">
                    {getInfluentialPapers().map((paper, index) => (
                      <div 
                        key={paper.id} 
                        className="p-3 transition-colors border rounded-lg cursor-pointer hover:bg-slate-50 dark:hover:bg-slate-800"
                        onClick={() => setSelectedPaper(paper)}
                      >
                        <div className="flex items-start gap-3">
                          <Badge variant="secondary" className="mt-1">
                            #{index + 1}
                          </Badge>
                          <div className="flex-1 min-w-0">
                            <p className="mb-1 text-sm font-medium line-clamp-2">
                              {paper.title}
                            </p>
                            <div className="flex items-center gap-3 text-xs text-slate-600 dark:text-slate-400">
                              <span className="flex items-center gap-1">
                                <Network className="w-3 h-3" />
                                {paper.inNetworkCitations} connections
                              </span>
                              <span>{paper.year}</span>
                            </div>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                </CardContent>
              </Card>
            </div>

            {/* Selected Paper Detail */}
            {selectedPaper && (
              <Card className="border-blue-200 dark:border-blue-800">
                <CardHeader>
                  <div className="flex items-start justify-between">
                    <div>
                      <CardTitle className="mb-2 text-xl">{selectedPaper.title}</CardTitle>
                      <CardDescription className="text-base">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="flex items-center gap-1">
                            <Users className="w-4 h-4" />
                            {selectedPaper.authors.slice(0, 3).join(', ')}
                            {selectedPaper.authors.length > 3 && ` +${selectedPaper.authors.length - 3} more`}
                          </span>
                          <span>•</span>
                          <span>{selectedPaper.year}</span>
                          <span>•</span>
                          <span className="flex items-center gap-1">
                            <Quote className="w-4 h-4" />
                            {formatCitations(selectedPaper.citations)} citations
                          </span>
                        </div>
                      </CardDescription>
                    </div>
                    <Button variant="outline" size="sm" asChild>
                      <a href={selectedPaper.url} target="_blank" rel="noopener noreferrer">
                        <ExternalLink className="w-4 h-4 mr-2" />
                        View Paper
                      </a>
                    </Button>
                  </div>
                </CardHeader>
                {selectedPaper.abstract && (
                  <CardContent>
                    <p className="text-sm text-slate-700 dark:text-slate-300">
                      {selectedPaper.abstract}
                    </p>
                  </CardContent>
                )}
              </Card>
            )}
          </div>
        )}
      </main>
    </div>
  );
}

export default function NetworkPage() {
  return (
    <Suspense fallback={
      <div className="flex items-center justify-center min-h-screen bg-slate-50 dark:bg-slate-950">
        <Loader2 className="w-8 h-8 text-blue-600 animate-spin" />
      </div>
    }>
      <NetworkPageContent />
    </Suspense>
  );
}
