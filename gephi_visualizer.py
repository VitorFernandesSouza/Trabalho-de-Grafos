import networkx as nx
from graph_lib.abstract_graph import AbstractGraph
from mining.analyzer import GraphAnalyzer
import json
import os
from typing import Dict, List, Tuple

GEPHI_GRAPHS_DIR = "gephi_graphs"

class GephiVisualizer:
    """
    Class to create graph visualizations for Gephi according to the specified metrics:
    - Top 10 users by in-degree
    - Top 10 users by PageRank
    - Top 10 users by Closeness Centrality
    - Top 5 Bridge Users
    - 5 Largest Communities Detected
    """
    
    def __init__(self, graph: AbstractGraph):
        self.graph = graph
        self.analyzer = GraphAnalyzer()
        self._ensure_output_dir()

    def _ensure_output_dir(self):
        """Create the output directory if it doesn't exist"""
        if not os.path.exists(GEPHI_GRAPHS_DIR):
            os.makedirs(GEPHI_GRAPHS_DIR)
            print(f"Created directory: {GEPHI_GRAPHS_DIR}")
        
    def create_top_indegree_graph(self, output_path: str = "gephi_top10_indegree.gexf", top_n: int = 10):
        """Create a graph visualization for top N users by in-degree"""
        print(f"Creating Top {top_n} In-degree graph...")

        # Get degree centrality metrics
        degree_metrics = self.analyzer.degree_centrality(self.graph)

        # Sort by in-degree
        sorted_by_indegree = sorted(degree_metrics.items(), key=lambda x: x[1][0], reverse=True)
        top_users = [user[0] for user in sorted_by_indegree[:top_n]]

        # Create subgraph with top users and their connections
        G = self._create_subgraph(top_users, degree_metrics)

        # Add in-degree as node attribute for visualization
        for node in G.nodes():
            if node in degree_metrics:
                G.nodes[node]['indegree'] = degree_metrics[node][0]
                G.nodes[node]['outdegree'] = degree_metrics[node][1]

        # Export to GEXF format for Gephi
        full_path = os.path.join(GEPHI_GRAPHS_DIR, output_path)
        nx.write_gexf(G, full_path)
        print(f"Graph saved to {full_path}")
        return top_users
    
    def create_top_pagerank_graph(self, output_path: str = "gephi_top10_pagerank.gexf", top_n: int = 10):
        """Create a graph visualization for top N users by PageRank"""
        print(f"Creating Top {top_n} PageRank graph...")

        # Calculate PageRank
        pagerank_scores = self.analyzer.pagerank(self.graph)

        # Sort by PageRank score
        sorted_by_pagerank = sorted(pagerank_scores.items(), key=lambda x: x[1], reverse=True)
        top_users = [user[0] for user in sorted_by_pagerank[:top_n]]

        # Create subgraph
        G = self._create_subgraph(top_users, pagerank_scores)

        # Add PageRank as node attribute
        for node in G.nodes():
            if node in pagerank_scores:
                G.nodes[node]['pagerank'] = pagerank_scores[node]

        # Export to GEXF
        full_path = os.path.join(GEPHI_GRAPHS_DIR, output_path)
        nx.write_gexf(G, full_path)
        print(f"Graph saved to {full_path}")
        return top_users
    
    def create_top_closeness_graph(self, output_path: str = "gephi_top10_closeness.gexf", top_n: int = 10):
        """Create a graph visualization for top N users by Closeness Centrality"""
        print(f"Creating Top {top_n} Closeness Centrality graph...")

        # Calculate Closeness Centrality
        closeness_scores = self.analyzer.closeness_centrality(self.graph)

        # Sort by closeness score
        sorted_by_closeness = sorted(closeness_scores.items(), key=lambda x: x[1], reverse=True)
        top_users = [user[0] for user in sorted_by_closeness[:top_n]]

        # Create subgraph
        G = self._create_subgraph(top_users, closeness_scores)

        # Add closeness as node attribute
        for node in G.nodes():
            if node in closeness_scores:
                G.nodes[node]['closeness'] = closeness_scores[node]

        # Export to GEXF
        full_path = os.path.join(GEPHI_GRAPHS_DIR, output_path)
        nx.write_gexf(G, full_path)
        print(f"Graph saved to {full_path}")
        return top_users
    
    def create_bridge_users_graph(self, output_path: str = "gephi_top5_bridges.gexf", top_n: int = 5):
        """Create a graph visualization for top N bridge users"""
        print(f"Creating Top {top_n} Bridge Users graph...")

        # First detect communities
        communities = self.analyzer.detect_communities_label_propagation(self.graph)

        # Find bridge users
        bridges = self.analyzer.analyze_bridging_ties(self.graph, communities)

        # Get top bridge users
        top_bridges = [bridge[0] for bridge in bridges[:top_n]]

        # Create graph including only bridge users and their connections to each other
        G = nx.DiGraph()

        # Add bridge users as nodes
        for bridge_user in top_bridges:
            G.add_node(bridge_user)
            G.nodes[bridge_user]['community'] = communities.get(bridge_user, -1)
            G.nodes[bridge_user]['is_bridge'] = True

        # Add edges only between bridge users
        for bridge_user in top_bridges:
            bridge_idx = self._get_vertex_index(bridge_user)
            if bridge_idx is not None:
                for neighbor_idx in self.graph.getNeighbors(bridge_idx):
                    neighbor_label = self.graph.get_vertex_label(neighbor_idx)
                    # Only add edge if neighbor is also in top bridge users
                    if neighbor_label in top_bridges:
                        G.add_edge(bridge_user, neighbor_label)

        # Export to GEXF
        full_path = os.path.join(GEPHI_GRAPHS_DIR, output_path)
        nx.write_gexf(G, full_path)
        print(f"Graph saved to {full_path}")
        return top_bridges
    
    def create_communities_graph(self, output_path: str = "gephi_top5_communities.gexf", top_n: int = 5):
        """Create a graph visualization for top N largest communities"""
        print(f"Creating Top {top_n} Largest Communities graph...")
        
        # Detect communities
        communities = self.analyzer.detect_communities_label_propagation(self.graph)
        
        # Count community sizes
        community_sizes = {}
        for user, comm_id in communities.items():
            community_sizes[comm_id] = community_sizes.get(comm_id, 0) + 1
        
        # Get top N largest communities
        sorted_communities = sorted(community_sizes.items(), key=lambda x: x[1], reverse=True)
        top_communities = [comm[0] for comm in sorted_communities[:top_n]]
        
        # Create graph with users from top communities
        G = nx.DiGraph()
        
        # Add nodes from top communities
        for user, comm_id in communities.items():
            if comm_id in top_communities:
                user_idx = self._get_vertex_index(user)
                if user_idx is not None:
                    G.add_node(user)
                    G.nodes[user]['community'] = comm_id
                    G.nodes[user]['community_rank'] = top_communities.index(comm_id) + 1
        
        # Add edges between nodes in the graph
        for node in G.nodes():
            node_idx = self._get_vertex_index(node)
            if node_idx is not None:
                for neighbor_idx in self.graph.getNeighbors(node_idx):
                    neighbor_label = self.graph.get_vertex_label(neighbor_idx)
                    if neighbor_label in G.nodes():
                        G.add_edge(node, neighbor_label)
        
        # Export to GEXF
        full_path = os.path.join(GEPHI_GRAPHS_DIR, output_path)
        nx.write_gexf(G, full_path)
        print(f"Graph saved to {full_path}")

        # Return community information
        community_info = []
        for i, comm_id in enumerate(top_communities[:top_n]):
            size = community_sizes[comm_id]
            members = [user for user, cid in communities.items() if cid == comm_id][:10]  # Sample first 10
            community_info.append({
                'community_id': comm_id,
                'rank': i + 1,
                'size': size,
                'sample_members': members
            })
        
        return community_info
    
    def _create_subgraph(self, nodes: List[str], metrics: Dict) -> nx.DiGraph:
        """Helper method to create a subgraph with specified nodes and their connections"""
        G = nx.DiGraph()
        
        # Add nodes
        for node in nodes:
            G.add_node(node)
        
        # Add edges between these nodes
        for node in nodes:
            node_idx = self._get_vertex_index(node)
            if node_idx is not None:
                for neighbor_idx in self.graph.getNeighbors(node_idx):
                    neighbor_label = self.graph.get_vertex_label(neighbor_idx)
                    if neighbor_label in nodes:
                        G.add_edge(node, neighbor_label)
        
        return G
    
    def _get_vertex_index(self, label: str) -> int:
        """Helper method to get vertex index from label"""
        for i in range(self.graph.getVertexCount()):
            if self.graph.get_vertex_label(i) == label:
                return i
        return None
    
    def create_all_visualizations(self):
        """Create all five visualizations at once"""
        results = {}
        
        # 1. Top 10 by in-degree
        results['top_indegree'] = self.create_top_indegree_graph()
        
        # 2. Top 10 by PageRank
        results['top_pagerank'] = self.create_top_pagerank_graph()
        
        # 3. Top 10 by Closeness Centrality
        results['top_closeness'] = self.create_top_closeness_graph()
        
        # 4. Top 5 Bridge Users
        results['top_bridges'] = self.create_bridge_users_graph()
        
        # 5. Top 5 Communities
        results['top_communities'] = self.create_communities_graph()
        
        # Save results summary
        summary_path = os.path.join(GEPHI_GRAPHS_DIR, 'gephi_visualization_summary.json')
        with open(summary_path, 'w') as f:
            json.dump(results, f, indent=2)

        print("\nAll visualizations created successfully!")
        print(f"Files created in '{GEPHI_GRAPHS_DIR}/' folder:")
        print("- gephi_top10_indegree.gexf")
        print("- gephi_top10_pagerank.gexf")
        print("- gephi_top10_closeness.gexf")
        print("- gephi_top5_bridges.gexf")
        print("- gephi_top5_communities.gexf")
        print("- gephi_visualization_summary.json")

        return results


if __name__ == "__main__":
    # Example usage
    print("Please use this module by importing it and providing a graph instance.")
    print("Example:")
    print("  from gephi_visualizer import GephiVisualizer")
    print("  from graph_lib.adjacency_list import AdjacencyList")
    print("  ")
    print("  # Load your graph")
    print("  graph = AdjacencyList()")
    print("  graph.load_from_csv('github_graph.csv')")
    print("  ")
    print("  # Create visualizer")
    print("  visualizer = GephiVisualizer(graph)")
    print("  ")
    print("  # Create all visualizations")
    print("  results = visualizer.create_all_visualizations()")