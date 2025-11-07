import os
import json
from typing import List, Tuple

import networkx as nx
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class GraphBuilder:
    """
    Lê issues.json e pulls.json em data/, constrói o grafo integrado
    e exporta para data/grafo_integrado.gexf.
    """

    def __init__(
        self,
        issues_path: str = "data/issues.json",
        pulls_path: str = "data/pulls.json",
        output_path: str = "data/grafo_integrado.gexf",
    ) -> None:
        self.issues_path = issues_path
        self.pulls_path = pulls_path
        self.output_path = output_path

    def _load_json(self, path: str):
        logger.info(f"Lendo arquivo {path}...")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _build_edges_from_issues(self, issues) -> List[Tuple[str, str, int]]:
        """
        G2 do enunciado:
        aresta de quem fecha a issue -> autor da issue, com peso 3.
        """
        edges: List[Tuple[str, str, int]] = []

        for issue in issues:
            author = (issue.get("user") or {}).get("login")
            closed_by = (issue.get("closed_by") or {}).get("login")

            if author and closed_by and closed_by != author:
                edges.append((closed_by, author, 3))

        logger.info(f"Arestas derivadas de issues (fechamento): {len(edges)}")
        return edges

    def _build_edges_from_pulls(self, pulls) -> List[Tuple[str, str, int]]:
        """
        G3 do enunciado:
        aresta de quem faz merge da PR -> autor da PR, com peso 5.
        """
        edges: List[Tuple[str, str, int]] = []

        for pr in pulls:
            author = (pr.get("user") or {}).get("login")
            merged_by = (pr.get("merged_by") or {}).get("login")

            if author and merged_by and merged_by != author:
                edges.append((merged_by, author, 5))

        logger.info(f"Arestas derivadas de pull requests (merge): {len(edges)}")
        return edges

    def construir(self) -> nx.DiGraph:
        """
        Constrói o grafo integrado a partir das arestas coletadas
        e salva em formato .gexf.
        """
        if not os.path.exists(self.issues_path) or not os.path.exists(self.pulls_path):
            raise FileNotFoundError(
                f"Arquivos {self.issues_path} ou {self.pulls_path} não encontrados. "
                f"Execute a coleta antes de construir o grafo."
            )

        issues = self._load_json(self.issues_path)
        pulls = self._load_json(self.pulls_path)

        edges: List[Tuple[str, str, int]] = []
        edges.extend(self._build_edges_from_issues(issues))
        edges.extend(self._build_edges_from_pulls(pulls))

        G = nx.DiGraph()

        for u, v, w in edges:
            if G.has_edge(u, v):
                G[u][v]["weight"] += w
            else:
                G.add_edge(u, v, weight=w)

        logger.info(
            f"Grafo integrado construído com {G.number_of_nodes()} nós e {G.number_of_edges()} arestas."
        )

        os.makedirs(os.path.dirname(self.output_path), exist_ok=True)
        nx.write_gexf(G, self.output_path)
        logger.info(f"Grafo exportado para {self.output_path}")

        return G
