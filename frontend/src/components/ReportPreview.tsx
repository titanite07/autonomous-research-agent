'use client';

import { useState } from 'react';
import { X, Download, FileText, Maximize2, Minimize2 } from 'lucide-react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';

interface ReportPreviewProps {
  analysisResult: Record<string, unknown>;
  isOpen: boolean;
  onClose: () => void;
}

export function ReportPreview({ analysisResult, isOpen, onClose }: ReportPreviewProps) {
  const [isFullscreen, setIsFullscreen] = useState(false);

  if (!isOpen) return null;

  // Generate markdown report from analysis result
  const generateMarkdownReport = (): string => {
    // Match backend API response structure
    const summaries = analysisResult.summaries as Array<Record<string, unknown>> | undefined;
    const synthesis = analysisResult.synthesis as Record<string, unknown> | undefined;
    const citations = analysisResult.citations as Record<string, unknown> | undefined;
    const knowledgeGraph = analysisResult.knowledge_graph as Record<string, unknown> | undefined;
    const totalPapers = analysisResult.total_papers_analyzed as number || summaries?.length || 0;

    let markdown = `# Research Analysis Report\n\n`;
    markdown += `*Generated on ${new Date().toLocaleDateString('en-US', { 
      year: 'numeric', 
      month: 'long', 
      day: 'numeric' 
    })}*\n\n`;
    markdown += `---\n\n`;

    // Executive Summary from synthesis
    if (synthesis?.synthesis_text) {
      markdown += `## Executive Summary\n\n`;
      markdown += `${synthesis.synthesis_text}\n\n`;
    }

    // Paper Summaries
    if (summaries && summaries.length > 0) {
      markdown += `## Paper Summaries\n\n`;
      markdown += `Total Papers Analyzed: **${summaries.length}**\n\n`;
      
      summaries.forEach((summary, idx) => {
        const title = summary.title as string || `Paper ${idx + 1}`;
        const url = summary.url as string | undefined;
        const keyFindings = summary.key_findings as string[] | undefined;
        const methodology = summary.methodology as string | undefined;
        const results = summary.results as string | undefined;
        const limitations = summary.limitations as string[] | undefined;
        const futureWork = summary.future_work as string | undefined;
        const relevanceScore = summary.relevance_score as number | undefined;
        
        markdown += `### ${idx + 1}. ${title}\n\n`;
        
        // Add URL if available
        if (url) {
          markdown += `**Source:** [View Paper](${url})\n\n`;
        }
        
        // Add relevance score
        if (relevanceScore !== undefined) {
          markdown += `**Relevance Score:** ${relevanceScore}/10\n\n`;
        }
        
        // Key Findings
        if (keyFindings && keyFindings.length > 0) {
          markdown += `#### Key Findings\n\n`;
          keyFindings.forEach(finding => {
            markdown += `- ${finding}\n`;
          });
          markdown += `\n`;
        }
        
        // Methodology
        if (methodology) {
          markdown += `#### Methodology\n\n`;
          markdown += `${methodology}\n\n`;
        }
        
        // Results
        if (results) {
          markdown += `#### Results\n\n`;
          markdown += `${results}\n\n`;
        }
        
        // Limitations
        if (limitations && limitations.length > 0) {
          markdown += `#### Limitations\n\n`;
          limitations.forEach(limitation => {
            markdown += `- ${limitation}\n`;
          });
          markdown += `\n`;
        }
        
        // Future Work
        if (futureWork) {
          markdown += `#### Future Research Directions\n\n`;
          markdown += `${futureWork}\n\n`;
        }
        
        markdown += `---\n\n`;
      });
    }

    // Synthesis & Key Findings
    if (synthesis) {
      markdown += `## Research Synthesis\n\n`;
      
      // Topic Keywords (as key concepts)
      if (synthesis.topic_keywords) {
        markdown += `### Key Topics & Concepts\n\n`;
        const keywords = synthesis.topic_keywords as Array<[string, number]>;
        // Handle both array of strings and array of tuples [keyword, score]
        const keywordStrings = keywords.map(k => {
          if (Array.isArray(k)) {
            return k[0]; // Extract keyword from [keyword, score] tuple
          }
          return String(k);
        });
        markdown += keywordStrings.slice(0, 20).join(' • ') + '\n\n';
      }

      // Paper Clusters (common themes)
      if (synthesis.paper_clusters) {
        markdown += `### Common Themes\n\n`;
        const clusters = synthesis.paper_clusters as Record<string, Array<Record<string, unknown>>>;
        Object.entries(clusters).forEach(([theme, papers]) => {
          markdown += `- **${theme}** (${papers.length} paper${papers.length > 1 ? 's' : ''})\n`;
          // Add paper titles under each theme
          papers.forEach(paper => {
            const paperTitle = paper.title as string || 'Unknown';
            markdown += `  - ${paperTitle}\n`;
          });
        });
        markdown += `\n`;
      }

      // Temporal Patterns (research evolution)
      if (synthesis.temporal_patterns) {
        markdown += `### Research Evolution\n\n`;
        const patterns = synthesis.temporal_patterns as Record<string, unknown>;
        Object.entries(patterns).forEach(([period, info]) => {
          markdown += `- **${period}:** ${JSON.stringify(info)}\n`;
        });
        markdown += `\n`;
      }
    }

    // Citations Network
    if (citations) {
      markdown += `## Citation Analysis\n\n`;
      
      if (citations.total_citations !== undefined) {
        markdown += `**Total Citations Analyzed:** ${citations.total_citations}\n\n`;
      }

      if (citations.most_cited_papers) {
        markdown += `### Most Influential Papers\n\n`;
        const mostCited = citations.most_cited_papers as Array<Record<string, unknown>>;
        mostCited.slice(0, 5).forEach((paper, idx) => {
          const title = paper.title as string || 'Unknown';
          const citationCount = paper.citation_count as number || 0;
          markdown += `${idx + 1}. **${title}** (${citationCount} citations)\n`;
        });
        markdown += `\n`;
      }

      if (citations.citation_network) {
        const network = citations.citation_network as Record<string, unknown>;
        markdown += `**Citation Network:** ${network.nodes} nodes, ${network.edges} edges\n\n`;
      }
    }

    // Knowledge Graph
    if (knowledgeGraph) {
      markdown += `## Knowledge Graph Insights\n\n`;
      
      // Entities (from synthesis topic_keywords)
      if (knowledgeGraph.entities) {
        const entities = knowledgeGraph.entities as Array<[string, number]> | string[];
        markdown += `### Key Entities & Concepts\n\n`;
        
        // Handle both array of strings and array of tuples [entity, score]
        const entityStrings = entities.map(e => {
          if (Array.isArray(e)) {
            return `${e[0]} (${(e[1] * 100).toFixed(0)}%)`; // Show keyword with relevance %
          }
          return String(e);
        });
        
        markdown += `**Total Concepts Extracted:** ${entities.length}\n\n`;
        if (entityStrings.length > 0) {
          markdown += entityStrings.slice(0, 15).map(e => `- ${e}`).join('\n') + '\n\n';
        }
      }

      // Themes
      if (knowledgeGraph.themes) {
        markdown += `### Research Themes\n\n`;
        markdown += `${knowledgeGraph.themes}\n\n`;
      }

      // Clusters
      if (knowledgeGraph.clusters) {
        const clusters = knowledgeGraph.clusters as Record<string, Array<Record<string, unknown>>>;
        markdown += `### Thematic Clusters\n\n`;
        Object.entries(clusters).forEach(([cluster, papers]) => {
          markdown += `- **${cluster}:** ${papers.length} paper${papers.length > 1 ? 's' : ''}\n`;
        });
        markdown += `\n`;
      }
      
      // Temporal Patterns
      if (knowledgeGraph.temporal_patterns) {
        const patterns = knowledgeGraph.temporal_patterns as Record<string, unknown>;
        markdown += `### Temporal Analysis\n\n`;
        if (patterns.time_span) {
          markdown += `- **Time Span:** ${patterns.time_span}\n`;
        }
        if (patterns.publication_trend) {
          markdown += `- **Publication Trend:** ${patterns.publication_trend}\n`;
        }
        markdown += `\n`;
      }
    }

    // Conclusion
    markdown += `## Conclusion\n\n`;
    markdown += `This comprehensive analysis examined **${totalPapers}** research paper${totalPapers > 1 ? 's' : ''} to identify key findings, `;
    markdown += `common themes, and research patterns. `;
    
    if (knowledgeGraph?.entities) {
      const entities = knowledgeGraph.entities as Array<[string, number]> | string[];
      markdown += `The knowledge graph extracted **${entities.length}** key concepts and their relationships. `;
    }
    
    if (citations?.total_citations !== undefined && citations.total_citations !== null) {
      const totalCitations = citations.total_citations as number;
      if (totalCitations > 0) {
        markdown += `Citation analysis revealed **${totalCitations}** citation relationships`;
        if (citations.most_cited_papers) {
          const mostCited = citations.most_cited_papers as Array<Record<string, unknown>>;
          if (mostCited.length > 0) {
            markdown += `, with the most influential papers identified`;
          }
        }
        markdown += `. `;
      } else {
        markdown += `No citation network data was available for the analyzed paper${totalPapers > 1 ? 's' : ''}. `;
      }
    }
    
    if (synthesis?.synthesis_text) {
      markdown += `\n\nThe synthesis reveals important trends in the research landscape, `;
      markdown += `highlighting areas of active development and potential future directions.`;
    }
    
    markdown += `\n\n`;
    markdown += `---\n\n`;
    markdown += `*Generated by Autonomous Research Agent v1.0.0*\n`;

    return markdown;
  };

  const markdownContent = generateMarkdownReport();

  // Download as Markdown
  const downloadMarkdown = () => {
    const blob = new Blob([markdownContent], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `research-analysis-${Date.now()}.md`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // Download as PDF (convert markdown to HTML first)
  const downloadPDF = () => {
    // Create a printable HTML version
    const htmlContent = `
      <!DOCTYPE html>
      <html>
        <head>
          <meta charset="utf-8">
          <title>Research Analysis Report</title>
          <style>
            @page {
              margin: 1in;
            }
            body {
              font-family: 'Georgia', serif;
              line-height: 1.6;
              color: #333;
              max-width: 800px;
              margin: 0 auto;
              padding: 20px;
            }
            h1 {
              color: #1a1a1a;
              border-bottom: 3px solid #22c55e;
              padding-bottom: 10px;
              margin-top: 30px;
            }
            h2 {
              color: #2a2a2a;
              border-bottom: 2px solid #10b981;
              padding-bottom: 8px;
              margin-top: 25px;
            }
            h3 {
              color: #3a3a3a;
              margin-top: 20px;
            }
            ul, ol {
              margin: 10px 0;
              padding-left: 30px;
            }
            li {
              margin: 5px 0;
            }
            code {
              background: #f4f4f4;
              padding: 2px 6px;
              border-radius: 3px;
              font-family: 'Courier New', monospace;
            }
            blockquote {
              border-left: 4px solid #22c55e;
              padding-left: 15px;
              margin: 15px 0;
              color: #555;
            }
            hr {
              border: none;
              border-top: 1px solid #ddd;
              margin: 30px 0;
            }
            .metadata {
              color: #666;
              font-style: italic;
              margin-bottom: 30px;
            }
          </style>
        </head>
        <body>
          ${markdownToHTML(markdownContent)}
        </body>
      </html>
    `;

    // Open print dialog
    const printWindow = window.open('', '_blank');
    if (printWindow) {
      printWindow.document.write(htmlContent);
      printWindow.document.close();
      printWindow.onload = () => {
        printWindow.print();
      };
    }
  };

  // Simple markdown to HTML converter (basic implementation)
  const markdownToHTML = (md: string): string => {
    let html = md;
    
    // Headers
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');
    
    // Bold
    html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
    
    // Italic
    html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
    
    // Lists - match list items and wrap in ul
    const listItems = html.match(/^\- (.*$)/gim);
    if (listItems) {
      const listHtml = listItems.map(item => item.replace(/^\- (.*$)/im, '<li>$1</li>')).join('');
      html = html.replace(/^\- .*$/gim, '').replace(/\n{2,}/, `<ul>${listHtml}</ul>`);
    }
    
    // Line breaks
    html = html.replace(/\n\n/g, '</p><p>');
    html = '<p>' + html + '</p>';
    
    // Horizontal rules
    html = html.replace(/---/g, '<hr>');
    
    return html;
  };

  return (
    <div 
      className={`fixed inset-0 z-50 flex items-center justify-center bg-black/80 backdrop-blur-sm transition-opacity ${
        isFullscreen ? 'p-0' : 'p-4'
      }`}
      onClick={onClose}
    >
      <div 
        className={`bg-black border-2 border-green-500 flex flex-col overflow-hidden transition-all ${
          isFullscreen ? 'w-full h-full' : 'w-full max-w-6xl h-[90vh]'
        }`}
        onClick={(e) => e.stopPropagation()}
      >
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-green-500 bg-green-950/20">
          <div className="flex items-center gap-3">
            <FileText className="w-5 h-5 text-green-400" />
            <h2 className="text-lg font-bold text-green-400">Research Analysis Report</h2>
            <span className="px-2 py-1 text-xs text-green-300 border border-green-500 rounded bg-green-950/30">
              PREVIEW
            </span>
          </div>
          
          <div className="flex items-center gap-2">
            {/* Download Buttons */}
            <button
              onClick={downloadMarkdown}
              className="flex items-center gap-2 px-3 py-1.5 text-sm text-blue-400 border border-blue-500 hover:bg-blue-950/30 transition-colors"
              title="Download as Markdown"
            >
              <Download className="w-4 h-4" />
              .MD
            </button>
            
            <button
              onClick={downloadPDF}
              className="flex items-center gap-2 px-3 py-1.5 text-sm text-red-400 border border-red-500 hover:bg-red-950/30 transition-colors"
              title="Download as PDF"
            >
              <Download className="w-4 h-4" />
              .PDF
            </button>
            
            {/* Fullscreen Toggle */}
            <button
              onClick={() => setIsFullscreen(!isFullscreen)}
              className="p-2 text-yellow-400 border border-yellow-500 hover:bg-yellow-950/30 transition-colors"
              title={isFullscreen ? 'Exit Fullscreen' : 'Fullscreen'}
            >
              {isFullscreen ? <Minimize2 className="w-4 h-4" /> : <Maximize2 className="w-4 h-4" />}
            </button>
            
            {/* Close Button */}
            <button
              onClick={onClose}
              className="p-2 text-red-400 border border-red-500 hover:bg-red-950/30 transition-colors"
              title="Close"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        {/* Content */}
        <div className="flex-1 p-6 overflow-y-auto text-gray-300 bg-black">
          <div className="max-w-4xl mx-auto prose prose-invert prose-green">
            <ReactMarkdown 
              remarkPlugins={[remarkGfm]}
              components={{
                h1: ({ children }) => <h1 className="text-3xl font-bold text-green-400 border-b-2 border-green-500 pb-3 mb-4">{children}</h1>,
                h2: ({ children }) => <h2 className="text-2xl font-semibold text-green-300 border-b border-green-600 pb-2 mb-3 mt-6">{children}</h2>,
                h3: ({ children }) => <h3 className="text-xl font-medium text-green-200 mb-2 mt-4">{children}</h3>,
                p: ({ children }) => <p className="mb-4 leading-relaxed text-gray-300">{children}</p>,
                ul: ({ children }) => <ul className="mb-4 ml-6 space-y-2 list-disc">{children}</ul>,
                ol: ({ children }) => <ol className="mb-4 ml-6 space-y-2 list-decimal">{children}</ol>,
                li: ({ children }) => <li className="text-gray-300">{children}</li>,
                strong: ({ children }) => <strong className="font-semibold text-green-200">{children}</strong>,
                em: ({ children }) => <em className="italic text-cyan-300">{children}</em>,
                hr: () => <hr className="my-6 border-green-700" />,
                code: ({ children }) => <code className="px-2 py-1 text-sm text-cyan-400 bg-gray-900 border border-cyan-900 rounded">{children}</code>,
              }}
            >
              {markdownContent}
            </ReactMarkdown>
          </div>
        </div>

        {/* Footer */}
        <div className="p-3 text-xs text-center text-gray-500 border-t border-green-500 bg-green-950/10">
          Generated by Autonomous Research Agent • {new Date().toLocaleString()}
        </div>
      </div>
    </div>
  );
}
