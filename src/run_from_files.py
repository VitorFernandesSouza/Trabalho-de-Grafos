from src.analysis.graph_builder import GraphBuilder
from src.analysis.graph_analysis import GraphAnalysis
from src.utils.logger import setup_logger

logger = setup_logger(__name__)


def main() -> None:
    logger.info("Rodando teste com issues.json e pulls.json artificiais...")

    builder = GraphBuilder(
        issues_path="data/issues.json",
        pulls_path="data/pulls.json",
        output_path="data/grafo_teste.gexf",
    )
    graph = builder.construir()

    metrics = GraphAnalysis(graph).compute_metrics()

    print("===== METRICAS DO GRAFO DE TESTE =====")
    for k, v in metrics.items():
        print(f"{k}: {v}")


if __name__ == "__main__":
    main()
