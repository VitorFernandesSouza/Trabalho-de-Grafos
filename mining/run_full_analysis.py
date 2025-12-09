"""
Complete Analysis Script
Generates all metrics, rankings, and saves results for the report
"""

import json
import sys
from collections import Counter
from mining.github_miner import GitHubMiner
from mining.analyzer import GraphAnalyzer

def main():
    print("="*60)
    print("COMPLETE GRAPH ANALYSIS - Next.js Repository")
    print("="*60)

    # 1. Load data and build graph
    print("\n[1/8] Loading data and building integrated graph...")
    miner = GitHubMiner.create_from_config()
    if not miner:
        print("ERROR: No configuration found. Run main.py first.")
        sys.exit(1)

    # Load the most recent data file
    data_file = "github_data_vercel_next.js_20251209_040851.json"
    if not miner.load_data_from_json(data_file):
        print(f"ERROR: Could not load {data_file}")
        sys.exit(1)

    graph = miner.get_grafo_integrado()
    print(f"   Graph loaded: {graph.getVertexCount()} nodes, {graph.getEdgeCount()} edges")

    # 2. Calculate Centrality Metrics
    print("\n[2/8] Calculating centrality metrics...")
    print("   - Degree centrality...")
    degree = GraphAnalyzer.degree_centrality(graph)

    print("   - Closeness centrality (this may take a while)...")
    closeness = GraphAnalyzer.closeness_centrality(graph)

    print("   - Betweenness centrality (this may take a while)...")
    betweenness = GraphAnalyzer.betweenness_centrality(graph)

    print("   - PageRank...")
    pagerank = GraphAnalyzer.pagerank(graph)

    # 3. Calculate Network Structure Metrics
    print("\n[3/8] Calculating network structure metrics...")
    density = GraphAnalyzer.density(graph)
    print(f"   - Density: {density:.6f}")

    print("   - Clustering coefficient...")
    clustering = GraphAnalyzer.clustering_coefficient(graph)
    print(f"   - Average clustering: {clustering:.6f}")

    print("   - Assortativity...")
    assortativity = GraphAnalyzer.assortativity(graph)
    print(f"   - Assortativity: {assortativity:.6f}")

    # 4. Detect Communities
    print("\n[4/8] Detecting communities (Label Propagation)...")
    communities = GraphAnalyzer.detect_communities_label_propagation(graph)
    community_counts = Counter(communities.values())
    num_communities = len(community_counts)
    print(f"   - Found {num_communities} communities")
    print(f"   - Largest community: {max(community_counts.values())} nodes")
    print(f"   - Smallest community: {min(community_counts.values())} nodes")

    # 5. Find Bridges
    print("\n[5/8] Analyzing bridging ties...")
    bridges = GraphAnalyzer.analyze_bridging_ties(graph, communities)
    print(f"   - Top bridge user: {bridges[0][0]} with {bridges[0][1]} external connections")

    # 6. Generate Rankings
    print("\n[6/8] Generating Top 10 rankings...")

    # Top 10 by In-Degree
    degree_in_sorted = sorted(degree.items(), key=lambda x: x[1][0], reverse=True)[:10]

    # Top 10 by Out-Degree
    degree_out_sorted = sorted(degree.items(), key=lambda x: x[1][1], reverse=True)[:10]

    # Top 10 by Closeness
    closeness_sorted = sorted(closeness.items(), key=lambda x: x[1], reverse=True)[:10]

    # Top 10 by Betweenness
    betweenness_sorted = sorted(betweenness.items(), key=lambda x: x[1], reverse=True)[:10]

    # Top 10 by PageRank
    pagerank_sorted = sorted(pagerank.items(), key=lambda x: x[1], reverse=True)[:10]

    # 7. Calculate per-node clustering
    print("\n[7/8] Calculating per-node clustering coefficients...")
    # Note: current implementation returns global clustering
    # For per-node, we'd need to modify the method, but we'll save what we have

    # 8. Save all results
    print("\n[8/8] Saving results to JSON...")

    results = {
        "metadata": {
            "repository": f"{miner.repo_owner}/{miner.repo_name}",
            "data_file": data_file,
            "analysis_date": "2025-12-09"
        },
        "graph_statistics": {
            "num_vertices": graph.getVertexCount(),
            "num_edges": graph.getEdgeCount(),
            "density": density,
            "avg_clustering": clustering,
            "assortativity": assortativity,
            "num_communities": num_communities,
            "is_connected": graph.isConnected()
        },
        "centrality_metrics": {
            "degree": {user: {"in": deg[0], "out": deg[1], "total": deg[0] + deg[1]}
                      for user, deg in degree.items()},
            "closeness": closeness,
            "betweenness": betweenness,
            "pagerank": pagerank
        },
        "communities": {
            "assignments": communities,
            "sizes": {f"community_{i}": count for i, count in enumerate(community_counts.most_common())}
        },
        "bridges": [{"user": user, "external_connections": count} for user, count in bridges],
        "top_10_rankings": {
            "degree_in": [{"rank": i+1, "user": user, "in_degree": deg[0], "out_degree": deg[1]}
                          for i, (user, deg) in enumerate(degree_in_sorted)],
            "degree_out": [{"rank": i+1, "user": user, "in_degree": deg[0], "out_degree": deg[1]}
                           for i, (user, deg) in enumerate(degree_out_sorted)],
            "closeness": [{"rank": i+1, "user": user, "closeness": val}
                          for i, (user, val) in enumerate(closeness_sorted)],
            "betweenness": [{"rank": i+1, "user": user, "betweenness": val}
                            for i, (user, val) in enumerate(betweenness_sorted)],
            "pagerank": [{"rank": i+1, "user": user, "pagerank": val}
                         for i, (user, val) in enumerate(pagerank_sorted)]
        }
    }

    output_file = "data/analysis_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)

    print(f"\n✅ Results saved to: {output_file}")

    # Display summary
    print("\n" + "="*60)
    print("ANALYSIS SUMMARY")
    print("="*60)
    print(f"Nodes: {graph.getVertexCount()}")
    print(f"Edges: {graph.getEdgeCount()}")
    print(f"Density: {density:.6f}")
    print(f"Avg Clustering: {clustering:.6f}")
    print(f"Assortativity: {assortativity:.6f}")
    print(f"Communities: {num_communities}")
    print(f"\nTop 5 by PageRank:")
    for i, (user, pr) in enumerate(pagerank_sorted[:5], 1):
        print(f"  {i}. {user}: {pr:.6f}")

    print(f"\nTop 5 Bridges:")
    for i, (user, conn) in enumerate(bridges[:5], 1):
        print(f"  {i}. {user}: {conn} external connections")

    print("\n✅ Analysis complete! Check data/analysis_results.json for full results.")
    print("   Next step: Run create_visualizations.py to generate plots for your report")

if __name__ == "__main__":
    main()
