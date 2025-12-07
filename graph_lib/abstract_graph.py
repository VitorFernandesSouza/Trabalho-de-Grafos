import abc
import csv
import os
import xml.etree.ElementTree as ET
from xml.dom import minidom
from typing import List, Dict

class AbstractGraph(abc.ABC):
    def __init__(self, num_vertices: int):
        self.num_vertices = num_vertices
        self._vertex_weights: Dict[int, float] = {i: 1.0 for i in range(num_vertices)}
        self._vertex_labels: Dict[int, str] = {i: f"Node_{i}" for i in range(num_vertices)}

    def set_vertex_label(self, v: int, label: str):
        self._validate_index(v)
        self._vertex_labels[v] = label

    def get_vertex_label(self, v: int) -> str:
        self._validate_index(v)
        return self._vertex_labels.get(v, str(v))

    def _validate_index(self, *indices):
        for idx in indices:
            if idx < 0 or idx >= self.num_vertices:
                raise IndexError(f"Índice {idx} inválido. Esperado entre 0 e {self.num_vertices - 1}.")
    
    def _ensure_data_dir(self):
        if not os.path.exists("data"):
            os.makedirs("data")

    @abc.abstractmethod
    def getVertexCount(self) -> int: pass

    @abc.abstractmethod
    def getEdgeCount(self) -> int: pass

    @abc.abstractmethod
    def hasEdge(self, u: int, v: int) -> bool: pass

    @abc.abstractmethod
    def addEdge(self, u: int, v: int) -> None: pass

    @abc.abstractmethod
    def removeEdge(self, u: int, v: int) -> None: pass

    @abc.abstractmethod
    def getEdgeWeight(self, u: int, v: int) -> float: pass

    @abc.abstractmethod
    def setEdgeWeight(self, u: int, v: int, w: float) -> None: pass

    @abc.abstractmethod
    def getNeighbors(self, u: int) -> List[int]: pass

    # Métodos Concretos

    def isSucessor(self, u: int, v: int) -> bool:
        return self.hasEdge(u, v)

    def isPredecessor(self, u: int, v: int) -> bool:
        return self.hasEdge(v, u)

    def isDivergent(self, u1: int, v1: int, u2: int, v2: int) -> bool:
        self._validate_index(u1, v1, u2, v2)
        if not (self.hasEdge(u1, v1) and self.hasEdge(u2, v2)):
            return False
        return (u1 == u2) and (v1 != v2)

    def isConvergent(self, u1: int, v1: int, u2: int, v2: int) -> bool:
        self._validate_index(u1, v1, u2, v2)
        if not (self.hasEdge(u1, v1) and self.hasEdge(u2, v2)):
            return False
        return (v1 == v2) and (u1 != u2)

    def isIncident(self, u: int, v: int, x: int) -> bool:
        self._validate_index(u, v, x)
        if not self.hasEdge(u, v):
            return False
        return x == u or x == v

    def getVertexInDegree(self, u: int) -> int:
        self._validate_index(u)
        degree = 0
        for i in range(self.num_vertices):
            if self.hasEdge(i, u):
                degree += 1
        return degree

    def getVertexOutDegree(self, u: int) -> int:
        self._validate_index(u)
        return len(self.getNeighbors(u))

    def setVertexWeight(self, v: int, w: float):
        self._validate_index(v)
        self._vertex_weights[v] = w

    def getVertexWeight(self, v: int) -> float:
        self._validate_index(v)
        return self._vertex_weights.get(v, 1.0)

    def isConnected(self) -> bool:
        if self.getVertexCount() == 0: return True
        visited = set()
        queue = [0]
        visited.add(0)
        
        while queue:
            curr = queue.pop(0)
            for neighbor in self.getNeighbors(curr):
                if neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
            for i in range(self.num_vertices):
                if i not in visited and self.hasEdge(i, curr):
                    visited.add(i)
                    queue.append(i)
        return len(visited) == self.num_vertices

    def isEmptyGraph(self) -> bool:
        return self.getEdgeCount() == 0

    def isCompleteGraph(self) -> bool:
        n = self.getVertexCount()
        return self.getEdgeCount() == n * (n - 1)

    def exportToGEPHI(self, filename: str):
        self._ensure_data_dir()
        
        clean_name = filename.replace(".csv", "")
        
        nodes_path = os.path.join("data", f"{clean_name}_nodes.csv")
        edges_path = os.path.join("data", f"{clean_name}_edges.csv")
        
        try:
            with open(nodes_path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Id", "Label", "Weight"])
                for i in range(self.num_vertices):
                    writer.writerow([i, self.get_vertex_label(i), self.getVertexWeight(i)])
            
            with open(edges_path, mode='w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(["Source", "Target", "Weight", "Type"])
                for u in range(self.num_vertices):
                    for v in self.getNeighbors(u):
                        writer.writerow([u, v, self.getEdgeWeight(u, v), "Directed"])
            print(f"Exportado para CSV: {nodes_path}, {edges_path}")
        except IOError as e:
            print(f"Erro ao exportar CSV: {e}")

    def exportToGEXF(self, filename: str):
        self._ensure_data_dir()
        
        if not filename.endswith(".gexf"):
            filename += ".gexf"
            
        filepath = os.path.join("data", filename)
        
        # Estrutura básica do GEXF
        gexf = ET.Element('gexf', {
            'xmlns': 'http://www.gexf.net/1.2draft',
            'version': '1.2'
        })
        
        meta = ET.SubElement(gexf, 'meta', {'lastmodifieddate': '2023-10-01'})
        creator = ET.SubElement(meta, 'creator')
        creator.text = 'GitHubMiner Tool'
        
        graph_elem = ET.SubElement(gexf, 'graph', {
            'mode': 'static', 
            'defaultedgetype': 'directed'
        })
        
        nodes_elem = ET.SubElement(graph_elem, 'nodes')
        for i in range(self.num_vertices):
            node = ET.SubElement(nodes_elem, 'node', {
                'id': str(i),
                'label': self.get_vertex_label(i)
            })
        
        edges_elem = ET.SubElement(graph_elem, 'edges')
        edge_id = 0
        for u in range(self.num_vertices):
            for v in self.getNeighbors(u):
                weight = self.getEdgeWeight(u, v)
                ET.SubElement(edges_elem, 'edge', {
                    'id': str(edge_id),
                    'source': str(u),
                    'target': str(v),
                    'weight': str(weight)
                })
                edge_id += 1
                
        try:
            raw_string = ET.tostring(gexf, 'utf-8')
            parsed = minidom.parseString(raw_string)
            pretty_xml = parsed.toprettyxml(indent="  ")
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(pretty_xml)
                
            print(f"Exportado para GEXF: {filepath}")
        except Exception as e:
            print(f"Erro ao exportar GEXF: {e}")