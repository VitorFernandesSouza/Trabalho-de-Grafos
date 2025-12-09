"""
Gerador de Tabela LaTeX com Dados de Mineração
Lê o JSON de mineração e gera estatísticas sobre os dados coletados
"""

import json
from collections import Counter
from datetime import datetime
import os

def load_mining_data(filepath: str) -> dict:
    """Carrega o JSON de mineração"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)

def analyze_mining_data(data: dict) -> dict:
    """Analisa os dados de mineração e retorna estatísticas"""
    
    # Estatísticas básicas
    num_users = len(data['user_map'])
    
    # Contar tipos de interação
    interaction_counts = {
        'comment': 0,
        'close': 0,
        'review': 0,
        'merge': 0
    }
    
    for interaction in data['raw_interactions']:
        interaction_type = interaction[2]
        if interaction_type in interaction_counts:
            interaction_counts[interaction_type] += 1
    
    return {
        'repo_owner': data['repo_owner'],
        'repo_name': data['repo_name'],
        'timestamp': data['timestamp'],
        'num_users': num_users,
        'comments': interaction_counts['comment'],
        'closes': interaction_counts['close'],
        'reviews': interaction_counts['review'],
        'merges': interaction_counts['merge'],
        'total_interactions': sum(interaction_counts.values())
    }

def generate_mining_table(stats: dict) -> str:
    """Gera tabela LaTeX com estatísticas da mineração"""
    
    # Formatar timestamp
    ts = datetime.fromisoformat(stats['timestamp'])
    formatted_date = ts.strftime('%d/%m/%Y às %H:%M')
    
    latex = r"""\begin{table}[h]
\centering
\caption{Dados Coletados na Mineração do GitHub}
\label{tab:mining_data}
\begin{tabular}{|l|r|}
\hline
\textbf{Métrica} & \textbf{Valor} \\
\hline
Repositório & """ + f"{stats['repo_owner']}/{stats['repo_name']}" + r""" \\
Data da Coleta & """ + formatted_date + r""" \\
\hline
Total de Usuários & """ + f"{stats['num_users']:,}".replace(',', '.') + r""" \\
Comentários Coletados & """ + f"{stats['comments']:,}".replace(',', '.') + r""" \\
Issues Fechadas (close) & """ + f"{stats['closes']:,}".replace(',', '.') + r""" \\
Revisões de PR (review) & """ + f"{stats['reviews']:,}".replace(',', '.') + r""" \\
Merges de PR & """ + f"{stats['merges']:,}".replace(',', '.') + r""" \\
\hline
\textbf{Total de Interações} & \textbf{""" + f"{stats['total_interactions']:,}".replace(',', '.') + r"""} \\
\hline
\end{tabular}
\end{table}
"""
    return latex

def main():
    print("=" * 60)
    print("GERADOR DE TABELA DE MINERAÇÃO")
    print("=" * 60)
    
    # Encontrar o arquivo JSON mais recente
    data_dir = "data"
    json_files = [f for f in os.listdir(data_dir) 
                  if f.startswith("github_data_") and f.endswith(".json")
                  and "analysis" not in f]
    
    if not json_files:
        print("ERRO: Nenhum arquivo de mineração encontrado em data/")
        return
    
    # Pegar o mais recente
    json_files.sort(reverse=True)
    latest_file = json_files[0]
    filepath = os.path.join(data_dir, latest_file)
    
    print(f"\nCarregando: {filepath}")
    data = load_mining_data(filepath)
    
    print("Analisando dados de mineração...")
    stats = analyze_mining_data(data)
    
    print(f"\n📊 Estatísticas:")
    print(f"   Repositório: {stats['repo_owner']}/{stats['repo_name']}")
    print(f"   Usuários: {stats['num_users']:,}")
    print(f"   Comentários: {stats['comments']:,}")
    print(f"   Issues Fechadas: {stats['closes']:,}")
    print(f"   Revisões: {stats['reviews']:,}")
    print(f"   Merges: {stats['merges']:,}")
    print(f"   Total: {stats['total_interactions']:,}")
    
    # Gerar tabela
    latex = generate_mining_table(stats)
    
    # Salvar tabela
    os.makedirs("latex_tables", exist_ok=True)
    
    filename = "latex_tables/mining_data.tex"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(latex)
    print(f"\n✅ Tabela salva em: {filename}")
    
    print("\n" + "=" * 60)
    print("PREVIEW DA TABELA")
    print("=" * 60)
    print(latex)

if __name__ == "__main__":
    main()
