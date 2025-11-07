import os
from dotenv import load_dotenv

from src.data.github_data_collector import GitHubDataCollector
from src.analysis.graph_builder import GraphBuilder
from src.analysis.graph_analysis import GraphAnalysis
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def main() -> None:
    load_dotenv()

    repo = os.getenv("REPO_NAME", "microsoft/vscode")
    token1 = os.getenv("GITHUB_TOKEN")
    token2 = os.getenv("GITHUB_TOKEN2")  # se você estiver usando fallback de token

    logger.info(f"Iniciando coleta de dados do repositório {repo} com autenticação (token 1)...")

    try:
        collector = GitHubDataCollector(repo, token1)
        issues = collector.get_issues(state="all")
        pulls = collector.get_pull_requests(state="all")
    except SystemExit:
        logger.warning("⚠️ Token principal inválido. Tentando com GITHUB_TOKEN2...")
        collector = GitHubDataCollector(repo, token2)
        issues = collector.get_issues(state="all")
        pulls = collector.get_pull_requests(state="all")

    collector.save_data(issues, pulls)

    builder = GraphBuilder()
    graph = builder.construir()

    print("✅ Grafo integrado exportado para data/grafo_integrado.gexf")
    print("Calculando métricas...")

    metrics = GraphAnalysis(graph).compute_metrics()
    print("===== MÉTRICAS DO GRAFO INTEGRADO =====")
    for k, v in metrics.items():
        print(f"{k}: {v}")

    logger.info("Pipeline concluído com sucesso.")


if __name__ == "__main__":
    main()
