"""Artworks router."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from ..models.artwork import ArtworkCreate, ArtworkUpdate, ArtworkResponse, ArtworkListResponse
from ..models.provenance import ProvenanceRecord, ProvenanceEventCreate, ProvenanceEventUpdate
from ..services.artwork_service import artwork_service

router = APIRouter(prefix="/artworks", tags=["artworks"])


@router.get("/", response_model=ArtworkListResponse)
async def list_artworks(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    artist: Optional[str] = Query(None, description="Filter by artist name"),
    period: Optional[str] = Query(None, description="Filter by art period"),
    search: Optional[str] = Query(None, description="Search term")
):
    """
    List artworks with pagination and optional filtering.
    
    Returns a paginated list of artworks in JSON-LD format.
    """
    try:
        return artwork_service.list_artworks(
            page=page,
            limit=limit,
            artist=artist,
            period=period,
            search=search
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error listing artworks: {str(e)}")


@router.get("/{artwork_id}", response_model=ArtworkResponse)
async def get_artwork(artwork_id: str):
    """
    Get a single artwork by ID.
    
    Returns the artwork with full details in JSON-LD format.
    """
    try:
        artwork = artwork_service.get_artwork(artwork_id)
        if not artwork:
            raise HTTPException(status_code=404, detail=f"Artwork '{artwork_id}' not found")
        return artwork
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving artwork: {str(e)}")


@router.post("/", response_model=ArtworkResponse, status_code=201)
async def create_artwork(artwork: ArtworkCreate):
    """
    Create a new artwork.
    
    Stores the artwork in the Fuseki triplestore and returns the created
    artwork with its assigned ID in JSON-LD format.
    """
    try:
        return artwork_service.create_artwork(artwork)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating artwork: {str(e)}")


@router.put("/{artwork_id}", response_model=ArtworkResponse)
async def update_artwork(artwork_id: str, artwork: ArtworkUpdate):
    """
    Update an existing artwork.
    
    Updates only the provided fields. Returns the updated artwork in JSON-LD format.
    """
    try:
        updated = artwork_service.update_artwork(artwork_id, artwork)
        if not updated:
            raise HTTPException(status_code=404, detail=f"Artwork '{artwork_id}' not found")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating artwork: {str(e)}")


@router.delete("/{artwork_id}", status_code=204)
async def delete_artwork(artwork_id: str):
    """
    Delete an artwork and its provenance history.
    
    This operation cannot be undone.
    """
    try:
        deleted = artwork_service.delete_artwork(artwork_id)
        if not deleted:
            raise HTTPException(status_code=404, detail=f"Artwork '{artwork_id}' not found")
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting artwork: {str(e)}")


# --- Provenance Endpoints ---

@router.get("/{artwork_id}/provenance", response_model=List[ProvenanceRecord])
async def get_provenance(artwork_id: str):
    """
    Get provenance history for an artwork.
    
    Returns a list of provenance events (ownership history) ordered chronologically.
    """
    try:
        # First verify the artwork exists
        artwork = artwork_service.get_artwork(artwork_id)
        if not artwork:
            raise HTTPException(status_code=404, detail=f"Artwork '{artwork_id}' not found")
        
        return artwork_service.get_provenance(artwork_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error retrieving provenance: {str(e)}")


@router.post("/{artwork_id}/provenance", response_model=ProvenanceRecord, status_code=201)
async def add_provenance_event(artwork_id: str, event: ProvenanceEventCreate):
    """
    Add a provenance event to an artwork.
    
    Creates a new provenance record and returns it with an assigned ID.
    Events are automatically ordered based on creation time.
    """
    try:
        # First verify the artwork exists
        artwork = artwork_service.get_artwork(artwork_id)
        if not artwork:
            raise HTTPException(status_code=404, detail=f"Artwork '{artwork_id}' not found")
        
        return artwork_service.add_provenance_event(artwork_id, event)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error adding provenance event: {str(e)}")


@router.put("/{artwork_id}/provenance/{event_id}", response_model=ProvenanceRecord)
async def update_provenance_event(artwork_id: str, event_id: str, event: ProvenanceEventUpdate):
    """
    Update a provenance event.
    
    Updates only the provided fields. Returns the updated event.
    """
    try:
        # First verify the artwork exists
        artwork = artwork_service.get_artwork(artwork_id)
        if not artwork:
            raise HTTPException(status_code=404, detail=f"Artwork '{artwork_id}' not found")
        
        updated = artwork_service.update_provenance_event(artwork_id, event_id, event)
        if not updated:
            raise HTTPException(status_code=404, detail=f"Provenance event '{event_id}' not found")
        return updated
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating provenance event: {str(e)}")


@router.delete("/{artwork_id}/provenance/{event_id}", status_code=204)
async def delete_provenance_event(artwork_id: str, event_id: str):
    """
    Delete a provenance event.
    
    This operation cannot be undone.
    """
    try:
        # First verify the artwork exists
        artwork = artwork_service.get_artwork(artwork_id)
        if not artwork:
            raise HTTPException(status_code=404, detail=f"Artwork '{artwork_id}' not found")
        
        artwork_service.delete_provenance_event(artwork_id, event_id)
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting provenance event: {str(e)}")

