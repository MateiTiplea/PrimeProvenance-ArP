"""Pydantic models for external data enrichment."""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class LinkedEntity(BaseModel):
    """A linked entity with URI and label."""
    uri: Optional[str] = None
    label: Optional[str] = None
    name: Optional[str] = None  # Alternative to label (used by DBpedia)


class DBpediaArtworkInfo(BaseModel):
    """DBpedia artwork information."""
    source: str = "dbpedia"
    uri: str
    abstract: Optional[str] = None
    thumbnail: Optional[str] = None
    artist: Optional[LinkedEntity] = None
    museum: Optional[LinkedEntity] = None
    year: Optional[str] = None
    dimensions: Optional[Dict[str, str]] = None
    wikidata_uri: Optional[str] = None
    error: Optional[str] = None


class DBpediaArtistInfo(BaseModel):
    """DBpedia artist biographical information."""
    source: str = "dbpedia"
    uri: str
    abstract: Optional[str] = None
    thumbnail: Optional[str] = None
    birthDate: Optional[str] = None
    deathDate: Optional[str] = None
    birthPlace: Optional[LinkedEntity] = None
    nationality: Optional[str] = None
    movement: Optional[LinkedEntity] = None
    wikidata_uri: Optional[str] = None
    error: Optional[str] = None


class WikidataArtworkInfo(BaseModel):
    """Wikidata artwork metadata."""
    source: str = "wikidata"
    uri: str
    qid: str
    image: Optional[str] = None
    inception: Optional[str] = None
    creator: Optional[LinkedEntity] = None
    location: Optional[LinkedEntity] = None
    material: Optional[LinkedEntity] = None
    genre: Optional[LinkedEntity] = None
    movement: Optional[LinkedEntity] = None
    error: Optional[str] = None


class WikidataArtistInfo(BaseModel):
    """Wikidata artist information."""
    source: str = "wikidata"
    uri: str
    qid: str
    image: Optional[str] = None
    birthDate: Optional[str] = None
    deathDate: Optional[str] = None
    birthPlace: Optional[LinkedEntity] = None
    nationality: Optional[LinkedEntity] = None
    occupation: Optional[LinkedEntity] = None
    movement: Optional[LinkedEntity] = None
    error: Optional[str] = None


class GettyTerm(BaseModel):
    """Getty AAT term information."""
    source: str = "getty"
    uri: str
    prefLabel: Optional[str] = None
    scopeNote: Optional[str] = None
    broader: Optional[LinkedEntity] = None
    error: Optional[str] = None


class LocalArtistInfo(BaseModel):
    """Artist information from local triplestore."""
    source: str = "local"
    uri: Optional[str] = None
    name: Optional[str] = None
    birthDate: Optional[str] = None
    deathDate: Optional[str] = None
    nationality: Optional[str] = None
    description: Optional[str] = None


class ExternalLinks(BaseModel):
    """External links for an artwork or artist."""
    dbpedia: Optional[str] = Field(None, description="DBpedia resource URI")
    wikidata: Optional[str] = Field(None, description="Wikidata entity URI")
    getty: Optional[List[str]] = Field(None, description="Getty AAT URIs")


class ArtworkEnrichment(BaseModel):
    """Combined enrichment data for an artwork from all external sources."""
    artwork_id: str
    dbpedia: Optional[DBpediaArtworkInfo] = None
    wikidata: Optional[WikidataArtworkInfo] = None
    getty: Optional[List[GettyTerm]] = None
    artist_dbpedia: Optional[DBpediaArtistInfo] = None
    artist_wikidata: Optional[WikidataArtistInfo] = None
    artist_local: Optional[LocalArtistInfo] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "artwork_id": "artwork_mona_lisa",
                "dbpedia": {
                    "source": "dbpedia",
                    "uri": "http://dbpedia.org/resource/Mona_Lisa",
                    "abstract": "The Mona Lisa is a half-length portrait painting...",
                    "thumbnail": "http://commons.wikimedia.org/wiki/Special:FilePath/..."
                },
                "wikidata": {
                    "source": "wikidata",
                    "uri": "http://www.wikidata.org/entity/Q12418",
                    "qid": "Q12418",
                    "image": "http://commons.wikimedia.org/wiki/Special:FilePath/..."
                }
            }
        }


class ExternalResourceQuery(BaseModel):
    """Request model for querying an external resource."""
    uri: str = Field(..., description="Full URI of the resource to query")


class ExternalQueryResponse(BaseModel):
    """Generic response for external queries."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    source: str
    cached: bool = False

