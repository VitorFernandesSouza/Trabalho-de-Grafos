import os
from dotenv import load_dotenv

from src.data.github_data_collector import GitHubDataCollector
from src.analysis.graph_builder import GraphBuilder
from src.analysis.graph_analysis import GraphAnalysis
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def main() -> None:
    load_dotenv()

    repo = os.getenv("REPO_NAME")
    token1 = os.getenv("GITHUB_TOKEN")
    token2 = os.getenv("GITHUB_TOKEN2")

    logger.info(f"Iniciando coleta de dados do repositório {repo}...")

    # ============================================================
    # 1. Coleta de dados com fallback de token
    # ============================================================
    try:
        collector = GitHubDataCollector(repo, token1)
        issues = collector.get_issues(state="all")
        pulls = collector.get_pull_requests(state="all")

        issue_comments = collector.get_issue_comments_bulk(issues)
        pull_comments = collector.get_pull_comments_bulk(pulls)
        pull_reviews = collector.get_pull_reviews_bulk(pulls)

    except SystemExit:
        logger.warning("⚠️ Token principal inválido. Tentando com GITHUB_TOKEN2...")
        collector = GitHubDataCollector(repo, token2)
        issues = collector.get_issues(state="all")
        pulls = collector.get_pull_requests(state="all")

        issue_comments = collector.get_issue_comments_bulk(issues)
        pull_comments = collector.get_pull_comments_bulk(pulls)
        pull_reviews = collector.get_pull_reviews_bulk(pulls)

    # ============================================================
    # 2. Salvamento dos dados brutos em /data
    # ============================================================
    collector.save_data(
        issues=issues,
        pulls=pulls,
        issue_comments=issue_comments,
        pull_comments=pull_comments,
        pull_reviews=pull_reviews,
    )

    # ============================================================
    # 3. Construção dos grafos
    # ============================================================
    builder = GraphBuilder()
    grafos = builder.construir_todos()  # Retorna os 3 grafos + o integrado

    print("\n✅ Todos os grafos foram exportados para a pasta 'data/'")
    print("Calculando métricas de cada grafo...\n")

    # ============================================================
    # 4. Cálculo e exibição das métricas
    # ============================================================
    for nome, grafo in grafos.items():
        print(f"===== MÉTRICAS DO GRAFO {nome.upper()} =====")
        metrics = GraphAnalysis(grafo).compute_metrics()
        for k, v in metrics.items():
            print(f"{k}: {v}")
        print()

    logger.info("Pipeline concluído com sucesso.")


if __name__ == "__main__":
    main()
