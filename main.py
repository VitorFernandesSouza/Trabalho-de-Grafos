import sys
import os
import signal
from mining.github_miner import GitHubMiner
from mining.analyzer import GraphAnalyzer
from graph_lib.abstract_graph import AbstractGraph

# Variável global para o miner (necessária para o signal handler)
current_miner = None

def signal_handler(sig, frame):
    """
    Handler para capturar Ctrl+C e salvar dados antes de sair.
    """
    print("\n\nInterrupção detectada (Ctrl+C)!")
    if current_miner and current_miner.raw_interactions:
        print("Salvando dados antes de sair...")
        filename = current_miner.save_data_to_json()
        if filename:
            print(f"Dados salvos em: {filename}")
        else:
            print("Falha ao salvar dados.")
    else:
        print("Nenhum dado para salvar.")
    print("Saindo do programa...")
    sys.exit(0)

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
    global current_miner
    miner = None
    grafo_integrado = None
    grafo = {}
    
    # Configurar handler para Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)
    
    # Tentar carregar configuração salva automaticamente
    print("Verificando configuração salva...")
    miner = GitHubMiner.create_from_config()
    if miner:
        current_miner = miner
        config = GitHubMiner.load_config()
        print(f"Configuração carregada: {config['repo_owner']}/{config['repo_name']}")
        if config.get('token'):
            print("Token GitHub configurado.")
        else:
            print("Sem token GitHub (limitações de rate limit podem aplicar).")
    else:
        print("Nenhuma configuração encontrada.") 

    while True:
        print("\n" + "="*40)
        print(" FERRAMENTA DE ANÁLISE DE GRAFOS GITHUB")
        print("="*40)
        print("1. Configurar/Alterar Mineração (Token e Repo)")
        print("2. Executar Mineração de Dados")
        print("3. Carregar Dados Salvos")
        print("4. Salvar Dados Manualmente")
        print("5. Construir Grafos Individuais (1, 2, 3)")
        print("6. Construir Grafo Integrado (Ponderado)")
        print("7. Analisar Grafo Integrado (Métricas Etapa 3)")
        print("8. Exportar para Gephi")
        print("0. Sair")
        
        # Mostrar configuração atual se existir
        if miner:
            config = GitHubMiner.load_config()
            if config:
                print(f"\nConfiguração atual: {config['repo_owner']}/{config['repo_name']}")
                print(f"Token: {'Configurado' if config.get('token') else 'Não configurado'}")
        
        opt = input("\nEscolha uma opção: ")

        if opt == '1':
            print("\n--- Configuração do GitHub ---")
            
            # Mostrar configuração atual se existir
            current_config = GitHubMiner.load_config()
            if current_config:
                print(f"Configuração atual:")
                print(f"  Repositório: {current_config['repo_owner']}/{current_config['repo_name']}")
                print(f"  Token: {'Configurado' if current_config.get('token') else 'Não configurado'}")
                print()
            
            owner = input("Dono do Repositório (ex: facebook): ").strip()
            repo = input("Nome do Repositório (ex: react): ").strip()
            token = input("GitHub Token (opcional, mas recomendado): ").strip()
            
            if not owner or not repo:
                print("Erro: Dono e nome do repositório são obrigatórios.")
                input("Pressione Enter...")
                continue
            
            # Salvar configuração
            GitHubMiner.save_config(owner, repo, token if token else None)
            
            # Criar nova instância
            miner = GitHubMiner(owner, repo, token if token else None)
            current_miner = miner  # Atualizar variável global para signal handler
            print("Configuração salva e aplicada!")

        elif opt == '2':
            if not miner:
                print("Configure primeiro (Opção 1).")
                continue
            miner.mine_data()
            input("Pressione Enter para continuar...")

        elif opt == '3':
            if not miner:
                print("Configure primeiro (Opção 1).")
                continue
                
            saved_files = miner.list_saved_files()
            if not saved_files:
                print("Nenhum arquivo salvo encontrado.")
                input("Pressione Enter...")
                continue
                
            print("\nArquivos salvos disponíveis:")
            for i, filename in enumerate(saved_files):
                print(f"{i + 1}. {filename}")
            
            try:
                choice = int(input("\nEscolha o arquivo (número): ")) - 1
                if 0 <= choice < len(saved_files):
                    if miner.load_data_from_json(saved_files[choice]):
                        print("Dados carregados com sucesso!")
                    else:
                        print("Falha ao carregar dados.")
                else:
                    print("Escolha inválida.")
            except ValueError:
                print("Entrada inválida.")
            input("Pressione Enter...")

        elif opt == '4':
            if not miner or not miner.raw_interactions:
                print("Nenhum dado para salvar. Execute a mineração primeiro.")
                continue
            
            print("Salvando dados manualmente...")
            filename = miner.save_data_to_json()
            if filename:
                print(f"Dados salvos com sucesso em: {filename}")
            input("Pressione Enter...")

        elif opt == '5':
            if not miner or not miner.raw_interactions:
                print("Nenhum dado minerado. Execute a opção 2 ou carregue dados salvos (opção 3).")
                continue
            grafo['comments'] = miner.get_graph_1_comments()
            grafo['closed'] = miner.get_graph_2_issues_closed()
            grafo['reviews'] = miner.get_graph_3_reviews_merges()
            
            print(f"Grafo 1 (Comentários): {grafo['comments'].getVertexCount()} nós, {grafo['comments'].getEdgeCount()} arestas.")
            print(f"Grafo 2 (Fechamentos): {grafo['closed'].getVertexCount()} nós, {grafo['closed'].getEdgeCount()} arestas.")
            print(f"Grafo 3 (Reviews/Merges): {grafo['reviews'].getVertexCount()} nós, {grafo['reviews'].getEdgeCount()} arestas.")
            input("Pressione Enter...")

        elif opt == '6':
            if not miner or not miner.raw_interactions:
                print("Sem dados.")
                continue
            grafo_integrado = miner.get_grafo_integrado()
            print(f"Grafo Integrado construído!")
            print(f"Nós: {grafo_integrado.getVertexCount()}")
            print(f"Arestas: {grafo_integrado.getEdgeCount()}")
            input("Pressione Enter...")

        elif opt == '7':
            if not grafo_integrado:
                print("Construa o grafo integrado primeiro (Opção 6).")
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

        elif opt == '8':
            if grafo_integrado:
                grafo_integrado.exportToGEPHI("grafo_integrado")
                print("Arquivos CSV gerados.")
            else:
                print("Grafo não existe.")

        elif opt == '0':
            sys.exit()

if __name__ == "__main__":
    main_menu()