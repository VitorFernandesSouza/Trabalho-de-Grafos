# GitHub Graph Analysis Tool

A tool for mining and analyzing GitHub repository interactions using graph theory algorithms.

## Requirements

- Python 3.6+
- `requests` library

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the main application:
```bash
python main.py
```

The tool provides a menu-driven interface with options to:
1. Configure repository and GitHub token
2. Mine repository data (issues, PRs, comments, reviews)
3. Build individual graphs (comments, closures, reviews/merges)
4. Create integrated weighted graph
5. Analyze graph metrics (centrality, clustering, communities)
6. Export to Gephi format

## Features

- **Graph Analysis**: Degree, closeness, betweenness centrality, PageRank
- **Community Detection**: Label propagation algorithm
- **Metrics**: Density, clustering coefficient, assortativity
- **Export**: Gephi-compatible CSV files for visualization