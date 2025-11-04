'use client';

import { useEffect, useRef, useState } from 'react';
import dynamic from 'next/dynamic';

// Dynamic import to avoid SSR issues with canvas
const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), {
  ssr: false,
  loading: () => (
    <div className="flex items-center justify-center h-[500px] bg-slate-100 dark:bg-slate-900 rounded-lg">
      <p className="text-slate-600 dark:text-slate-400">Loading graph...</p>
    </div>
  ),
});

interface GraphNode {
  id: string;
  name: string;
  val: number; // Node size
  color: string;
  citations: number;
  year: number;
  authors: string[];
}

interface GraphLink {
  source: string;
  target: string;
  value: number; // Link thickness
}

interface CitationGraphProps {
  papers: Array<{
    id: string;
    title: string;
    authors: string[];
    citations: number;
    year: number;
    url: string;
  }>;
  links: Array<{
    source: string;
    target: string;
    weight: number;
  }>;
  onNodeClick?: (node: GraphNode) => void;
  height?: number;
}

export function CitationGraph({ papers, links, onNodeClick, height = 500 }: CitationGraphProps) {
  const [graphData, setGraphData] = useState<{ nodes: GraphNode[]; links: GraphLink[] }>({
    nodes: [],
    links: [],
  });
  const [mounted, setMounted] = useState(false);
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const graphRef = useRef<any>(null);

  useEffect(() => {
    // Mount flag for client-side only rendering
    const timer = setTimeout(() => setMounted(true), 0);
    return () => {
      clearTimeout(timer);
      setMounted(false);
    };
  }, []);

  useEffect(() => {
    if (!papers || papers.length === 0) return;

    // Use setTimeout to defer state update and avoid cascading renders
    const timer = setTimeout(() => {
      // Convert papers to graph nodes
      const nodes: GraphNode[] = papers.map((paper) => {
        // Node size based on citations (log scale)
        const val = Math.max(5, Math.log10(paper.citations + 1) * 5);
        
        // Color based on year
        let color = '#6366f1'; // Default indigo
        const yearsSince2015 = paper.year - 2015;
        if (yearsSince2015 < 0) {
          color = '#ef4444'; // Old papers - red
        } else if (yearsSince2015 < 3) {
          color = '#f59e0b'; // 2015-2017 - amber
        } else if (yearsSince2015 < 6) {
          color = '#10b981'; // 2018-2020 - green
        } else {
          color = '#6366f1'; // Recent papers - indigo
        }

        return {
          id: paper.id,
          name: paper.title.length > 50 ? paper.title.substring(0, 50) + '...' : paper.title,
          val,
          color,
          citations: paper.citations,
          year: paper.year,
          authors: paper.authors,
        };
      });

      // Convert links to graph links
      const graphLinks: GraphLink[] = links.map((link) => ({
        source: link.source,
        target: link.target,
        value: link.weight * 5, // Scale for visibility
      }));

      setGraphData({ nodes, links: graphLinks });
    }, 0);

    return () => clearTimeout(timer);
  }, [papers, links]);

  useEffect(() => {
    // Center graph when data loads
    if (graphRef.current && graphData.nodes.length > 0) {
      setTimeout(() => {
        graphRef.current?.zoomToFit(400);
      }, 100);
    }
  }, [graphData]);

  if (!mounted) {
    return (
      <div className="h-[500px] bg-slate-100 dark:bg-slate-900 rounded-lg flex items-center justify-center">
        <p className="text-slate-600 dark:text-slate-400">Initializing graph...</p>
      </div>
    );
  }

  if (papers.length === 0) {
    return (
      <div className="h-[500px] bg-slate-100 dark:bg-slate-900 rounded-lg flex items-center justify-center border-2 border-dashed border-slate-300 dark:border-slate-700">
        <div className="text-center">
          <p className="text-slate-600 dark:text-slate-400 mb-2">No papers available</p>
          <p className="text-sm text-slate-500 dark:text-slate-500">
            Complete a search to see the citation network
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="relative bg-slate-50 dark:bg-slate-900 rounded-lg overflow-hidden border border-slate-200 dark:border-slate-800">
      <ForceGraph2D
        ref={graphRef}
        graphData={graphData}
        height={height}
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        nodeLabel={(node: any) => {
          const n = node as GraphNode;
          return `
            <div style="background: rgba(0,0,0,0.8); color: white; padding: 8px; border-radius: 4px; font-size: 12px; max-width: 250px;">
              <strong>${n.name}</strong><br/>
              <span style="color: #94a3b8;">Citations: ${n.citations.toLocaleString()}</span><br/>
              <span style="color: #94a3b8;">Year: ${n.year}</span><br/>
              <span style="color: #94a3b8; font-size: 10px;">${n.authors.slice(0, 3).join(', ')}</span>
            </div>
          `;
        }}
        nodeVal="val"
        nodeColor="color"
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        nodeCanvasObject={(node: any, ctx: CanvasRenderingContext2D, globalScale: number) => {
          const n = node as GraphNode;
          const label = n.name;
          const fontSize = 12 / globalScale;
          ctx.font = `${fontSize}px Sans-Serif`;
          
          // Draw node circle
          ctx.beginPath();
          ctx.arc(node.x!, node.y!, n.val, 0, 2 * Math.PI, false);
          ctx.fillStyle = n.color;
          ctx.fill();
          
          // Draw label if zoomed in enough
          if (globalScale >= 1.5) {
            ctx.textAlign = 'center';
            ctx.textBaseline = 'middle';
            ctx.fillStyle = '#fff';
            ctx.fillText(label, node.x!, node.y! + n.val + fontSize + 2);
          }
        }}
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        linkWidth={(link: any) => link.value}
        linkColor={() => '#64748b'}
        linkDirectionalParticles={2}
        linkDirectionalParticleWidth={2}
        linkDirectionalParticleSpeed={0.005}
        onNodeClick={(node) => {
          if (onNodeClick) {
            onNodeClick(node as GraphNode);
          }
        }}
        cooldownTime={3000}
        d3AlphaDecay={0.02}
        d3VelocityDecay={0.3}
        backgroundColor="transparent"
      />
      
      {/* Legend */}
      <div className="absolute bottom-4 right-4 bg-white dark:bg-slate-800 p-3 rounded-lg shadow-lg border border-slate-200 dark:border-slate-700 text-xs">
        <div className="font-semibold mb-2 text-slate-900 dark:text-slate-100">Legend</div>
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-red-500"></div>
            <span className="text-slate-700 dark:text-slate-300">Pre-2015</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-amber-500"></div>
            <span className="text-slate-700 dark:text-slate-300">2015-2017</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-green-500"></div>
            <span className="text-slate-700 dark:text-slate-300">2018-2020</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 rounded-full bg-indigo-500"></div>
            <span className="text-slate-700 dark:text-slate-300">2021+</span>
          </div>
          <div className="mt-2 pt-2 border-t border-slate-200 dark:border-slate-700 text-slate-600 dark:text-slate-400">
            Node size = Citations
          </div>
        </div>
      </div>
    </div>
  );
}
