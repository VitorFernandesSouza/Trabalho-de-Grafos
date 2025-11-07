from src.core.abstract_graph import AbstractGraph

class AdjacencyListGraph(AbstractGraph):
    def __init__(self, num_vertices):
        super().__init__(num_vertices)
        self.adj_list = {i: [] for i in range(num_vertices)}

    def add_edge(self, u, v):
        if u != v and v not in self.adj_list[u]:
            self.adj_list[u].append(v)

    def remove_edge(self, u, v):
        if v in self.adj_list[u]:
            self.adj_list[u].remove(v)

    def has_edge(self, u, v):
        return v in self.adj_list[u]

    def get_edge_count(self):
        return sum(len(lst) for lst in self.adj_list.values())
