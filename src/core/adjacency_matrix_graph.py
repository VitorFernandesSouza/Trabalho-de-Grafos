from src.core.abstract_graph import AbstractGraph
import numpy as np

class AdjacencyMatrixGraph(AbstractGraph):
    def __init__(self, num_vertices):
        super().__init__(num_vertices)
        self.matrix = np.zeros((num_vertices, num_vertices))

    def add_edge(self, u, v):
        if u == v: return
        self.matrix[u][v] = 1

    def remove_edge(self, u, v):
        self.matrix[u][v] = 0

    def has_edge(self, u, v):
        return self.matrix[u][v] == 1

    def get_edge_count(self):
        return int(np.sum(self.matrix))
