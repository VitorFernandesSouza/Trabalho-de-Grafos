import os
import json
from typing import List, Dict

import requests
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


class GitHubDataCollector:
    """Coleta issues e pull requests de um repositório do GitHub usando o token do .env."""

    def __init__(self, repo: str, token: str) -> None:
        if not repo:
            raise ValueError("Repositório não informado. Defina GITHUB_REPO no .env ou passe no código.")
        if not token:
            raise ValueError("Token não informado. Defina GITHUB_TOKEN no .env.")

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
            raise SystemExit("Encerrando execução: token não autorizado.")

        if resp.status_code == 403 and "rate limit" in resp.text.lower():
            logger.error("Limite de requisições atingido para este token.")
            raise SystemExit("Rate limit atingido. Tente novamente mais tarde.")

        return resp

    def _get_single_page(self, resource: str, state: str) -> List[Dict]:
        """
        Coleta APENAS a primeira página (até 100 registros) para evitar 422
        em repositório gigante. Nada de page=.
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

    def get_issues(self, state: str = "all") -> List[Dict]:
        logger.info(f"Coletando issues (state={state})...")
        return self._get_single_page("issues", state)

    def get_pull_requests(self, state: str = "all") -> List[Dict]:
        logger.info(f"Coletando pull requests (state={state})...")
        return self._get_single_page("pulls", state)

    def save_data(self, issues: List[Dict], pulls: List[Dict], output_dir: str = "data") -> None:
        logger.info("Salvando dados em arquivos JSON...")

        os.makedirs(output_dir, exist_ok=True)

        with open(os.path.join(output_dir, "issues.json"), "w", encoding="utf-8") as f:
            json.dump(issues, f, indent=2)

        with open(os.path.join(output_dir, "pulls.json"), "w", encoding="utf-8") as f:
            json.dump(pulls, f, indent=2)

        logger.info("Dados salvos com sucesso em data/issues.json e data/pulls.json")
