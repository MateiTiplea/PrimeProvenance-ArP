"""Search router for full-text search across artworks."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from ..services.artwork_service import artwork_service
from ..models.artwork import SearchResponse

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/", response_model=SearchResponse)
async def search_artworks(
    q: Optional[str] = Query(None, description="Search query"),
    fields: Optional[List[str]] = Query(
        None, 
        description="Fields to search (title, artist, description). Defaults to all."
    ),
    artist: Optional[str] = Query(None, description="Filter by artist name"),
    period: Optional[str] = Query(None, description="Filter by art period"),
    medium: Optional[str] = Query(None, description="Filter by artwork medium"),
    location: Optional[str] = Query(None, description="Filter by current location"),
    style: Optional[str] = Query(None, description="Filter by artwork style"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Full-text search across artworks with faceted filtering.
    
    Searches across specified fields (or all by default) and returns
    matching artworks with pagination and facet counts.
    
    **Query Parameters:**
    - `q` (optional): The search term
    - `fields` (optional): List of fields to search - title, artist, description
    - `fields` (optional): List of fields to search - title, artist, description
    - `artist` (optional): Filter by artist name
    - `period` (optional): Filter by art period
    - `medium` (optional): Filter by artwork medium
    - `location` (optional): Filter by current location
    - `style` (optional): Filter by artwork style
    - `page` (optional): Page number for pagination (default: 1)
    - `limit` (optional): Number of results per page (default: 20, max: 100)
    
    **Response:**
    - `query`: The original search query
    - `total`: Total number of matching results
    - `page`: Current page number
    - `limit`: Items per page
    - `results`: Array of matching artworks
    - `facets`: Available filter options with counts
    """
    try:
        return artwork_service.search_artworks(
            q=q,
            fields=fields,
            page=page,
            limit=limit,
            artist=artist,
            period=period,
            medium=medium,
            location=location,
            style=style
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching artworks: {str(e)}")
