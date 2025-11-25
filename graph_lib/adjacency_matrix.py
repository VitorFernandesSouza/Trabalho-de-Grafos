from typing import List, Optional
from .abstract_graph import AbstractGraph

class AdjacencyMatrixGraph(AbstractGraph):
    def __init__(self, numVertices: int):
        super().__init__(numVertices)
        self._matrix: List[List[Optional[float]]] = [[None] * numVertices for _ in range(numVertices)]
        self._edge_count = 0

    def getVertexCount(self) -> int:
        return self.num_vertices

    def getEdgeCount(self) -> int:
        return self._edge_count

    def hasEdge(self, u: int, v: int) -> bool:
        self._validate_index(u, v)
        return self._matrix[u][v] is not None

    def addEdge(self, u: int, v: int) -> None:
        self._validate_index(u, v)
        if u == v: return
        if self._matrix[u][v] is None:
            self._matrix[u][v] = 1.0
            self._edge_count += 1

    def removeEdge(self, u: int, v: int) -> None:
        self._validate_index(u, v)
        if self._matrix[u][v] is not None:
            self._matrix[u][v] = None
            self._edge_count -= 1

    def setEdgeWeight(self, u: int, v: int, w: float) -> None:
        self._validate_index(u, v)
        if self._matrix[u][v] is not None:
            self._matrix[u][v] = w
        else:
            raise ValueError("Aresta não existe.")

    def getEdgeWeight(self, u: int, v: int) -> float:
        self._validate_index(u, v)
        return self._matrix[u][v] if self._matrix[u][v] is not None else 0.0

    def getNeighbors(self, u: int) -> List[int]:
        self._validate_index(u)
        return [v for v in range(self.num_vertices) if self._matrix[u][v] is not None]