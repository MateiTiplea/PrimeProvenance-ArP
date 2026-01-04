"""RDF service using rdflib."""

from rdflib import Graph


class RDFService:
    """Service for RDF graph operations."""
    
    def __init__(self):
        self.graph = Graph()
    
    def parse(self, data: str, format: str = "turtle") -> Graph:
        """Parse RDF data into a graph."""
        return self.graph.parse(data=data, format=format)
    
    def serialize(self, format: str = "turtle") -> str:
        """Serialize graph to string."""
        return self.graph.serialize(format=format)


rdf_service = RDFService()
