"""Artwork data models."""

from pydantic import BaseModel, Field
from typing import Optional, List, Any, Dict


class ArtworkBase(BaseModel):
    """Base artwork properties for create/update operations."""
    
    title: str = Field(..., min_length=1, max_length=500)
    artist: Optional[str] = None
    dateCreated: Optional[str] = None
    medium: Optional[str] = None
    dimensions: Optional[str] = None
    description: Optional[str] = None
    imageUrl: Optional[str] = None
    currentLocation: Optional[str] = None
    period: Optional[str] = None
    style: Optional[str] = None


class ArtworkCreate(ArtworkBase):
    """Schema for creating a new artwork."""
    pass


class ArtworkUpdate(BaseModel):
    """Schema for updating an artwork (all fields optional)."""
    
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    artist: Optional[str] = None
    dateCreated: Optional[str] = None
    medium: Optional[str] = None
    dimensions: Optional[str] = None
    description: Optional[str] = None
    imageUrl: Optional[str] = None
    currentLocation: Optional[str] = None
    period: Optional[str] = None
    style: Optional[str] = None


class ExternalLinks(BaseModel):
    """External links to DBpedia, Wikidata, Getty AAT."""
    
    dbpedia: Optional[str] = None
    wikidata: Optional[str] = None
    getty: Optional[str] = None


class ArtworkResponse(ArtworkBase):
    """Schema for artwork response with JSON-LD context."""
    
    id: str
    
    # External links from owl:sameAs
    externalLinks: Optional[ExternalLinks] = None
    
    # JSON-LD context
    context: Optional[Dict[str, Any]] = Field(None, alias="@context")
    type: Optional[str] = Field(None, alias="@type")
    
    class Config:
        populate_by_name = True


class ArtworkListResponse(BaseModel):
    """Paginated list of artworks."""
    
    items: List[ArtworkResponse]
    total: int
    page: int
    limit: int
    hasMore: bool
    
    # JSON-LD context for the collection
    context: Optional[Dict[str, Any]] = Field(None, alias="@context")
    
    class Config:
        populate_by_name = True
