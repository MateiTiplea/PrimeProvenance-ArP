"""SPARQL router."""

from fastapi import APIRouter
from pydantic import BaseModel

from ..services.sparql_service import sparql_service

router = APIRouter(prefix="/sparql", tags=["sparql"])


class QueryRequest(BaseModel):
    query: str


@router.post("/query")
async def execute_query(request: QueryRequest):
    """Execute a SPARQL query."""
    try:
        results = sparql_service.execute_query(request.query)
        return {"success": True, "results": results}
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.get("/status")
async def check_status():
    """Check Fuseki connection status."""
    connected = sparql_service.test_connection()
    return {"connected": connected}
