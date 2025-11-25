import requests
import time
from typing import Dict, List, Tuple
from graph_lib.adjacency_list import AdjacencyListGraph
from graph_lib.abstract_graph import AbstractGraph

# Constantes de Peso (Etapa 1.2)
WEIGHT_COMMENT = 2.0
WEIGHT_CLOSE   = 3.0
WEIGHT_REVIEW  = 4.0
WEIGHT_MERGE   = 5.0

class GitHubMiner:
    def __init__(self, repo_owner: str, repo_name: str, token: str = None):
        self.repo_owner = repo_owner
        self.repo_name  = repo_name
        self.headers    = {"Authorization": f"token {token}"} if token else {}
        self.base_url   = f"https://api.github.com/repos/{repo_owner}/{repo_name}"
        
        # Mapeamento Login -> ID
        self.user_map: Dict[str, int] = {}
        self.next_id = 0
        
        # Armazenamento de interações cruas: (source, target, type, weight)
        # Types: 'comment', 'close', 'review', 'merge'
        self.raw_interactions: List[Tuple[int, int, str, float]] = []

    def _get_user_id(self, login: str) -> int:
        if login not in self.user_map:
            self.user_map[login] = self.next_id
            self.next_id += 1
        return self.user_map[login]

    def _request(self, url: str, params: dict = None):
        """
        Faz requisições paginadas para a API do GitHub.
        Garante que 'page' e 'per_page' sejam enviados em TODAS as páginas
        junto com os demais parâmetros (por exemplo 'state': 'all').
        """
        data = []
        page = 1
        max_pages = 3  # limite de segurança para demonstração

        print(f"Requisitando: {url}...")
        while page <= max_pages:
            final_params = dict(params) if params else {}
            final_params["per_page"] = 100
            final_params["page"]     = page

            try:
                resp = requests.get(url, headers=self.headers, params=final_params)
                print(f"GET {resp.url} -> status {resp.status_code}")
                
                if resp.status_code == 403:
                    print("Rate Limit atingido ou erro de permissão.")
                    print(resp.text)
                    break
                if resp.status_code != 200:
                    print(f"Erro HTTP {resp.status_code} ao acessar {url}")
                    print(resp.text)
                    break

                page_data = resp.json()
                if not page_data:
                    break

                data.extend(page_data)
                page += 1
                time.sleep(0.5)  # gentileza com a API
            except Exception as e:
                print(f"Erro de conexão: {e}")
                break

        return data

    def mine_data(self):
        """
        Realiza a mineração completa: Issues, Comments, Pull Requests, Reviews.
        """
        print(f"--- Iniciando Mineração em {self.repo_owner}/{self.repo_name} ---")
        
        # 1. Buscar Issues e Pull Requests
        # Aqui uso state: 'all' para garantir retorno de issues e PRs
        issues = self._request(f"{self.base_url}/issues", {"state": "all"})
        print(f"Total de issues retornadas: {len(issues)}")

        for item in issues:
            if not item.get("user"):
                continue
            
            creator_login = item["user"]["login"]
            creator_id    = self._get_user_id(creator_login)
            number        = item["number"]
            is_pr         = "pull_request" in item
            
            # Tipo 2: fechamento de issue por outro usuário (Grafo 2)
            if (not is_pr) and item.get("state") == "closed" and item.get("closed_by"):
                closer_login = item["closed_by"]["login"]
                closer_id    = self._get_user_id(closer_login)
                if closer_id != creator_id:
                    self.raw_interactions.append((closer_id, creator_id, "close", WEIGHT_CLOSE))

            # Tipo 1: comentários em issues ou PRs (Grafo 1)
            if item.get("comments", 0) > 0:
                comments_url = item["comments_url"]
                comments = self._request(comments_url)
                for comm in comments:
                    if not comm.get("user"):
                        continue
                    comm_login = comm["user"]["login"]
                    comm_id    = self._get_user_id(comm_login)

                    if comm_id != creator_id:
                        self.raw_interactions.append((comm_id, creator_id, "comment", WEIGHT_COMMENT))

            # Tipo 3: reviews e merges em PRs (Grafo 3)
            if is_pr:
                # Reviews
                reviews_url = f"{self.base_url}/pulls/{number}/reviews"
                reviews = self._request(reviews_url)
                for rev in reviews:
                    if not rev.get("user"):
                        continue
                    reviewer_login = rev["user"]["login"]
                    reviewer_id    = self._get_user_id(reviewer_login)
                    # poderíamos checar rev["state"], mas para o TP basta contar como review
                    if reviewer_id != creator_id:
                        self.raw_interactions.append((reviewer_id, creator_id, "review", WEIGHT_REVIEW))

                # Merge
                try:
                    pr_resp = requests.get(f"{self.base_url}/pulls/{number}", headers=self.headers)
                    print(f"GET {pr_resp.url} -> status {pr_resp.status_code}")
                    if pr_resp.status_code == 200:
                        pr_data = pr_resp.json()
                        if pr_data.get("merged_by"):
                            merger_login = pr_data["merged_by"]["login"]
                            merger_id    = self._get_user_id(merger_login)
                            if merger_id != creator_id:
                                self.raw_interactions.append((merger_id, creator_id, "merge", WEIGHT_MERGE))
                except Exception as e:
                    print(f"Erro ao buscar detalhe do PR {number}: {e}")

        print(f"Mineração concluída. Total de interações capturadas: {len(self.raw_interactions)}")
        if self.raw_interactions:
            print("Primeiras 5 interações:")
            for inter in self.raw_interactions[:5]:
                print(inter)

    def _build_graph_from_interactions(self, interaction_types: List[str] = None) -> AbstractGraph:
        """
        Método genérico para construir grafo baseado em tipos de interação.
        Se interaction_types for None, usa todos (grafo integrado).
        """
        graph = AdjacencyListGraph(self.next_id)
        
        # Configurar labels
        inv_map = {v: k for k, v in self.user_map.items()}
        for uid, login in inv_map.items():
            graph.set_vertex_label(uid, login)
            
        # Soma pesos de arestas paralelas
        edge_weights: Dict[Tuple[int, int], float] = {}
        
        for u, v, type_, weight in self.raw_interactions:
            if interaction_types and type_ not in interaction_types:
                continue

            if (u, v) not in edge_weights:
                edge_weights[(u, v)] = 0.0
            edge_weights[(u, v)] += weight

        # Preencher grafo
        for (u, v), w in edge_weights.items():
            graph.addEdge(u, v)
            graph.setEdgeWeight(u, v, w)
            
        return graph

    def get_graph_1_comments(self) -> AbstractGraph:
        return self._build_graph_from_interactions(["comment"])

    def get_graph_2_issues_closed(self) -> AbstractGraph:
        return self._build_graph_from_interactions(["close"])

    def get_graph_3_reviews_merges(self) -> AbstractGraph:
        return self._build_graph_from_interactions(["review", "merge"])

    def get_integrated_graph(self) -> AbstractGraph:
        # Usa todos os tipos
        return self._build_graph_from_interactions(None)
