import os
import json
from typing import List, Tuple, Dict

import networkx as nx
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class GraphBuilder:
    """
    Constroi:
      - Grafo 1: comentarios em issues ou pull requests
      - Grafo 2: fechamentos de issues por outro usuario
      - Grafo 3: revisoes/aprovacoes/merges de pull requests
      - Grafo integrado: combinacao ponderada de todas as interacoes
    """

    def __init__(
        self,
        issues_path: str = "data/issues.json",
        pulls_path: str = "data/pulls.json",
        issue_comments_path: str = "data/issue_comments.json",
        pull_comments_path: str = "data/pull_comments.json",
        pull_reviews_path: str = "data/pull_reviews.json",
        output_path: str = "data/grafo_integrado.gexf",
    ) -> None:
        self.issues_path = issues_path
        self.pulls_path = pulls_path
        self.issue_comments_path = issue_comments_path
        self.pull_comments_path = pull_comments_path
        self.pull_reviews_path = pull_reviews_path

        self.output_integrado = output_path
        base_dir = os.path.dirname(output_path) or "data"
        self.output_grafo1 = os.path.join(base_dir, "grafo1_comentarios.gexf")
        self.output_grafo2 = os.path.join(base_dir, "grafo2_fechamentos.gexf")
        self.output_grafo3 = os.path.join(base_dir, "grafo3_reviews_merges.gexf")

    def _load_json(self, path: str):
        logger.info(f"Lendo arquivo {path}...")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    # ============================================================
    # Mapeamentos auxiliares
    # ============================================================

    def _map_issue_authors(self, issues) -> Dict[int, str]:
        """
        Mapa numero_da_issue -> login do autor
        """
        mapping: Dict[int, str] = {}
        for issue in issues:
            number = issue.get("number")
            author = (issue.get("user") or {}).get("login")
            if number is not None and author:
                mapping[number] = author
        return mapping

    def _map_pull_authors(self, pulls) -> Dict[int, str]:
        """
        Mapa numero_da_PR -> login do autor
        """
        mapping: Dict[int, str] = {}
        for pr in pulls:
            number = pr.get("number")
            author = (pr.get("user") or {}).get("login")
            if number is not None and author:
                mapping[number] = author
        return mapping

    # ============================================================
    # Arestas para cada tipo de relacao
    # ============================================================

    def _build_edges_from_issues(self, issues) -> List[Tuple[str, str, int]]:
        """
        Grafo 2: aresta de quem fecha a issue -> autor da issue, peso 3
        """
        edges: List[Tuple[str, str, int]] = []

        for issue in issues:
            author = (issue.get("user") or {}).get("login")
            closed_by = (issue.get("closed_by") or {}).get("login")

            if author and closed_by and closed_by != author:
                edges.append((closed_by, author, 3))

        logger.info(f"Arestas derivadas de issues (fechamento): {len(edges)}")
        return edges

    def _build_edges_from_pulls_merges(self, pulls) -> List[Tuple[str, str, int]]:
        """
        Parte do Grafo 3: merges de PR
        Aresta de quem faz o merge -> autor da PR, peso 5
        """
        edges: List[Tuple[str, str, int]] = []

        for pr in pulls:
            author = (pr.get("user") or {}).get("login")
            merged_by = (pr.get("merged_by") or {}).get("login")

            if author and merged_by and merged_by != author:
                edges.append((merged_by, author, 5))

        logger.info(f"Arestas derivadas de pull requests (merge): {len(edges)}")
        return edges

    def _build_edges_from_issue_comments(
        self,
        issue_comments,
        issue_authors: Dict[int, str],
    ) -> List[Tuple[str, str, int]]:
        """
        Grafo 1: comentarios em issues
        Aresta de quem comenta -> autor da issue, peso 2
        """
        edges: List[Tuple[str, str, int]] = []

        for c in issue_comments:
            commenter = (c.get("user") or {}).get("login")
            issue_number = c.get("issue_number")
            author = issue_authors.get(issue_number)

            if commenter and author and commenter != author:
                edges.append((commenter, author, 2))

        logger.info(
            f"Arestas derivadas de comentarios em issues: {len(edges)}"
        )
        return edges

    def _build_edges_from_pull_comments(
        self,
        pull_comments,
        pull_authors: Dict[int, str],
    ) -> List[Tuple[str, str, int]]:
        """
        Grafo 1: comentarios em pull requests
        Aresta de quem comenta -> autor da PR, peso 2
        """
        edges: List[Tuple[str, str, int]] = []

        for c in pull_comments:
            commenter = (c.get("user") or {}).get("login")
            pull_number = c.get("pull_number")
            author = pull_authors.get(pull_number)

            if commenter and author and commenter != author:
                edges.append((commenter, author, 2))

        logger.info(
            f"Arestas derivadas de comentarios em PRs: {len(edges)}"
        )
        return edges

    def _build_edges_from_pull_reviews(
        self,
        pull_reviews,
        pull_authors: Dict[int, str],
    ) -> List[Tuple[str, str, int]]:
        """
        Parte do Grafo 3: reviews de PR
        Aresta de revisor -> autor da PR, peso 4
        Opcionalmente pode filtrar por state (APPROVED, CHANGES_REQUESTED, etc.)
        """
        edges: List[Tuple[str, str, int]] = []

        for r in pull_reviews:
            reviewer = (r.get("user") or {}).get("login")
            pull_number = r.get("pull_number")
            author = pull_authors.get(pull_number)

            if reviewer and author and reviewer != author:
                # se quiser filtrar, use r.get("state")
                edges.append((reviewer, author, 4))

        logger.info(
            f"Arestas derivadas de reviews de PRs: {len(edges)}"
        )
        return edges

    # ============================================================
    # Utilitario para montar grafos a partir de lista de arestas
    # ============================================================

    def _build_graph_from_edges(
        self, edges: List[Tuple[str, str, int]]
    ) -> nx.DiGraph:
        G = nx.DiGraph()
        for u, v, w in edges:
            if G.has_edge(u, v):
                G[u][v]["weight"] += w
            else:
                G.add_edge(u, v, weight=w)
        return G

    # ============================================================
    # Pipeline de construcao
    # ============================================================

    def construir_todos(self) -> Dict[str, nx.DiGraph]:
        # Verifica existencia dos arquivos
        paths = [
            self.issues_path,
            self.pulls_path,
            self.issue_comments_path,
            self.pull_comments_path,
            self.pull_reviews_path,
        ]
        for p in paths:
            if not os.path.exists(p):
                raise FileNotFoundError(
                    f"Arquivo {p} nao encontrado. Execute a coleta antes de construir os grafos."
                )

        issues = self._load_json(self.issues_path)
        pulls = self._load_json(self.pulls_path)
        issue_comments = self._load_json(self.issue_comments_path)
        pull_comments = self._load_json(self.pull_comments_path)
        pull_reviews = self._load_json(self.pull_reviews_path)

        issue_authors = self._map_issue_authors(issues)
        pull_authors = self._map_pull_authors(pulls)

        # Grafo 1: comentarios (issues + PRs)
        edges_comentarios_issues = self._build_edges_from_issue_comments(
            issue_comments, issue_authors
        )
        edges_comentarios_pulls = self._build_edges_from_pull_comments(
            pull_comments, pull_authors
        )
        edges_comentarios: List[Tuple[str, str, int]] = []
        edges_comentarios.extend(edges_comentarios_issues)
        edges_comentarios.extend(edges_comentarios_pulls)

        # Grafo 2: fechamentos de issues
        edges_fechamentos = self._build_edges_from_issues(issues)

        # Grafo 3: reviews + merges
        edges_reviews = self._build_edges_from_pull_reviews(
            pull_reviews, pull_authors
        )
        edges_merges = self._build_edges_from_pulls_merges(pulls)
        edges_reviews_merges: List[Tuple[str, str, int]] = []
        edges_reviews_merges.extend(edges_reviews)
        edges_reviews_merges.extend(edges_merges)

        # Constroi grafos separados
        G1 = self._build_graph_from_edges(edges_comentarios)
        G2 = self._build_graph_from_edges(edges_fechamentos)
        G3 = self._build_graph_from_edges(edges_reviews_merges)

        # Grafo integrado: soma de todas as arestas
        all_edges: List[Tuple[str, str, int]] = []
        all_edges.extend(edges_comentarios)
        all_edges.extend(edges_fechamentos)
        all_edges.extend(edges_reviews_merges)

        G_integrado = self._build_graph_from_edges(all_edges)

        logger.info(
            f"Grafo 1 (comentarios): {G1.number_of_nodes()} nos, {G1.number_of_edges()} arestas."
        )
        logger.info(
            f"Grafo 2 (fechamentos): {G2.number_of_nodes()} nos, {G2.number_of_edges()} arestas."
        )
        logger.info(
            f"Grafo 3 (reviews/merges): {G3.number_of_nodes()} nos, {G3.number_of_edges()} arestas."
        )
        logger.info(
            f"Grafo integrado: {G_integrado.number_of_nodes()} nos, {G_integrado.number_of_edges()} arestas."
        )

        # Exporta tudo
        os.makedirs(os.path.dirname(self.output_integrado) or "data", exist_ok=True)
        nx.write_gexf(G1, self.output_grafo1)
        nx.write_gexf(G2, self.output_grafo2)
        nx.write_gexf(G3, self.output_grafo3)
        nx.write_gexf(G_integrado, self.output_integrado)

        logger.info(f"Grafo 1 exportado para {self.output_grafo1}")
        logger.info(f"Grafo 2 exportado para {self.output_grafo2}")
        logger.info(f"Grafo 3 exportado para {self.output_grafo3}")
        logger.info(f"Grafo integrado exportado para {self.output_integrado}")

        return {
            "comentarios": G1,
            "fechamentos": G2,
            "reviews_merges": G3,
            "integrado": G_integrado,
        }

    def construir(self) -> nx.DiGraph:
        grafos = self.construir_todos()
        return grafos["integrado"]
