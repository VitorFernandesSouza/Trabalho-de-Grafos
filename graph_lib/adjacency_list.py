from typing import List, Dict
from .abstract_graph import AbstractGraph

class AdjacencyListGraph(AbstractGraph):
    def __init__(self, numVertices: int):
        super().__init__(numVertices)
        self._adj_list: List[Dict[int, float]] = [{} for _ in range(numVertices)]
        self._edge_count = 0

    def getVertexCount(self) -> int:
        return self.num_vertices

    def getEdgeCount(self) -> int:
        return self._edge_count

    def hasEdge(self, u: int, v: int) -> bool:
        self._validate_index(u, v)
        return v in self._adj_list[u]

    def addEdge(self, u: int, v: int) -> None:
        self._validate_index(u, v)
        if u == v: return
        if v not in self._adj_list[u]:
            self._adj_list[u][v] = 1.0
            self._edge_count += 1

    def removeEdge(self, u: int, v: int) -> None:
        self._validate_index(u, v)
        if v in self._adj_list[u]:
            del self._adj_list[u][v]
            self._edge_count -= 1

    def setEdgeWeight(self, u: int, v: int, w: float) -> None:
        self._validate_index(u, v)
        if v in self._adj_list[u]:
            self._adj_list[u][v] = w
        else:
            raise ValueError("Aresta não existe.")

    def getEdgeWeight(self, u: int, v: int) -> float:
        self._validate_index(u, v)
        return self._adj_list[u].get(v, 0.0)

    def getNeighbors(self, u: int) -> List[int]:
        self._validate_index(u)
        return list(self._adj_list[u].keys())