"""External data router for DBpedia, Wikidata, and Getty AAT queries."""

from fastapi import APIRouter, HTTPException, Query, Path
from typing import Optional, List
from urllib.parse import unquote

from ..models.external import (
    DBpediaArtworkInfo,
    DBpediaArtistInfo,
    WikidataArtworkInfo,
    WikidataArtistInfo,
    GettyTerm,
    ArtworkEnrichment,
    ExternalQueryResponse,
)
from ..services.external_sparql_service import external_sparql_service
from ..services.sparql_service import sparql_service

router = APIRouter(prefix="/external", tags=["external"])


# =============================================================================
# DBpedia Endpoints
# =============================================================================

@router.get(
    "/dbpedia/artwork/{resource:path}",
    response_model=ExternalQueryResponse,
    summary="Query DBpedia for artwork information",
    description="Fetch artwork metadata from DBpedia including abstract, thumbnail, artist, and museum information."
)
async def get_dbpedia_artwork(
    resource: str = Path(..., description="DBpedia resource name or full URI (e.g., 'Mona_Lisa' or 'http://dbpedia.org/resource/Mona_Lisa')")
):
    """Query DBpedia for artwork information."""
    try:
        # Normalize to full URI
        resource = unquote(resource)
        if not resource.startswith("http"):
            uri = f"http://dbpedia.org/resource/{resource}"
        else:
            uri = resource
        
        data = external_sparql_service.get_dbpedia_artwork_info(uri)
        
        if "error" in data:
            return ExternalQueryResponse(
                success=False,
                error=data.get("error"),
                source="dbpedia"
            )
        
        return ExternalQueryResponse(
            success=True,
            data=data,
            source="dbpedia"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying DBpedia: {str(e)}")


@router.get(
    "/dbpedia/artist/{resource:path}",
    response_model=ExternalQueryResponse,
    summary="Query DBpedia for artist information",
    description="Fetch artist biographical data from DBpedia including birth/death dates, nationality, and art movement."
)
async def get_dbpedia_artist(
    resource: str = Path(..., description="DBpedia resource name or full URI (e.g., 'Leonardo_da_Vinci')")
):
    """Query DBpedia for artist biographical information."""
    try:
        resource = unquote(resource)
        if not resource.startswith("http"):
            uri = f"http://dbpedia.org/resource/{resource}"
        else:
            uri = resource
        
        data = external_sparql_service.get_dbpedia_artist_info(uri)
        
        if "error" in data:
            return ExternalQueryResponse(
                success=False,
                error=data.get("error"),
                source="dbpedia"
            )
        
        return ExternalQueryResponse(
            success=True,
            data=data,
            source="dbpedia"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying DBpedia: {str(e)}")


# =============================================================================
# Wikidata Endpoints
# =============================================================================

@router.get(
    "/wikidata/artwork/{entity}",
    response_model=ExternalQueryResponse,
    summary="Query Wikidata for artwork information",
    description="Fetch artwork metadata from Wikidata including image, inception date, materials, and location."
)
async def get_wikidata_artwork(
    entity: str = Path(..., description="Wikidata Q-ID or full URI (e.g., 'Q12418' or 'http://www.wikidata.org/entity/Q12418')")
):
    """Query Wikidata for artwork metadata."""
    try:
        entity = unquote(entity)
        data = external_sparql_service.get_wikidata_artwork_info(entity)
        
        if "error" in data:
            return ExternalQueryResponse(
                success=False,
                error=data.get("error"),
                source="wikidata"
            )
        
        return ExternalQueryResponse(
            success=True,
            data=data,
            source="wikidata"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying Wikidata: {str(e)}")


@router.get(
    "/wikidata/artist/{entity}",
    response_model=ExternalQueryResponse,
    summary="Query Wikidata for artist information",
    description="Fetch artist biographical data from Wikidata including birth/death dates, nationality, and occupation."
)
async def get_wikidata_artist(
    entity: str = Path(..., description="Wikidata Q-ID or full URI (e.g., 'Q762' for Leonardo da Vinci)")
):
    """Query Wikidata for artist information."""
    try:
        entity = unquote(entity)
        data = external_sparql_service.get_wikidata_artist_info(entity)
        
        if "error" in data:
            return ExternalQueryResponse(
                success=False,
                error=data.get("error"),
                source="wikidata"
            )
        
        return ExternalQueryResponse(
            success=True,
            data=data,
            source="wikidata"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying Wikidata: {str(e)}")


# =============================================================================
# Getty AAT Endpoints
# =============================================================================

@router.get(
    "/getty/{aat_id}",
    response_model=ExternalQueryResponse,
    summary="Query Getty AAT for term information",
    description="Fetch term information from Getty Art & Architecture Thesaurus including preferred label and scope note."
)
async def get_getty_term(
    aat_id: str = Path(..., description="Getty AAT ID (e.g., '300015050' for oil paint) or full URI")
):
    """Query Getty AAT for art terminology."""
    try:
        aat_id = unquote(aat_id)
        data = external_sparql_service.get_getty_term(aat_id)
        
        if "error" in data:
            return ExternalQueryResponse(
                success=False,
                error=data.get("error"),
                source="getty"
            )
        
        return ExternalQueryResponse(
            success=True,
            data=data,
            source="getty"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying Getty AAT: {str(e)}")


# =============================================================================
# Artwork Enrichment Endpoint
# =============================================================================

# Namespace constants (match those in artwork_service.py)
ARP_NS = "http://example.org/arp#"
OWL_NS = "http://www.w3.org/2002/07/owl#"
SCHEMA_NS = "http://schema.org/"


@router.get(
    "/enrich/{artwork_id}",
    response_model=ArtworkEnrichment,
    summary="Enrich artwork with external data",
    description="""
    Fetch and combine external data for an artwork from DBpedia, Wikidata, and Getty AAT.
    
    This endpoint:
    1. Queries the local Fuseki triplestore for owl:sameAs links
    2. Fetches data from each linked external source
    3. Returns combined enrichment data
    
    Results are cached for performance.
    """
)
async def enrich_artwork(
    artwork_id: str = Path(..., description="Artwork ID (e.g., 'artwork_mona_lisa')")
):
    """Enrich artwork data from external sources."""
    try:
        # Build full URI
        if not artwork_id.startswith("http"):
            artwork_uri = f"{ARP_NS}{artwork_id}"
        else:
            artwork_uri = artwork_id
        
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
        
        try:
            result = sparql_service.execute_query(query)
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error querying local triplestore: {str(e)}")
        
        if not result.get("results", {}).get("bindings"):
            raise HTTPException(status_code=404, detail=f"Artwork '{artwork_id}' not found")
        
        # Extract URIs from results
        dbpedia_uri = None
        wikidata_uri = None
        getty_uris = []
        artist_dbpedia_uri = None
        artist_wikidata_uri = None
        
        for binding in result["results"]["bindings"]:
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


# =============================================================================
# Cache Management
# =============================================================================

@router.post(
    "/cache/clear",
    summary="Clear external query cache",
    description="Clear all cached external query results."
)
async def clear_cache():
    """Clear the external query cache."""
    external_sparql_service.cache.clear()
    return {"message": "Cache cleared successfully"}


@router.post(
    "/cache/cleanup",
    summary="Cleanup expired cache entries",
    description="Remove expired entries from the cache."
)
async def cleanup_cache():
    """Remove expired entries from the cache."""
    removed = external_sparql_service.cache.cleanup()
    return {"message": f"Removed {removed} expired cache entries"}

