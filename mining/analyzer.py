import math
import random
from typing import Dict, List, Tuple
from graph_lib.abstract_graph import AbstractGraph

class GraphAnalyzer:
    """
    Implementação dos algoritmos e métricas da Etapa 3.
    """

    # --- Métricas de Centralidade ---

    @staticmethod
    def degree_centrality(graph: AbstractGraph) -> Dict[str, Tuple[int, int]]:
        """Retorna {label: (in_degree, out_degree)}"""
        metrics = {}
        for i in range(graph.getVertexCount()):
            label = graph.get_vertex_label(i)
            metrics[label] = (graph.getVertexInDegree(i), graph.getVertexOutDegree(i))
        return metrics

    @staticmethod
    def closeness_centrality(graph: AbstractGraph) -> Dict[str, float]:
        """
        Calcula a proximidade (Closeness).
        C(u) = (N - 1) / Sum(dist(u, v))
        Para grafos desconexos, usa a fórmula de Wasserman e Faust.
        """
        n = graph.getVertexCount()
        closeness = {}
        
        for s in range(n):
            # BFS para calcular distâncias curtas a partir de s
            distances = {s: 0}
            queue = [s]
            while queue:
                u = queue.pop(0)
                for v in graph.getNeighbors(u):
                    if v not in distances:
                        distances[v] = distances[u] + 1
                        queue.append(v)
            
            total_dist = sum(distances.values())
            reachable = len(distances) - 1 # remove self
            
            if total_dist > 0 and reachable > 0:
                # Fórmula ajustada para grafos desconexos
                val = (reachable / (n - 1)) * (reachable / total_dist)
            else:
                val = 0.0
            
            closeness[graph.get_vertex_label(s)] = val
            
        return closeness

    @staticmethod
    def betweenness_centrality(graph: AbstractGraph) -> Dict[str, float]:
        """
        Implementação simplificada do algoritmo de Brandes para Betweenness.
        """
        n = graph.getVertexCount()
        cb = {v: 0.0 for v in range(n)}
        
        for s in range(n):
            # 1. Single-source shortest-paths (BFS)
            S = []
            P = {w: [] for w in range(n)}
            sigma = {w: 0.0 for w in range(n)}; sigma[s] = 1.0
            d = {w: -1 for w in range(n)}; d[s] = 0
            Q = [s]
            
            while Q:
                v = Q.pop(0)
                S.append(v)
                for w in graph.getNeighbors(v):
                    # Path discovery
                    if d[w] < 0:
                        Q.append(w)
                        d[w] = d[v] + 1
                    # Path counting
                    if d[w] == d[v] + 1:
                        sigma[w] += sigma[v]
                        P[w].append(v)
            
            # 2. Accumulation
            delta = {v: 0.0 for v in range(n)}
            while S:
                w = S.pop()
                for v in P[w]:
                    if sigma[w] > 0: # Evitar div por zero
                        delta[v] += (sigma[v] / sigma[w]) * (1 + delta[w])
                if w != s:
                    cb[w] += delta[w]
                    
        # Normalização para grafo direcionado: 1 / ((N-1)(N-2))
        norm = (n - 1) * (n - 2)
        result = {}
        for v in range(n):
            val = cb[v] / norm if norm > 0 else 0
            result[graph.get_vertex_label(v)] = val
        return result

    @staticmethod
    def pagerank(graph: AbstractGraph, d: float = 0.85, iter: int = 100) -> Dict[str, float]:
        """
        Algoritmo PageRank (Power Iteration).
        """
        n = graph.getVertexCount()
        if n == 0: return {}
        
        pr = [1.0 / n] * n
        
        # Identificar nós sem saída (sinks) para distribuir seu rank
        out_degrees = [graph.getVertexOutDegree(i) for i in range(n)]
        
        for _ in range(iter):
            new_pr = [0.0] * n
            sink_pr_sum = sum(pr[i] for i in range(n) if out_degrees[i] == 0)
            
            for i in range(n):
                # Contribuição dos nós que apontam para i
                incoming = 0.0
                # Maneira ineficiente (O(V+E)), mas funciona com a API atual
                # Idealmente teríamos getPredecessors(i)
                for candidate in range(n):
                    if graph.hasEdge(candidate, i):
                        if out_degrees[candidate] > 0:
                            incoming += pr[candidate] / out_degrees[candidate]
                
                new_pr[i] = (1 - d) / n + d * (incoming + sink_pr_sum / n)
            
            pr = new_pr

        return {graph.get_vertex_label(i): pr[i] for i in range(n)}

    # --- Métricas de Estrutura e Coesão ---

    @staticmethod
    def density(graph: AbstractGraph) -> float:
        V = graph.getVertexCount()
        E = graph.getEdgeCount()
        if V <= 1: return 0.0
        return E / (V * (V - 1))

    @staticmethod
    def clustering_coefficient(graph: AbstractGraph) -> float:
        """
        Coeficiente de Aglomeração Médio (Global).
        C_i = (nº arestas entre vizinhos) / (k_i * (k_i - 1))
        Nota: Em grafos direcionados, existem 4 tipos de triângulos.
        Simplificação comum: tratar vizinhança como não direcionada ou considerar apenas 'sucessores'.
        Aqui usaremos a definição padrão Watts-Strogatz adaptada: vizinhos totais (in + out).
        """
        n = graph.getVertexCount()
        total_cc = 0.0
        
        for i in range(n):
            neighbors = set(graph.getNeighbors(i))
            # Adicionar predecessores para visão completa de vizinhança (opcional, mas recomendado)
            for cand in range(n):
                if graph.hasEdge(cand, i): neighbors.add(cand)
            
            k = len(neighbors)
            if k < 2:
                continue
                
            links = 0
            neighbors_list = list(neighbors)
            for idx, u in enumerate(neighbors_list):
                for v in neighbors_list[idx+1:]:
                    if graph.hasEdge(u, v) or graph.hasEdge(v, u):
                        links += 1
            
            # Possíveis conexões entre k vizinhos (não direcionado para o cluster): k*(k-1)/2
            total_cc += links / (k * (k - 1) / 2)
            
        return total_cc / n if n > 0 else 0.0

    @staticmethod
    def assortativity(graph: AbstractGraph) -> float:
        """
        Assortatividade por Grau (Correlação de Pearson entre graus de nós conectados).
        Consideraremos (out_degree do source, in_degree do target).
        """
        edges = []
        for u in range(graph.getVertexCount()):
            for v in graph.getNeighbors(u):
                edges.append((graph.getVertexOutDegree(u), graph.getVertexInDegree(v)))
        
        if not edges: return 0.0
        
        x = [e[0] for e in edges]
        y = [e[1] for e in edges]
        
        # Cálculo da correlação de Pearson
        n = len(edges)
        sum_x = sum(x)
        sum_y = sum(y)
        sum_x2 = sum(i*i for i in x)
        sum_y2 = sum(i*i for i in y)
        sum_xy = sum(i*j for i, j in zip(x, y))
        
        numerator = n * sum_xy - sum_x * sum_y
        denominator = math.sqrt((n * sum_x2 - sum_x**2) * (n * sum_y2 - sum_y**2))
        
        return numerator / denominator if denominator != 0 else 0.0

    # --- Métricas de Comunidade ---

    @staticmethod
    def detect_communities_label_propagation(graph: AbstractGraph) -> Dict[str, int]:
        """
        Algoritmo de Propagação de Rótulos (Label Propagation) para detecção de comunidades.
        Retorna {label_usuario: id_comunidade}
        """
        n = graph.getVertexCount()
        # Inicialmente cada nó é sua própria comunidade
        labels = list(range(n))
        indices = list(range(n))
        
        changed = True
        iter_count = 0
        while changed and iter_count < 20:
            changed = False
            random.shuffle(indices) # Assíncrono aleatório
            
            for i in indices:
                neighbors = graph.getNeighbors(i)
                # Incluir predecessores também para coesão bidirecional
                for cand in range(n):
                    if graph.hasEdge(cand, i): neighbors.append(cand)
                
                if not neighbors: continue
                
                # Encontrar label mais frequente na vizinhança
                neighbor_labels = [labels[v] for v in neighbors]
                freq = {}
                for l in neighbor_labels:
                    freq[l] = freq.get(l, 0) + 1
                
                max_freq = max(freq.values())
                candidates = [l for l, f in freq.items() if f == max_freq]
                new_label = random.choice(candidates)
                
                if labels[i] != new_label:
                    labels[i] = new_label
                    changed = True
            iter_count += 1
            
        return {graph.get_vertex_label(i): labels[i] for i in range(n)}

    @staticmethod
    def analyze_bridging_ties(graph: AbstractGraph, communities: Dict[str, int]):
        """
        Identifica usuários que conectam comunidades diferentes (Bridging Ties).
        Usuários com arestas conectando nós de labels diferentes.
        """
        bridges = []
        n = graph.getVertexCount()
        
        for u in range(n):
            u_label = graph.get_vertex_label(u)
            if u_label not in communities: continue
            u_comm = communities[u_label]
            
            connections_outside = 0
            for v in graph.getNeighbors(u):
                v_label = graph.get_vertex_label(v)
                if communities.get(v_label) != u_comm:
                    connections_outside += 1
            
            if connections_outside > 0:
                bridges.append((u_label, connections_outside))
        
        # Retorna os top 5 pontes
        bridges.sort(key=lambda x: x[1], reverse=True)
        return bridges[:5]