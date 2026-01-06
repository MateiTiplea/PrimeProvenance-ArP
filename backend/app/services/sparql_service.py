"""SPARQL service for Fuseki connection."""

from SPARQLWrapper import SPARQLWrapper, JSON, POST, POSTDIRECTLY, BASIC
from typing import Dict, Any

from ..config import settings


class SPARQLService:
    """Service for executing SPARQL queries against Fuseki."""

    # Timeout for SPARQL queries in seconds
    QUERY_TIMEOUT = 15

    def __init__(self):
        self.query_endpoint = SPARQLWrapper(settings.fuseki_query_endpoint)
        self.query_endpoint.setReturnFormat(JSON)
        self.query_endpoint.setTimeout(self.QUERY_TIMEOUT)

        self.update_endpoint = SPARQLWrapper(settings.fuseki_update_endpoint)
        self.update_endpoint.setMethod(POST)
        self.update_endpoint.setRequestMethod(POSTDIRECTLY)
        self.update_endpoint.setTimeout(self.QUERY_TIMEOUT)
        # Fuseki requires authentication for update operations
        self.update_endpoint.setHTTPAuth(BASIC)
        self.update_endpoint.setCredentials(
            settings.fuseki_username, settings.fuseki_password
        )

    def execute_query(self, query: str) -> Dict[str, Any]:
        """Execute a SPARQL SELECT query and return results."""
        self.query_endpoint.setQuery(query)
        return self.query_endpoint.query().convert()

    def execute_update(self, update: str) -> bool:
        """Execute a SPARQL UPDATE (INSERT/DELETE) query."""
        self.update_endpoint.setQuery(update)
        self.update_endpoint.query()
        return True

    def test_connection(self) -> bool:
        """Test if Fuseki is reachable."""
        try:
            self.execute_query("SELECT * WHERE { ?s ?p ?o } LIMIT 1")
            return True
        except Exception:
            return False


sparql_service = SPARQLService()
