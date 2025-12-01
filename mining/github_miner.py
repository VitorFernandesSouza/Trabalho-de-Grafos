import requests
import time
import json
import os
from datetime import datetime
from typing import Dict, List, Tuple
from graph_lib.adjacency_list import AdjacencyListGraph
from graph_lib.abstract_graph import AbstractGraph

# PESOS
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
        
        self.user_map: Dict[str, int] = {}
        self.next_id = 0
        
        # Types: 'comment', 'close', 'review', 'merge'
        self.raw_interactions: List[Tuple[int, int, str, float]] = []

    def _get_user_id(self, login: str) -> int:
        if login not in self.user_map:
            self.user_map[login] = self.next_id
            self.next_id += 1
        return self.user_map[login]

    def _request(self, url: str, params: dict = None):
        
        data = []
        page = 1
        max_pages = 3  # Número máximo de páginas a buscar 

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
        
        issues = self._request(f"{self.base_url}/issues", {"state": "all"})
        print(f"Total de issues retornadas: {len(issues)}")

        for item in issues:
            if not item.get("user"):
                continue
            
            creator_login = item["user"]["login"]
            creator_id    = self._get_user_id(creator_login)
            number        = item["number"]
            is_pr         = "pull_request" in item
            
            if (not is_pr) and item.get("state") == "closed" and item.get("closed_by"):
                closer_login = item["closed_by"]["login"]
                closer_id    = self._get_user_id(closer_login)
                if closer_id != creator_id:
                    self.raw_interactions.append((closer_id, creator_id, "close", WEIGHT_CLOSE))

            # Comentários em issues ou PRs
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

            # Reviews e merges em PRs
            if is_pr:
                # Reviews
                reviews_url = f"{self.base_url}/pulls/{number}/reviews"
                reviews = self._request(reviews_url)
                for rev in reviews:
                    if not rev.get("user"):
                        continue
                    reviewer_login = rev["user"]["login"]
                    reviewer_id    = self._get_user_id(reviewer_login)
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
            
            # Salvamento automático após mineração bem-sucedida
            print("\nSalvando dados automaticamente...")
            self.save_data_to_json()

    def _build_graph_from_interactions(self, interaction_types: List[str] = None) -> AbstractGraph:
        graph = AdjacencyListGraph(self.next_id)
        
        inv_map = {v: k for k, v in self.user_map.items()}
        for uid, login in inv_map.items():
            graph.set_vertex_label(uid, login)
            
        edge_weights: Dict[Tuple[int, int], float] = {}
        
        for u, v, type_, weight in self.raw_interactions:
            if interaction_types and type_ not in interaction_types:
                continue

            if (u, v) not in edge_weights:
                edge_weights[(u, v)] = 0.0
            edge_weights[(u, v)] += weight

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

    def get_grafo_integrado(self) -> AbstractGraph:
        return self._build_graph_from_interactions(None)

    def save_data_to_json(self, filename: str = None):
        """
        Salva os dados minerados em um arquivo JSON para reutilização posterior.
        """
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"github_data_{self.repo_owner}_{self.repo_name}_{timestamp}.json"
        
        data_to_save = {
            "repo_owner": self.repo_owner,
            "repo_name": self.repo_name,
            "timestamp": datetime.now().isoformat(),
            "user_map": self.user_map,
            "next_id": self.next_id,
            "raw_interactions": self.raw_interactions
        }
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data_to_save, f, indent=2, ensure_ascii=False)
            print(f"Dados salvos em: {filename}")
            return filename
        except Exception as e:
            print(f"Erro ao salvar dados: {e}")
            return None

    def load_data_from_json(self, filename: str) -> bool:
        """
        Carrega dados previamente minerados de um arquivo JSON.
        Retorna True se carregado com sucesso, False caso contrário.
        """
        try:
            if not os.path.exists(filename):
                print(f"Arquivo não encontrado: {filename}")
                return False
            
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Verificar se é o mesmo repositório
            if (data.get("repo_owner") != self.repo_owner or 
                data.get("repo_name") != self.repo_name):
                print(f"Aviso: Dados são de um repositório diferente!")
                print(f"Arquivo: {data.get('repo_owner')}/{data.get('repo_name')}")
                print(f"Atual: {self.repo_owner}/{self.repo_name}")
                response = input("Deseja carregar mesmo assim? (s/n): ")
                if response.lower() != 's':
                    return False
            
            # Carregar os dados
            self.user_map = data.get("user_map", {})
            self.next_id = data.get("next_id", 0)
            self.raw_interactions = data.get("raw_interactions", [])
            
            print(f"Dados carregados com sucesso!")
            print(f"Timestamp do arquivo: {data.get('timestamp', 'N/A')}")
            print(f"Total de interações: {len(self.raw_interactions)}")
            print(f"Total de usuários: {len(self.user_map)}")
            
            return True
            
        except Exception as e:
            print(f"Erro ao carregar dados: {e}")
            return False

    def list_saved_files(self) -> List[str]:
        """
        Lista arquivos JSON salvos no diretório atual que correspondem ao padrão de nomenclatura.
        """
        pattern = f"github_data_{self.repo_owner}_{self.repo_name}"
        files = []
        
        try:
            for filename in os.listdir('.'):
                if filename.startswith(pattern) and filename.endswith('.json'):
                    files.append(filename)
            files.sort(reverse=True)  # Mais recentes primeiro
        except Exception as e:
            print(f"Erro ao listar arquivos: {e}")
        
        return files

    @staticmethod
    def save_config(repo_owner: str, repo_name: str, token: str = None):
        """
        Salva a configuração (repositório e token) em um arquivo.
        """
        config_data = {
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "token": token,
            "last_updated": datetime.now().isoformat()
        }
        
        try:
            with open("github_config.json", 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2, ensure_ascii=False)
            print("Configuração salva em github_config.json")
            return True
        except Exception as e:
            print(f"Erro ao salvar configuração: {e}")
            return False

    @staticmethod
    def load_config():
        """
        Carrega a configuração salva do arquivo.
        Retorna um dicionário com os dados ou None se não existir/erro.
        """
        try:
            if not os.path.exists("github_config.json"):
                return None
                
            with open("github_config.json", 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            # Validar campos obrigatórios
            if not config.get("repo_owner") or not config.get("repo_name"):
                print("Arquivo de configuração inválido.")
                return None
                
            return config
        except Exception as e:
            print(f"Erro ao carregar configuração: {e}")
            return None

    @staticmethod
    def create_from_config():
        """
        Cria uma instância do GitHubMiner a partir da configuração salva.
        """
        config = GitHubMiner.load_config()
        if config:
            return GitHubMiner(
                config["repo_owner"], 
                config["repo_name"], 
                config.get("token")
            )
        return None
