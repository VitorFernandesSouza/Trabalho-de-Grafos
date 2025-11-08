import os
import json
from typing import List, Dict

import requests
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class GitHubDataCollector:
    """
    Coleta dados de issues, pull requests, comentários e reviews
    de um repositório público do GitHub.

    Isso permite construir:
      - Grafo 1: comentários em issues ou pull requests
      - Grafo 2: fechamentos de issues por outro usuário
      - Grafo 3: revisões, aprovações e merges de pull requests
    """

    def __init__(self, repo: str, token: str) -> None:
        if not repo:
            raise ValueError("Repositório não informado.")
        if not token:
            raise ValueError("Token não informado.")

        self.repo = repo
        self.token = token.strip()

        self.base_url = f"https://api.github.com/repos/{self.repo}"
        self.headers = {
            "Authorization": f"token {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "User-Agent": "Grafos-Trabalho-Vitor",
        }

    def _request(self, url: str) -> requests.Response:
        logger.info(f"Requisitando {url}")
        resp = requests.get(url, headers=self.headers, timeout=30)

        if resp.status_code == 401:
            logger.error("Token inválido ou sem permissão para este repositório.")
            raise SystemExit("Encerrando execução.")

        if resp.status_code == 403 and "rate limit" in resp.text.lower():
            logger.error("Limite de requisições atingido para este token.")
            raise SystemExit("Rate limit atingido. Tente novamente mais tarde.")

        return resp

    def _get_single_page(self, resource: str, state: str) -> List[Dict]:
        """
        Coleta uma única página de um recurso (issues ou pulls) para evitar erro 422.
        """
        url = f"{self.base_url}/{resource}?state={state}&per_page=100"
        resp = self._request(url)

        if resp.status_code == 422:
            logger.warning(
                f"422 recebido ao acessar {resource} (dataset muito grande). "
                f"Retornando lista vazia para este recurso."
            )
            return []

        resp.raise_for_status()
        data = resp.json()
        logger.info(f"{len(data)} registros retornados de {resource}.")
        return data

    # ============================================================
    # Recursos principais: issues e pull requests
    # ============================================================

    def get_issues(self, state: str = "all") -> List[Dict]:
        """
        Issues do repositório (inclui issues normais e issues de PR).
        Usadas para:
          - fechar issue (Grafo 2)
          - comentários em issues (Grafo 1)
        """
        logger.info(f"Coletando issues (state={state})...")
        return self._get_single_page("issues", state)

    def get_pull_requests(self, state: str = "all") -> List[Dict]:
        """
        Pull requests do repositório.
        Usadas para:
          - merges de PR (Grafo 3) via campo merged_by
          - comentários em PR (Grafo 1)
          - reviews em PR (Grafo 3)
        """
        logger.info(f"Coletando pull requests (state={state})...")
        return self._get_single_page("pulls", state)

    # ============================================================
    # Comentários em issues e pulls  -> Grafo 1
    # ============================================================

    def get_issue_comments_bulk(self, issues: List[Dict]) -> List[Dict]:
        """
        Coleta comentários de todas as issues informadas.
        Cada comentário recebe o campo extra "issue_number".
        """
        all_comments: List[Dict] = []

        for issue in issues:
            number = issue.get("number")
            if number is None:
                continue

            url = f"{self.base_url}/issues/{number}/comments?per_page=100"
            resp = self._request(url)

            if resp.status_code == 422:
                logger.warning(
                    f"422 ao buscar comentários da issue {number}. Ignorando."
                )
                continue

            resp.raise_for_status()
            comments = resp.json()

            for c in comments:
                c["issue_number"] = number

            logger.info(
                f"Issue {number}: {len(comments)} comentários coletados."
            )
            all_comments.extend(comments)

        logger.info(
            f"Total de comentários em issues coletados: {len(all_comments)}"
        )
        return all_comments

    def get_pull_comments_bulk(self, pulls: List[Dict]) -> List[Dict]:
        """
        Coleta comentários de revisão de código em todas as PRs.
        Cada comentário recebe o campo extra "pull_number".
        """
        all_comments: List[Dict] = []

        for pr in pulls:
            number = pr.get("number")
            if number is None:
                continue

            url = f"{self.base_url}/pulls/{number}/comments?per_page=100"
            resp = self._request(url)

            if resp.status_code == 422:
                logger.warning(
                    f"422 ao buscar comentários da PR {number}. Ignorando."
                )
                continue

            resp.raise_for_status()
            comments = resp.json()

            for c in comments:
                c["pull_number"] = number

            logger.info(
                f"Pull request {number}: {len(comments)} comentários coletados."
            )
            all_comments.extend(comments)

        logger.info(
            f"Total de comentários em pull requests coletados: {len(all_comments)}"
        )
        return all_comments

    # ============================================================
    # Reviews de pull requests  -> Grafo 3
    # ============================================================

    def get_pull_reviews_bulk(self, pulls: List[Dict]) -> List[Dict]:
        """
        Coleta reviews de todas as PRs informadas.
        Cada review recebe o campo extra "pull_number".
        Usado no Grafo 3 como arestas de revisão/aprovação.
        """
        all_reviews: List[Dict] = []

        for pr in pulls:
            number = pr.get("number")
            if number is None:
                continue

            url = f"{self.base_url}/pulls/{number}/reviews?per_page=100"
            resp = self._request(url)

            if resp.status_code == 422:
                logger.warning(
                    f"422 ao buscar reviews da PR {number}. Ignorando."
                )
                continue

            resp.raise_for_status()
            reviews = resp.json()

            for r in reviews:
                r["pull_number"] = number

            logger.info(
                f"Pull request {number}: {len(reviews)} reviews coletados."
            )
            all_reviews.extend(reviews)

        logger.info(
            f"Total de reviews de pull requests coletados: {len(all_reviews)}"
        )
        return all_reviews

    # ============================================================
    # Salvamento em disco
    # ============================================================

    def save_data(
        self,
        issues: List[Dict],
        pulls: List[Dict],
        issue_comments: List[Dict],
        pull_comments: List[Dict],
        pull_reviews: List[Dict],
        output_dir: str = "data",
    ) -> None:
        """
        Salva todos os dados em arquivos JSON para uso posterior na construção dos grafos.
        """
        logger.info("Salvando dados em arquivos JSON...")

        os.makedirs(output_dir, exist_ok=True)

        with open(os.path.join(output_dir, "issues.json"), "w", encoding="utf-8") as f:
            json.dump(issues, f, indent=2)

        with open(os.path.join(output_dir, "pulls.json"), "w", encoding="utf-8") as f:
            json.dump(pulls, f, indent=2)

        with open(
            os.path.join(output_dir, "issue_comments.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(issue_comments, f, indent=2)

        with open(
            os.path.join(output_dir, "pull_comments.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(pull_comments, f, indent=2)

        with open(
            os.path.join(output_dir, "pull_reviews.json"), "w", encoding="utf-8"
        ) as f:
            json.dump(pull_reviews, f, indent=2)

        logger.info("Dados salvos com sucesso em data/*.json")
