"""Search router for full-text search across artworks."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from ..services.artwork_service import artwork_service

router = APIRouter(prefix="/search", tags=["search"])


@router.get("/")
async def search_artworks(
    q: str = Query(..., min_length=1, description="Search query"),
    fields: Optional[List[str]] = Query(
        None, 
        description="Fields to search (title, artist, description). Defaults to all."
    ),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page")
):
    """
    Full-text search across artworks.
    
    Searches across specified fields (or all by default) and returns
    matching artworks with pagination.
    
    **Query Parameters:**
    - `q` (required): The search term
    - `fields` (optional): List of fields to search - title, artist, description
    - `page` (optional): Page number for pagination (default: 1)
    - `limit` (optional): Number of results per page (default: 20, max: 100)
    
    **Response:**
    - `query`: The original search query
    - `total`: Total number of matching results
    - `page`: Current page number
    - `limit`: Items per page
    - `results`: Array of matching artworks
    """
    try:
        return artwork_service.search_artworks(
            q=q,
            fields=fields,
            page=page,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching artworks: {str(e)}")
