import sys
import os
from mining.github_miner import GitHubMiner
from mining.analyzer import GraphAnalyzer
from graph_lib.abstract_graph import AbstractGraph

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def print_top_metrics(metrics: dict, title: str, top_n=5):
    print(f"\n--- Top {top_n} {title} ---")
    sorted_items = sorted(metrics.items(), key=lambda x: x[1], reverse=True)
    for k, v in sorted_items[:top_n]:
        val = f"{v:.4f}" if isinstance(v, float) else v
        print(f"{k}: {val}")

# Menuzin
def main_menu():
    miner = None
    grafo_integrado = None
    grafo = {} 

    while True:
        print("\n" + "="*40)
        print(" FERRAMENTA DE ANÁLISE DE GRAFOS GITHUB")
        print("="*40)
        print("1. Configurar Mineração (Token e Repo)")
        print("2. Executar Mineração de Dados")
        print("3. Construir Grafos Individuais (1, 2, 3)")
        print("4. Construir Grafo Integrado (Ponderado)")
        print("5. Analisar Grafo Integrado (Métricas Etapa 3)")
        print("6. Exportar para Gephi")
        print("0. Sair")
        
        opt = input("\nEscolha uma opção: ")

        if opt == '1':
            owner = input("Dono do Repositório (ex: facebook): ")
            repo = input("Nome do Repositório (ex: react): ")
            token = input("GitHub Token (opcional, mas recomendado): ")
            miner = GitHubMiner(owner, repo, token if token.strip() else None)
            print("Configuração salva.")

        elif opt == '2':
            if not miner:
                print("Configure primeiro (Opção 1).")
                continue
            miner.mine_data()
            input("Pressione Enter para continuar...")

        elif opt == '3':
            if not miner or not miner.raw_interactions:
                print("Nenhum dado minerado. Execute a opção 2 antes.")
                continue
            grafo['comments'] = miner.get_graph_1_comments()
            grafo['closed'] = miner.get_graph_2_issues_closed()
            grafo['reviews'] = miner.get_graph_3_reviews_merges()
            
            print(f"Grafo 1 (Comentários): {grafo['comments'].getVertexCount()} nós, {grafo['comments'].getEdgeCount()} arestas.")
            print(f"Grafo 2 (Fechamentos): {grafo['closed'].getVertexCount()} nós, {grafo['closed'].getEdgeCount()} arestas.")
            print(f"Grafo 3 (Reviews/Merges): {grafo['reviews'].getVertexCount()} nós, {grafo['reviews'].getEdgeCount()} arestas.")
            input("Pressione Enter...")

        elif opt == '4':
            if not miner or not miner.raw_interactions:
                print("Sem dados.")
                continue
            grafo_integrado = miner.get_grafo_integrado()
            print(f"Grafo Integrado construído!")
            print(f"Nós: {grafo_integrado.getVertexCount()}")
            print(f"Arestas: {grafo_integrado.getEdgeCount()}")
            input("Pressione Enter...")

        elif opt == '5':
            if not grafo_integrado:
                print("Construa o grafo integrado primeiro (Opção 4).")
                continue
            
            g = grafo_integrado
            print("\nCALCULANDO MÉTRICAS...")
            
            dens = GraphAnalyzer.density(g)
            clust = GraphAnalyzer.clustering_coefficient(g)
            assort = GraphAnalyzer.assortativity(g)
            
            print(f"\n> Densidade: {dens:.5f}")
            print(f"> Coeficiente de Aglomeração (Global): {clust:.5f}")
            print(f"> Assortatividade: {assort:.5f}")
            
            print("\n> Calculando PageRank...")
            pr = GraphAnalyzer.pagerank(g)
            print_top_metrics(pr, "PageRank")
            
            print("\n> Calculando Betweenness (pode demorar)...")
            bw = GraphAnalyzer.betweenness_centrality(g)
            print_top_metrics(bw, "Betweenness Centrality")
            
            print("\n> Calculando Closeness...")
            cl = GraphAnalyzer.closeness_centrality(g)
            print_top_metrics(cl, "Closeness Centrality")
            
            deg = GraphAnalyzer.degree_centrality(g)
            out_deg = {k: v[1] for k, v in deg.items()}
            print_top_metrics(out_deg, "Out-Degree (Mais Ativos)")
            
            print("\n> Detectando Comunidades...")
            comm = GraphAnalyzer.detect_communities_label_propagation(g)
            num_comm = len(set(comm.values()))
            print(f"Comunidades detectadas: {num_comm}")
            
            bridges = GraphAnalyzer.analyze_bridging_ties(g, comm)
            print("\n--- Principais Pontes (Bridging Ties) ---")
            for user, count in bridges:
                print(f"Usuário {user} conecta {count} pessoas de fora do seu grupo.")
            
            input("\nPressione Enter para voltar...")

        elif opt == '6':
            if grafo_integrado:
                grafo_integrado.exportToGEPHI("grafo_integrado")
                print("Arquivos CSV gerados.")
            else:
                print("Grafo não existe.")

        elif opt == '0':
            sys.exit()

if __name__ == "__main__":
    main_menu()