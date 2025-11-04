"""Citation graph construction and analysis utilities

Build a directed citation graph (edges: citing -> cited) and compute centrality metrics.
"""
from typing import Dict, List, Tuple
import networkx as nx
import logging

logger = logging.getLogger(__name__)


def build_citation_graph(papers: Dict[str, Dict]) -> nx.DiGraph:
    """Create a directed graph from papers mapping (id -> paper_data).

    Nodes use identifier strings (DOI or title). Node attributes include 'title', 'doi', 'file'.
    Edges go from citing_paper -> cited_paper.
    If a cited paper is not present in the corpus, a node is still added with minimal metadata.
    """
    G = nx.DiGraph()

    # Precompute lookup by doi and approximate title
    doi_index = {}
    title_index = {}
    for pid, data in papers.items():
        meta = data.get('metadata', {}) or {}
        doi = meta.get('doi') or meta.get('DOI')
        title = meta.get('title') or data.get('title') or pid
        node_id = pid
        G.add_node(node_id, title=title, doi=doi, file=data.get('_source_file'))
        if doi:
            doi_index[doi.lower()] = node_id
        title_index[title.lower()] = node_id

    # Add edges
    # Import extractor; support both package-relative and standalone execution
    try:
        from .citation_extractor import extract_references_from_paper
    except Exception:
        # fallback: load by file path when module executed as standalone
        import importlib.util, os, sys
        this_dir = os.path.dirname(__file__)
        path = os.path.join(this_dir, 'citation_extractor.py')
        spec = importlib.util.spec_from_file_location('citation_extractor', path)
        mod = importlib.util.module_from_spec(spec)
        sys.modules['citation_extractor'] = mod
        spec.loader.exec_module(mod)
        extract_references_from_paper = mod.extract_references_from_paper

    for citing_id, data in papers.items():
        refs = extract_references_from_paper(data)
        for r in refs:
            target_id = None
            if r.get('doi'):
                key = r['doi'].lower()
                target_id = doi_index.get(key)
            # fallback: match by title substring
            if not target_id and r.get('title'):
                t = r['title'].lower()
                # exact match first
                target_id = title_index.get(t)
                if not target_id:
                    # fuzzy substring match
                    for title_k, nodeid in title_index.items():
                        if t in title_k or title_k in t:
                            target_id = nodeid
                            break
            # if still not found, create a new node with raw info
            if not target_id:
                # create synthetic id using raw text (truncated)
                synthetic = r.get('doi') or (r.get('title') or r.get('raw'))[:200]
                target_id = synthetic
                if not G.has_node(target_id):
                    G.add_node(target_id, title=r.get('title') or r.get('raw'), doi=r.get('doi'))
            # add edge citing->target
            G.add_edge(citing_id, target_id)

    logger.info(f"Built graph: {G.number_of_nodes()} nodes, {G.number_of_edges()} edges")
    return G


def compute_metrics(G: nx.DiGraph) -> Dict[str, Dict]:
    """Compute centrality metrics and citation counts.

    Returns a dict with keys: 'pagerank', 'betweenness', 'in_degree' mapping node->value
    """
    metrics = {}
    try:
        pr = nx.pagerank(G)
    except Exception:
        pr = {n: 0.0 for n in G.nodes}
    bc = nx.betweenness_centrality(G)
    in_deg = dict(G.in_degree())

    metrics['pagerank'] = pr
    metrics['betweenness'] = bc
    metrics['in_degree'] = in_deg
    return metrics


def top_n_by_metric(metrics: Dict[str, Dict], metric: str, n: int = 10) -> List[Tuple[str, float]]:
    """Return top-n nodes by given metric name present in metrics dict."""
    m = metrics.get(metric, {})
    items = sorted(m.items(), key=lambda kv: kv[1], reverse=True)
    return items[:n]


def export_graph(G: nx.DiGraph, path_graphml: str = None, path_png: str = None) -> None:
    """Export graph as GraphML and optional PNG visualization (small graphs only).

    GraphML preserves node attributes.
    """
    import os
    if path_graphml:
        nx.write_graphml(G, path_graphml)
        logger.info(f"Saved GraphML to {path_graphml}")
    if path_png:
        try:
            import matplotlib.pyplot as plt
            plt.figure(figsize=(10, 8))
            pos = nx.spring_layout(G, seed=42)
            nx.draw_networkx_nodes(G, pos, node_size=50)
            nx.draw_networkx_edges(G, pos, alpha=0.3)
            nx.draw_networkx_labels(G, pos, font_size=6)
            plt.axis('off')
            plt.tight_layout()
            plt.savefig(path_png, dpi=150)
            plt.close()
            logger.info(f"Saved graph image to {path_png}")
        except Exception as e:
            logger.warning(f"Failed to render PNG: {e}")


def summarize_top_n(G: nx.DiGraph, metrics: Dict[str, Dict], n: int = 10) -> List[Dict]:
    """Return a summary list of top-n nodes by PageRank with basic metadata."""
    pr = metrics.get('pagerank', {})
    items = sorted(pr.items(), key=lambda kv: kv[1], reverse=True)[:n]
    summary = []
    for node_id, score in items:
        node = G.nodes.get(node_id, {})
        summary.append({
            'id': node_id,
            'title': node.get('title'),
            'doi': node.get('doi'),
            'pagerank': score,
            'in_degree': metrics.get('in_degree', {}).get(node_id, 0)
        })
    return summary
