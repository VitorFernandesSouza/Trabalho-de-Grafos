from abc import ABC, abstractmethod

class AbstractGraph(ABC):
    def __init__(self, num_vertices):
        self.num_vertices = num_vertices
        self.vertex_weights = [0] * num_vertices

    @abstractmethod
    def add_edge(self, u, v): pass

    @abstractmethod
    def remove_edge(self, u, v): pass

    @abstractmethod
    def has_edge(self, u, v): pass

    @abstractmethod
    def get_edge_count(self): pass

    def set_vertex_weight(self, v, w): self.vertex_weights[v] = w
    def get_vertex_weight(self, v): return self.vertex_weights[v]
