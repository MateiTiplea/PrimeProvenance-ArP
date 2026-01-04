"""SPARQL service for Fuseki connection."""

from SPARQLWrapper import SPARQLWrapper, JSON
from typing import Dict, Any

from ..config import settings


class SPARQLService:
    """Service for executing SPARQL queries against Fuseki."""
    
    def __init__(self):
        self.endpoint = SPARQLWrapper(settings.fuseki_query_endpoint)
        self.endpoint.setReturnFormat(JSON)
    
    def execute_query(self, query: str) -> Dict[str, Any]:
        """Execute a SPARQL query and return results."""
        self.endpoint.setQuery(query)
        return self.endpoint.query().convert()
    
    def test_connection(self) -> bool:
        """Test if Fuseki is reachable."""
        try:
            self.execute_query("SELECT * WHERE { ?s ?p ?o } LIMIT 1")
            return True
        except Exception:
            return False


sparql_service = SPARQLService()
