"""Simple tests for citation graph utilities"""
from core.citation.citation_extractor import extract_references_from_paper, get_paper_identifier
from core.citation.citation_graph import build_citation_graph, compute_metrics


def test_extractor_basic():
    paper = {
        'metadata': {'title': 'Paper A', 'doi': '10.1000/xyz123'},
        'sections': {
            'references': '1. Smith J. An earlier work. 10.2000/abc;\n2. Doe J. Another work.'
        }
    }
    refs = extract_references_from_paper(paper)
    assert len(refs) >= 2
    assert any(r['doi'] for r in refs)


def test_graph_basic():
    # create two papers where A cites B
    paper_a = {'metadata': {'title': 'Paper A', 'doi': '10.1000/a1'}, 'sections': {'references': '1. Paper B. 10.1000/b1'}}
    paper_b = {'metadata': {'title': 'Paper B', 'doi': '10.1000/b1'}, 'sections': {}}
    papers = {
        '10.1000/a1': paper_a,
        '10.1000/b1': paper_b
    }
    G = build_citation_graph(papers)
    metrics = compute_metrics(G)
    assert G.number_of_nodes() >= 2
    assert ('10.1000/b1' in G)
    assert metrics['in_degree'].get('10.1000/b1', 0) >= 1


if __name__ == '__main__':
    test_extractor_basic()
    test_graph_basic()
    print('All local citation tests passed')
