"""Artworks router."""

from fastapi import APIRouter, HTTPException, Query
from typing import Optional, List

from ..models.artwork import ArtworkCreate, ArtworkUpdate, ArtworkResponse, ArtworkListResponse
from ..models.provenance import ProvenanceRecord, ProvenanceEventCreate, ProvenanceEventUpdate
from ..models.external import ArtworkEnrichment, DBpediaArtworkInfo, WikidataArtworkInfo, GettyTerm, DBpediaArtistInfo, WikidataArtistInfo
from ..services.artwork_service import artwork_service
from ..services.external_sparql_service import external_sparql_service
from ..services.sparql_service import sparql_service

router = APIRouter(prefix="/artworks", tags=["artworks"])


@router.get("/", response_model=ArtworkListResponse)
async def list_artworks(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    artist: Optional[str] = Query(None, description="Filter by artist name"),
    period: Optional[str] = Query(None, description="Filter by art period"),
    search: Optional[str] = Query(None, description="Search term")
):
    """List artworks with pagination and optional filtering."""
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
    """Get a single artwork by ID."""
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
    """Create a new artwork."""
    try:
        return artwork_service.create_artwork(artwork)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error creating artwork: {str(e)}")


@router.put("/{artwork_id}", response_model=ArtworkResponse)
async def update_artwork(artwork_id: str, artwork: ArtworkUpdate):
    """Update an existing artwork."""
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
    """Delete an artwork and its provenance history."""
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
    """Get provenance history for an artwork."""
    try:
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
    """Add a provenance event to an artwork."""
    try:
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
    """Update a provenance event."""
    try:
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
    """Delete a provenance event."""
    try:
        artwork = artwork_service.get_artwork(artwork_id)
        if not artwork:
            raise HTTPException(status_code=404, detail=f"Artwork '{artwork_id}' not found")
        
        artwork_service.delete_provenance_event(artwork_id, event_id)
        return None
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting provenance event: {str(e)}")


# --- External Enrichment Endpoint ---

# Namespace constants
ARP_NS = "http://example.org/arp#"
OWL_NS = "http://www.w3.org/2002/07/owl#"
SCHEMA_NS = "http://schema.org/"


@router.get(
    "/{artwork_id}/enrich",
    response_model=ArtworkEnrichment,
    tags=["external"],
    summary="Enrich artwork with external data",
    description="""
    Fetch and combine external data for an artwork from DBpedia, Wikidata, and Getty AAT.
    
    This endpoint:
    1. Queries the local Fuseki triplestore for owl:sameAs links
    2. Fetches data from each linked external source
    3. Returns combined enrichment data including artist information
    
    Results are cached for performance.
    """
)
async def enrich_artwork(artwork_id: str):
    """Enrich artwork data from external sources (DBpedia, Wikidata, Getty AAT)."""
    try:
        # Verify artwork exists
        artwork = artwork_service.get_artwork(artwork_id)
        if not artwork:
            raise HTTPException(status_code=404, detail=f"Artwork '{artwork_id}' not found")
        
        # Build full URI
        artwork_uri = f"{ARP_NS}{artwork_id}"
        
        # Query local Fuseki for owl:sameAs links and Getty material URIs
        query = f"""
        PREFIX owl: <{OWL_NS}>
        PREFIX schema: <{SCHEMA_NS}>
        PREFIX arp: <{ARP_NS}>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        
        SELECT ?sameAs ?artMedium ?artistUri ?artistSameAs WHERE {{
            <{artwork_uri}> a arp:Artwork .
            OPTIONAL {{ <{artwork_uri}> owl:sameAs ?sameAs }}
            OPTIONAL {{ <{artwork_uri}> schema:artMedium ?artMedium }}
            OPTIONAL {{ 
                <{artwork_uri}> dc:creator ?artistUri .
                OPTIONAL {{ ?artistUri owl:sameAs ?artistSameAs }}
            }}
        }}
        """
        
        result = sparql_service.execute_query(query)
        
        # Extract URIs from results
        dbpedia_uri = None
        wikidata_uri = None
        getty_uris = []
        artist_dbpedia_uri = None
        artist_wikidata_uri = None
        
        for binding in result.get("results", {}).get("bindings", []):
            # Extract sameAs links
            same_as = binding.get("sameAs", {}).get("value", "")
            if "dbpedia.org" in same_as:
                dbpedia_uri = same_as
            elif "wikidata.org" in same_as:
                wikidata_uri = same_as
            
            # Extract Getty material URIs
            art_medium = binding.get("artMedium", {}).get("value", "")
            if "vocab.getty.edu" in art_medium and art_medium not in getty_uris:
                getty_uris.append(art_medium)
            
            # Extract artist sameAs links
            artist_same_as = binding.get("artistSameAs", {}).get("value", "")
            if "dbpedia.org" in artist_same_as:
                artist_dbpedia_uri = artist_same_as
            elif "wikidata.org" in artist_same_as:
                artist_wikidata_uri = artist_same_as
        
        # Fetch external data
        enrichment = ArtworkEnrichment(artwork_id=artwork_id)
        
        if dbpedia_uri:
            data = external_sparql_service.get_dbpedia_artwork_info(dbpedia_uri)
            if "error" not in data:
                enrichment.dbpedia = DBpediaArtworkInfo(**data)
        
        if wikidata_uri:
            data = external_sparql_service.get_wikidata_artwork_info(wikidata_uri)
            if "error" not in data:
                enrichment.wikidata = WikidataArtworkInfo(**data)
        
        if getty_uris:
            getty_terms = []
            for uri in getty_uris:
                data = external_sparql_service.get_getty_term(uri)
                if "error" not in data:
                    getty_terms.append(GettyTerm(**data))
            enrichment.getty = getty_terms if getty_terms else None
        
        if artist_dbpedia_uri:
            data = external_sparql_service.get_dbpedia_artist_info(artist_dbpedia_uri)
            if "error" not in data:
                enrichment.artist_dbpedia = DBpediaArtistInfo(**data)
        
        if artist_wikidata_uri:
            data = external_sparql_service.get_wikidata_artist_info(artist_wikidata_uri)
            if "error" not in data:
                enrichment.artist_wikidata = WikidataArtistInfo(**data)
        
        return enrichment
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error enriching artwork: {str(e)}")
