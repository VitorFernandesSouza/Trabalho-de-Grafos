from gephi_visualizer import GephiVisualizer
from mining.github_miner import GitHubMiner
import os
import json

def main():
    """Main script to generate all Gephi visualizations"""
    
    print("=== Gephi Graph Visualization Generator ===")
    print("This script will create graph files for Gephi visualization")
    print("Based on the following metrics:")
    print("1. Top 10 users by in-degree")
    print("2. Top 10 users by PageRank")
    print("3. Top 10 users by Closeness Centrality")
    print("4. Top 5 Bridge Users")
    print("5. Top 5 Largest Communities\n")
    
    # Load miner from config
    print("Loading GitHub miner configuration...")
    miner = GitHubMiner.create_from_config()
    
    if not miner:
        print("Error: No miner configuration found!")
        print("Please run the main.py program first to configure and mine data.")
        return
    
    # Check if miner has data
    if not miner.raw_interactions:
        print("No data found in miner. Looking for saved data files...")
        saved_files = miner.list_saved_files()
        
        if not saved_files:
            print("Error: No saved data files found!")
            print("Please run the main.py program to mine data first.")
            return
        
        print("\nFound saved data files:")
        for i, file in enumerate(saved_files):
            print(f"{i+1}. {file}")
        
        # Load the most recent file
        print(f"\nLoading most recent data file: {saved_files[0]}")
        if not miner.load_data_from_json(saved_files[0]):
            print("Error loading data file!")
            return
    
    # Build integrated graph
    print("\nBuilding integrated graph...")
    graph = miner.get_grafo_integrado()
    
    if not graph:
        print("Error: Could not build integrated graph!")
        return
    
    print(f"Graph built successfully!")
    print(f"Number of vertices: {graph.getVertexCount()}")
    print(f"Number of edges: {graph.getEdgeCount()}\n")
    
    # Create visualizer
    visualizer = GephiVisualizer(graph)
    
    # Generate all visualizations
    print("Generating visualizations...\n")
    results = visualizer.create_all_visualizations()
    
    # Print summary of results
    print("\n=== Summary of Results ===\n")
    
    # Top 10 by In-degree
    print("Top 10 Users by In-Degree:")
    for i, user in enumerate(results['top_indegree'], 1):
        print(f"  {i}. {user}")
    
    # Top 10 by PageRank
    print("\nTop 10 Users by PageRank:")
    for i, user in enumerate(results['top_pagerank'], 1):
        print(f"  {i}. {user}")
    
    # Top 10 by Closeness Centrality
    print("\nTop 10 Users by Closeness Centrality:")
    for i, user in enumerate(results['top_closeness'], 1):
        print(f"  {i}. {user}")
    
    # Top 5 Bridge Users
    print("\nTop 5 Bridge Users:")
    for i, user in enumerate(results['top_bridges'], 1):
        print(f"  {i}. {user}")
    
    # Top 5 Communities
    print("\nTop 5 Largest Communities:")
    for comm in results['top_communities']:
        print(f"  Community {comm['rank']}: {comm['size']} members")
        print(f"    Sample members: {', '.join(comm['sample_members'][:5])}...")
    
    print("\n=== Instructions for Gephi ===")
    print("\n1. Open Gephi")
    print("2. Go to File > Open and select one of the .gexf files")
    print("3. In the Overview tab:")
    print("   - Use ForceAtlas 2 layout for better visualization")
    print("   - Adjust node size based on the relevant metric (in-degree, PageRank, etc.)")
    print("   - Color nodes by community (for community visualization)")
    print("4. In the Preview tab:")
    print("   - Adjust settings for better visualization")
    print("   - Export as PNG or PDF\n")
    
    print("All visualizations have been created successfully!")


if __name__ == "__main__":
    main()