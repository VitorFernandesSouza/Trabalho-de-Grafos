import networkx as nx
from typing import Dict, Any


class GraphAnalysis:
    def __init__(self, graph: nx.Graph) -> None:
        self.graph = graph

    def compute_metrics(self) -> Dict[str, Any]:
        """Calcula métricas do grafo com tratamento para grafo vazio."""
        n = self.graph.number_of_nodes()
        m = self.graph.number_of_edges()

        if n == 0:
            return {
                "num_nodes": 0,
                "num_edges": 0,
                "density": 0.0,
                "clustering": 0.0,
                "avg_degree": 0.0,
                "largest_cc_size": 0,
                "pagerank_top5": [],
            }

        density = nx.density(self.graph)

        undirected = self.graph.to_undirected()
        try:
            clustering = nx.average_clustering(undirected)
        except ZeroDivisionError:
            clustering = 0.0

        degrees = dict(self.graph.degree())
        avg_degree = sum(degrees.values()) / n if n > 0 else 0.0

        if isinstance(self.graph, nx.DiGraph):
            components = list(nx.weakly_connected_components(self.graph))
        else:
            components = list(nx.connected_components(self.graph))

        largest_cc_size = len(max(components, key=len)) if components else 0

        pagerank_top5 = []
        if m > 0:
            pr = nx.pagerank(self.graph)
            pagerank_top5 = sorted(pr.items(), key=lambda x: x[1], reverse=True)[:5]

        return {
            "num_nodes": n,
            "num_edges": m,
            "density": density,
            "clustering": clustering,
            "avg_degree": avg_degree,
            "largest_cc_size": largest_cc_size,
            "pagerank_top5": pagerank_top5,
        }
