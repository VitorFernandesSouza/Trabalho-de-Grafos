import sys
import os
import signal
from mining.github_miner import GitHubMiner
from mining.analyzer import GraphAnalyzer
from graph_lib.abstract_graph import AbstractGraph

current_miner = None

def signal_handler(sig, frame):
    print("\n\nInterrupção detectada (Ctrl+C)!")
    if current_miner and current_miner.raw_interactions:
        print("Salvando dados antes de sair...")
        filename = current_miner.save_data_to_json()
        if filename:
            print(f"Dados salvos em: {filename}")
    else:
        print("Nenhum dado para salvar.")
    sys.exit(0)

def main_menu():
    global current_miner
    miner = None
    grafo_integrado = None
    grafo_list = None
    grafo_matrix = None
    grafo = {}

    signal.signal(signal.SIGINT, signal_handler)
    
    print("Verificando configuração salva...")
    miner = GitHubMiner.create_from_config()
    if miner:
        current_miner = miner
        config = GitHubMiner.load_config()
        print(f"Configuração carregada: {config['repo_owner']}/{config['repo_name']}")
    else:
        print("Nenhuma configuração encontrada.") 

    while True:
        print("\n" + "="*40)
        print(" FERRAMENTA DE ANÁLISE DE GRAFOS GITHUB")
        print("="*40)
        print("1. Configurar/Alterar Mineração (Token e Repo)")
        print("2. Executar Mineração de Dados")
        print("3. Carregar Dados Salvos (Pasta 'data')")
        print("4. Salvar Dados Manualmente")
        print("5. Construir Grafos Individuais")
        print("6. Construir Grafo Integrado")
        print("7. Construir Grafo Integrado (Lista e Matriz)")
        print("8. Analisar Grafo Integrado")
        print("9. Exportar para CSV (Nós/Arestas)")
        print("10. Exportar para GEXF (Gephi)")
        print("11. Gerar Visualizações Gephi (Top Rankings)")
        print("0. Sair")
        
        opt = input("\nEscolha uma opção: ")

        if opt == '1':
            owner = input("Dono do Repositório: ").strip()
            repo = input("Nome do Repositório: ").strip()
            token = input("GitHub Token: ").strip()
            
            if not owner or not repo:
                print("Erro: Dono e nome obrigatórios.")
                continue
            
            GitHubMiner.save_config(owner, repo, token if token else None)
            miner = GitHubMiner(owner, repo, token if token else None)
            current_miner = miner
            print("Configuração salva!")

        elif opt == '2':
            if not miner:
                print("Configure primeiro (Opção 1).")
                continue
            miner.mine_data()
            input("Pressione Enter...")

        elif opt == '3':
            if not miner:
                print("Configure primeiro (Opção 1).")
                continue
                
            saved_files = miner.list_saved_files()
            if not saved_files:
                print("Nenhum arquivo encontrado na pasta 'data'.")
                input("Pressione Enter...")
                continue
                
            print("\nArquivos salvos disponíveis:")
            for i, filename in enumerate(saved_files):
                print(f"{i + 1}. {filename}")
            
            try:
                choice = int(input("\nEscolha o arquivo (número): ")) - 1
                if 0 <= choice < len(saved_files):
                    if miner.load_data_from_json(saved_files[choice]):
                        print("Dados carregados!")
                    else:
                        print("Falha ao carregar.")
            except ValueError:
                print("Entrada inválida.")

        elif opt == '4':
            if not miner or not miner.raw_interactions:
                print("Sem dados.")
                continue
            filename = miner.save_data_to_json()
            if filename:
                print(f"Salvo em: {filename}")
            input("Pressione Enter...")

        elif opt == '5':
            if not miner or not miner.raw_interactions:
                print("Sem dados.")
                continue
            grafo['comments'] = miner.get_graph_1_comments()
            grafo['closed'] = miner.get_graph_2_issues_closed()
            grafo['reviews'] = miner.get_graph_3_reviews_merges()
            print("Grafos construídos.")
            input("Pressione Enter...")

        elif opt == '6':
            if not miner or not miner.raw_interactions:
                print("Sem dados.")
                continue
            grafo_integrado = miner.get_grafo_integrado()
            print(f"Grafo Integrado: {grafo_integrado.getVertexCount()} nós, {grafo_integrado.getEdgeCount()} arestas.")
            input("Pressione Enter...")

        elif opt == '7':
            if not miner or not miner.raw_interactions:
                print("Sem dados.")
                continue
            print("Construindo grafos com ambas implementações...")
            grafo_list, grafo_matrix = miner.get_grafo_integrado_both()
            grafo_integrado = grafo_list  # Set default to list for compatibility
            print(f"Lista de Adjacência: {grafo_list.getVertexCount()} nós, {grafo_list.getEdgeCount()} arestas.")
            print(f"Matriz de Adjacência: {grafo_matrix.getVertexCount()} nós, {grafo_matrix.getEdgeCount()} arestas.")
            input("Pressione Enter...")

        elif opt == '8':
            if not grafo_integrado:
                print("Construa o grafo integrado primeiro (Opção 6 ou 7).")
                continue
            # Executa apenas uma métrica rápida para exemplo, ou todas se preferir
            print("Calculando densidade...")
            print(f"Densidade: {GraphAnalyzer.density(grafo_integrado):.5f}")
            print("(Use o menu original para ver todas as métricas)")
            input("Pressione Enter...")

        elif opt == '9':
            if grafo_integrado:
                grafo_integrado.exportToGEPHI("grafo_integrado")
            else:
                print("Grafo não existe.")
            input("Pressione Enter...")

        elif opt == '10':
            if grafo_integrado:
                grafo_integrado.exportToGEXF("grafo_integrado")
            else:
                print("Grafo não existe.")
            input("Pressione Enter...")

        elif opt == '11':
            if not grafo_integrado:
                print("Construa o grafo integrado primeiro (Opção 6 ou 7).")
                continue
            print("\nGerando visualizações para Gephi...")
            print("Importando módulo de visualização...")
            from gephi_visualizer import GephiVisualizer

            visualizer = GephiVisualizer(grafo_integrado)
            print("Criando todas as visualizações...")
            results = visualizer.create_all_visualizations()

            print("\n=== Resumo ===")
            print(f"Top 5 Bridge Users: {', '.join(results['top_bridges'][:5])}")
            print(f"Arquivos .gexf gerados com sucesso!")
            input("\nPressione Enter...")

        elif opt == '0':
            sys.exit()

if __name__ == "__main__":
    main_menu()