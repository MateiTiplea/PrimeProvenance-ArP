"""Statistics router for Getty-based artwork analytics."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional

from ..models.statistics import (
    MaterialDistribution,
    MaterialHierarchyResponse,
    TemporalTrendsResponse,
    CrossAnalysisResponse,
    StatisticsQueryRequest,
    StatisticsQueryResponse,
)
from ..services.statistics_service import statistics_service

router = APIRouter(prefix="/statistics", tags=["statistics"])


@router.get(
    "/materials",
    response_model=MaterialDistribution,
    summary="Get artwork distribution by Getty AAT materials",
    description="""
    Retrieve artwork counts grouped by Getty Art & Architecture Thesaurus (AAT) material types.
    
    This endpoint:
    1. Queries the local triplestore for artworks with schema:artMedium links to Getty AAT
    2. Counts artworks for each unique material
    3. Enriches results with Getty AAT labels and scope notes via federated query
    
    Results are ordered by artwork count (descending).
    """
)
async def get_material_distribution():
    """Get artwork counts by Getty AAT material types."""
    try:
        return statistics_service.get_material_distribution()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching material distribution: {str(e)}"
        )


@router.get(
    "/materials/hierarchy",
    response_model=MaterialHierarchyResponse,
    summary="Get material distribution by Getty AAT hierarchy",
    description="""
    Retrieve artwork distribution organized by Getty AAT broader categories.
    
    This endpoint:
    1. Gets the basic material distribution
    2. Groups materials by their parent/broader categories in the Getty hierarchy
    3. Returns a hierarchical view of material usage
    
    Useful for understanding which broad categories of materials are most used.
    """
)
async def get_material_hierarchy():
    """Get material distribution grouped by Getty AAT broader categories."""
    try:
        return statistics_service.get_material_hierarchy()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching material hierarchy: {str(e)}"
        )


@router.get(
    "/temporal",
    response_model=TemporalTrendsResponse,
    summary="Get temporal trends of Getty material usage",
    description="""
    Retrieve material usage trends across art historical periods.
    
    This endpoint:
    1. Cross-references artwork periods with Getty AAT materials
    2. Shows which materials were used in each time period
    3. Helps identify trends in artistic techniques across history
    
    Periods are based on arp:artworkPeriod values in the triplestore.
    """
)
async def get_temporal_trends():
    """Get Getty material usage trends across time periods."""
    try:
        return statistics_service.get_temporal_trends()
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching temporal trends: {str(e)}"
        )


@router.get(
    "/cross-analysis",
    response_model=CrossAnalysisResponse,
    summary="Get cross-category analysis (e.g., period x material)",
    description="""
    Retrieve a cross-tabulation matrix for two dimensions of artwork data.
    
    Supported dimensions:
    - `period`: Art historical period
    - `location`: Current location/museum
    - `artist`: Artist name
    - `material`: Getty AAT material type
    
    Returns a matrix showing counts for each combination of dimension values.
    This is useful for analyzing relationships between different aspects of artworks.
    """
)
async def get_cross_analysis(
    dimension_x: str = Query(
        "period",
        description="X-axis dimension (period, location, artist)",
        enum=["period", "location", "artist"]
    ),
    dimension_y: str = Query(
        "material",
        description="Y-axis dimension (material)",
        enum=["material"]
    )
):
    """Get cross-category analysis matrix."""
    try:
        return statistics_service.get_cross_analysis(
            dimension_x=dimension_x,
            dimension_y=dimension_y
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error fetching cross analysis: {str(e)}"
        )


@router.post(
    "/sparql",
    response_model=StatisticsQueryResponse,
    summary="Execute custom statistics SPARQL query",
    description="""
    Execute a custom SPARQL query with Getty namespace prefixes auto-injected.
    
    This endpoint:
    1. Optionally injects Getty-related namespace prefixes (aat, gvp, skos, etc.)
    2. Executes the query against the local Fuseki triplestore
    3. Returns the raw SPARQL results
    
    **Pre-injected prefixes (when enabled):**
    - `aat:` - Getty AAT namespace
    - `gvp:` - Getty Vocabulary Program ontology
    - `skos:` - SKOS vocabulary
    - `schema:` - Schema.org
    - `arp:` - ArP ontology
    - `dc:` - Dublin Core
    - `dcterms:` - Dublin Core Terms
    
    Use this for advanced statistical queries that aren't covered by the predefined endpoints.
    """
)
async def execute_statistics_query(request: StatisticsQueryRequest):
    """Execute a custom SPARQL statistics query."""
    try:
        return statistics_service.execute_statistics_query(
            query=request.query,
            include_getty_prefixes=request.include_getty_prefixes
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error executing statistics query: {str(e)}"
        )
