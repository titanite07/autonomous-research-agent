"""Runner CLI to build and analyze citation networks from analysis JSONs

Usage:
    python -m core.citation.analysis_runner <analyses_folder> [--out out_prefix]

Produces:
  - GraphML file: <out_prefix>_citation_graph.graphml
  - PNG preview: <out_prefix>_citation_graph.png
  - CSV top nodes: <out_prefix>_top_nodes.csv
"""
import argparse
import os
import csv
import logging

from .citation_extractor import collect_analysis_jsons_from_dir, get_paper_identifier
from .citation_graph import build_citation_graph, compute_metrics, export_graph, summarize_top_n

logger = logging.getLogger(__name__)


def main(argv=None):
    parser = argparse.ArgumentParser(description='Build and analyze citation network from analysis JSONs')
    parser.add_argument('analyses_folder', help='Folder containing paper analysis JSON files')
    parser.add_argument('--out', '-o', default='citation', help='Output prefix')
    parser.add_argument('--top', '-t', type=int, default=20, help='Top N nodes in summary')
    args = parser.parse_args(argv)

    folder = args.analyses_folder
    out = args.out
    top_n = args.top

    if not os.path.isdir(folder):
        logger.error('Folder not found: %s', folder)
        return 2

    papers = collect_analysis_jsons_from_dir(folder)
    if not papers:
        logger.error('No analysis JSON files found in %s', folder)
        return 2

    G = build_citation_graph(papers)
    metrics = compute_metrics(G)

    # exports
    graphml = f"{out}_citation_graph.graphml"
    png = f"{out}_citation_graph.png"
    export_graph(G, path_graphml=graphml, path_png=png)

    # summary csv
    summary = summarize_top_n(G, metrics, n=top_n)
    csv_path = f"{out}_top_nodes.csv"
    with open(csv_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['id', 'title', 'doi', 'pagerank', 'in_degree'])
        writer.writeheader()
        for row in summary:
            writer.writerow(row)

    print(f"Graph saved: {graphml}")
    print(f"PNG preview: {png}")
    print(f"Top nodes CSV: {csv_path}")
    print(f"Nodes: {G.number_of_nodes()}, Edges: {G.number_of_edges()}")
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
