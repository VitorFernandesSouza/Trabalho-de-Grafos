"""
Visualization Script
Creates all plots needed for the report
"""

import json
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter
import os

# Set style for professional-looking plots
plt.style.use('seaborn-v0_8-darkgrid')

def ensure_plots_dir():
    if not os.path.exists("plots"):
        os.makedirs("plots")

def load_results():
    with open("data/analysis_results.json", 'r', encoding='utf-8') as f:
        return json.load(f)

def plot_degree_distribution(results):
    """Plot degree distribution in log-log scale"""
    print("[1/6] Creating degree distribution plot...")

    degrees = [data["total"] for data in results["centrality_metrics"]["degree"].values()]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))

    # Linear scale
    ax1.hist(degrees, bins=50, alpha=0.7, color='steelblue', edgecolor='black')
    ax1.set_xlabel('Total Degree', fontsize=12, fontweight='bold')
    ax1.set_ylabel('Frequency', fontsize=12, fontweight='bold')
    ax1.set_title('Degree Distribution (Linear Scale)', fontsize=14, fontweight='bold')
    ax1.grid(alpha=0.3)

    # Log-log scale (to show power-law)
    degree_counts = Counter(degrees)
    degrees_sorted = sorted(degree_counts.keys())
    counts = [degree_counts[d] for d in degrees_sorted]

    ax2.loglog(degrees_sorted, counts, 'o', alpha=0.7, color='steelblue', markersize=6)
    ax2.set_xlabel('Degree (log scale)', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Frequency (log scale)', fontsize=12, fontweight='bold')
    ax2.set_title('Degree Distribution (Log-Log Scale)', fontsize=14, fontweight='bold')
    ax2.grid(True, alpha=0.3, which="both", ls="-")

    plt.tight_layout()
    plt.savefig('plots/degree_distribution.png', dpi=300, bbox_inches='tight')
    print("   ✅ Saved: plots/degree_distribution.png")
    plt.close()

def plot_pagerank_vs_degree(results):
    """Scatter plot of PageRank vs Degree"""
    print("[2/6] Creating PageRank vs Degree scatter plot...")

    users = list(results["centrality_metrics"]["degree"].keys())
    in_degrees = [results["centrality_metrics"]["degree"][u]["in"] for u in users]
    pageranks = [results["centrality_metrics"]["pagerank"][u] for u in users]

    # Get top 5 PageRank users for annotation
    pr_sorted = sorted(zip(users, pageranks, in_degrees), key=lambda x: x[1], reverse=True)

    plt.figure(figsize=(10, 7))
    plt.scatter(in_degrees, pageranks, alpha=0.5, s=50, color='steelblue', edgecolors='darkblue', linewidth=0.5)

    # Annotate top 5
    for i, (user, pr, deg) in enumerate(pr_sorted[:5]):
        plt.annotate(user, (deg, pr), fontsize=9, alpha=0.9,
                     xytext=(5, 5), textcoords='offset points',
                     bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.5))

    plt.xlabel('In-Degree', fontsize=12, fontweight='bold')
    plt.ylabel('PageRank', fontsize=12, fontweight='bold')
    plt.title('PageRank vs In-Degree\n(Top 5 users annotated)', fontsize=14, fontweight='bold')
    plt.grid(alpha=0.3)

    plt.tight_layout()
    plt.savefig('plots/pagerank_vs_degree.png', dpi=300, bbox_inches='tight')
    print("   ✅ Saved: plots/pagerank_vs_degree.png")
    plt.close()

def plot_centrality_comparison(results):
    """Compare different centrality metrics for top users"""
    print("[3/6] Creating centrality comparison plot...")

    top_10_pr = results["top_10_rankings"]["pagerank"]
    top_users = [entry["user"] for entry in top_10_pr]

    # Get metrics for these users
    degrees = [results["centrality_metrics"]["degree"][u]["total"] for u in top_users]
    closeness = [results["centrality_metrics"]["closeness"][u] for u in top_users]
    betweenness = [results["centrality_metrics"]["betweenness"][u] for u in top_users]
    pageranks = [results["centrality_metrics"]["pagerank"][u] for u in top_users]

    # Normalize to 0-1 for comparison
    def normalize(vals):
        min_v, max_v = min(vals), max(vals)
        if max_v == min_v:
            return [0.5] * len(vals)
        return [(v - min_v) / (max_v - min_v) for v in vals]

    degrees_norm = normalize(degrees)
    closeness_norm = normalize(closeness)
    betweenness_norm = normalize(betweenness)
    pageranks_norm = normalize(pageranks)

    x = np.arange(len(top_users))
    width = 0.2

    fig, ax = plt.subplots(figsize=(14, 6))
    ax.bar(x - 1.5*width, degrees_norm, width, label='Degree', alpha=0.8)
    ax.bar(x - 0.5*width, closeness_norm, width, label='Closeness', alpha=0.8)
    ax.bar(x + 0.5*width, betweenness_norm, width, label='Betweenness', alpha=0.8)
    ax.bar(x + 1.5*width, pageranks_norm, width, label='PageRank', alpha=0.8)

    ax.set_xlabel('User', fontsize=12, fontweight='bold')
    ax.set_ylabel('Normalized Centrality', fontsize=12, fontweight='bold')
    ax.set_title('Centrality Metrics Comparison (Top 10 by PageRank)', fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(top_users, rotation=45, ha='right')
    ax.legend()
    ax.grid(alpha=0.3, axis='y')

    plt.tight_layout()
    plt.savefig('plots/centrality_comparison.png', dpi=300, bbox_inches='tight')
    print("   ✅ Saved: plots/centrality_comparison.png")
    plt.close()

def plot_community_sizes(results):
    """Bar chart of community sizes"""
    print("[4/6] Creating community size distribution plot...")

    community_assignments = results["communities"]["assignments"]
    community_counts = Counter(community_assignments.values())
    sizes = sorted(community_counts.values(), reverse=True)

    plt.figure(figsize=(10, 6))
    plt.bar(range(len(sizes)), sizes, alpha=0.7, color='coral', edgecolor='darkred', linewidth=1)
    plt.xlabel('Community Rank', fontsize=12, fontweight='bold')
    plt.ylabel('Size (Number of Users)', fontsize=12, fontweight='bold')
    plt.title(f'Community Size Distribution\n({len(sizes)} communities detected)', fontsize=14, fontweight='bold')
    plt.grid(alpha=0.3, axis='y')

    # Add text showing top 3
    for i in range(min(3, len(sizes))):
        plt.text(i, sizes[i] + max(sizes)*0.02, str(sizes[i]),
                 ha='center', va='bottom', fontweight='bold')

    plt.tight_layout()
    plt.savefig('plots/community_sizes.png', dpi=300, bbox_inches='tight')
    print("   ✅ Saved: plots/community_sizes.png")
    plt.close()

def plot_top_contributors(results):
    """Horizontal bar chart of top contributors"""
    print("[5/6] Creating top contributors chart...")

    top_10 = results["top_10_rankings"]["pagerank"][:10]
    users = [entry["user"] for entry in top_10]
    pageranks = [entry["pagerank"] for entry in top_10]

    # Reverse for better readability (highest on top)
    users = users[::-1]
    pageranks = pageranks[::-1]

    fig, ax = plt.subplots(figsize=(10, 7))
    bars = ax.barh(range(len(users)), pageranks, alpha=0.8, color='mediumseagreen', edgecolor='darkgreen')

    # Color the top 3 differently
    bars[0].set_color('lightcoral')  # 10th
    bars[-1].set_color('gold')       # 1st
    bars[-2].set_color('silver')     # 2nd
    bars[-3].set_color('#CD7F32')    # 3rd (bronze)

    ax.set_yticks(range(len(users)))
    ax.set_yticklabels(users, fontsize=10)
    ax.set_xlabel('PageRank Score', fontsize=12, fontweight='bold')
    ax.set_title('Top 10 Contributors by PageRank', fontsize=14, fontweight='bold')
    ax.grid(alpha=0.3, axis='x')

    # Add value labels
    for i, (user, pr) in enumerate(zip(users, pageranks)):
        ax.text(pr, i, f' {pr:.6f}', va='center', fontsize=9)

    plt.tight_layout()
    plt.savefig('plots/top_contributors.png', dpi=300, bbox_inches='tight')
    print("   ✅ Saved: plots/top_contributors.png")
    plt.close()

def plot_network_metrics_summary(results):
    """Summary of key network metrics"""
    print("[6/6] Creating network metrics summary...")

    stats = results["graph_statistics"]

    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(12, 10))

    # Metric 1: Density
    ax1.bar(['Density'], [stats['density']], color='steelblue', alpha=0.7, width=0.5)
    ax1.set_ylabel('Value', fontsize=11, fontweight='bold')
    ax1.set_title('Network Density', fontsize=12, fontweight='bold')
    ax1.set_ylim(0, max(0.1, stats['density'] * 1.2))
    ax1.text(0, stats['density'] + stats['density']*0.05, f"{stats['density']:.6f}",
             ha='center', va='bottom', fontweight='bold')
    ax1.grid(alpha=0.3, axis='y')

    # Metric 2: Clustering Coefficient
    ax2.bar(['Avg Clustering'], [stats['avg_clustering']], color='coral', alpha=0.7, width=0.5)
    ax2.set_ylabel('Value', fontsize=11, fontweight='bold')
    ax2.set_title('Average Clustering Coefficient', fontsize=12, fontweight='bold')
    ax2.set_ylim(0, 1)
    ax2.text(0, stats['avg_clustering'] + 0.02, f"{stats['avg_clustering']:.6f}",
             ha='center', va='bottom', fontweight='bold')
    ax2.grid(alpha=0.3, axis='y')

    # Metric 3: Assortativity
    ax3.bar(['Assortativity'], [stats['assortativity']], color='mediumseagreen', alpha=0.7, width=0.5)
    ax3.set_ylabel('Value', fontsize=11, fontweight='bold')
    ax3.set_title('Degree Assortativity', fontsize=12, fontweight='bold')
    ax3.set_ylim(-1, 1)
    ax3.axhline(y=0, color='black', linestyle='--', linewidth=0.8, alpha=0.5)
    ax3.text(0, stats['assortativity'] + 0.05 if stats['assortativity'] > 0 else stats['assortativity'] - 0.05,
             f"{stats['assortativity']:.6f}", ha='center', va='bottom' if stats['assortativity'] > 0 else 'top',
             fontweight='bold')
    ax3.grid(alpha=0.3, axis='y')

    # Metric 4: Number of Communities
    ax4.bar(['Communities'], [stats['num_communities']], color='mediumpurple', alpha=0.7, width=0.5)
    ax4.set_ylabel('Count', fontsize=11, fontweight='bold')
    ax4.set_title('Number of Communities', fontsize=12, fontweight='bold')
    ax4.text(0, stats['num_communities'] + stats['num_communities']*0.02, str(stats['num_communities']),
             ha='center', va='bottom', fontweight='bold', fontsize=12)
    ax4.grid(alpha=0.3, axis='y')

    fig.suptitle(f'Network Metrics Summary\n{stats["num_vertices"]} nodes, {stats["num_edges"]} edges',
                 fontsize=14, fontweight='bold', y=0.98)

    plt.tight_layout()
    plt.savefig('plots/network_metrics_summary.png', dpi=300, bbox_inches='tight')
    print("   ✅ Saved: plots/network_metrics_summary.png")
    plt.close()

def main():
    print("="*60)
    print("GENERATING VISUALIZATIONS FOR REPORT")
    print("="*60)

    ensure_plots_dir()

    print("\nLoading analysis results...")
    try:
        results = load_results()
    except FileNotFoundError:
        print("ERROR: analysis_results.json not found!")
        print("Run run_full_analysis.py first to generate the data.")
        return

    print(f"Loaded results for {results['graph_statistics']['num_vertices']} nodes\n")

    # Generate all plots
    plot_degree_distribution(results)
    plot_pagerank_vs_degree(results)
    plot_centrality_comparison(results)
    plot_community_sizes(results)
    plot_top_contributors(results)
    plot_network_metrics_summary(results)

    print("\n" + "="*60)
    print("✅ ALL VISUALIZATIONS CREATED!")
    print("="*60)
    print("\nGenerated plots in 'plots/' directory:")
    print("  1. degree_distribution.png")
    print("  2. pagerank_vs_degree.png")
    print("  3. centrality_comparison.png")
    print("  4. community_sizes.png")
    print("  5. top_contributors.png")
    print("  6. network_metrics_summary.png")
    print("\nUse these images in your LaTeX report!")
    print("\nNext step: Generate LaTeX tables with generate_latex_tables.py")

if __name__ == "__main__":
    main()
