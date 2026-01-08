"""Artworks router."""

import io
from fastapi import APIRouter, HTTPException, Query, Request, Response
from fastapi.responses import JSONResponse
from typing import Optional, List
import qrcode
from rdflib import Graph, Namespace, Literal, URIRef
from rdflib.namespace import RDF, RDFS, XSD

from ..config import settings
from ..models.artwork import ArtworkCreate, ArtworkUpdate, ArtworkResponse, ArtworkListResponse
from ..models.provenance import ProvenanceRecord, ProvenanceEventCreate, ProvenanceEventUpdate
from ..models.external import ArtworkEnrichment, DBpediaArtworkInfo, WikidataArtworkInfo, GettyTerm, DBpediaArtistInfo, WikidataArtistInfo, LocalArtistInfo
from ..services.artwork_service import artwork_service
from ..services.external_sparql_service import external_sparql_service
from ..services.sparql_service import sparql_service

router = APIRouter(prefix="/artworks", tags=["artworks"])

# Namespaces for RDF serialization
SCHEMA = Namespace("https://schema.org/")
ARP = Namespace("http://example.org/arp#")
DC = Namespace("http://purl.org/dc/elements/1.1/")


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


def _artwork_to_jsonld(artwork: ArtworkResponse) -> dict:
    """Convert artwork to JSON-LD format."""
    jsonld = {
        "@context": "https://schema.org",
        "@type": "VisualArtwork",
        "@id": f"{settings.frontend_base_url}/artworks/{artwork.id}",
        "name": artwork.title,
    }
    if artwork.description:
        jsonld["description"] = artwork.description
    if artwork.artist:
        jsonld["creator"] = {"@type": "Person", "name": artwork.artist}
    if artwork.dateCreated:
        jsonld["dateCreated"] = artwork.dateCreated
    if artwork.medium:
        jsonld["artMedium"] = artwork.medium
    if artwork.currentLocation:
        jsonld["contentLocation"] = {"@type": "Place", "name": artwork.currentLocation}
    if artwork.imageUrl:
        jsonld["image"] = artwork.imageUrl
    if artwork.period:
        jsonld["temporalCoverage"] = artwork.period
    if artwork.style:
        jsonld["genre"] = artwork.style
    
    # Add sameAs links
    same_as = []
    if artwork.externalLinks:
        if artwork.externalLinks.dbpedia:
            same_as.append(artwork.externalLinks.dbpedia)
        if artwork.externalLinks.wikidata:
            same_as.append(artwork.externalLinks.wikidata)
        if artwork.externalLinks.getty:
            same_as.append(artwork.externalLinks.getty)
    if same_as:
        jsonld["sameAs"] = same_as
    
    return jsonld


def _artwork_to_rdf(artwork: ArtworkResponse, format: str = "turtle") -> str:
    """Convert artwork to RDF format (turtle or xml)."""
    g = Graph()
    g.bind("schema", SCHEMA)
    g.bind("arp", ARP)
    g.bind("dc", DC)
    
    artwork_uri = URIRef(f"{ARP}{artwork.id}")
    
    g.add((artwork_uri, RDF.type, SCHEMA.VisualArtwork))
    g.add((artwork_uri, SCHEMA.name, Literal(artwork.title)))
    
    if artwork.description:
        g.add((artwork_uri, SCHEMA.description, Literal(artwork.description)))
    if artwork.artist:
        g.add((artwork_uri, DC.creator, Literal(artwork.artist)))
    if artwork.dateCreated:
        g.add((artwork_uri, SCHEMA.dateCreated, Literal(artwork.dateCreated)))
    if artwork.medium:
        g.add((artwork_uri, SCHEMA.artMedium, Literal(artwork.medium)))
    if artwork.currentLocation:
        g.add((artwork_uri, SCHEMA.contentLocation, Literal(artwork.currentLocation)))
    if artwork.imageUrl:
        g.add((artwork_uri, SCHEMA.image, URIRef(artwork.imageUrl)))
    
    return g.serialize(format=format)


@router.get("/{artwork_id}/qr", tags=["sharing"])
async def get_artwork_qr(
    artwork_id: str,
    size: int = Query(256, ge=64, le=1024, description="QR code size in pixels")
):
    """
    Generate a QR code for the artwork's shareable URL.
    
    The QR code encodes the frontend URL for the artwork detail page.
    Scan with any QR reader to open the artwork page.
    """
    try:
        # Verify artwork exists
        artwork = artwork_service.get_artwork(artwork_id)
        if not artwork:
            raise HTTPException(status_code=404, detail=f"Artwork '{artwork_id}' not found")
        
        # Generate URL for QR code
        url = f"{settings.frontend_base_url}/artworks/{artwork_id}"
        
        # Create QR code
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(url)
        qr.make(fit=True)
        
        # Generate image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Resize if needed
        if size != 256:
            img = img.resize((size, size))
        
        # Save to buffer
        buffer = io.BytesIO()
        img.save(buffer, format="PNG")
        buffer.seek(0)
        
        return Response(
            content=buffer.getvalue(),
            media_type="image/png",
            headers={
                "Content-Disposition": f'inline; filename="{artwork_id}-qr.png"',
                "X-QR-URL": url
            }
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating QR code: {str(e)}")


@router.get("/{artwork_id}")
async def get_artwork(artwork_id: str, request: Request):
    """
    Get a single artwork by ID with content negotiation.
    
    Supports multiple formats via Accept header:
    - application/json (default)
    - application/ld+json (JSON-LD)
    - application/rdf+xml (RDF/XML)
    - text/turtle (Turtle RDF)
    """
    try:
        artwork = artwork_service.get_artwork(artwork_id)
        if not artwork:
            raise HTTPException(status_code=404, detail=f"Artwork '{artwork_id}' not found")
        
        # Content negotiation based on Accept header
        accept = request.headers.get("accept", "application/json")
        
        if "application/ld+json" in accept:
            return JSONResponse(
                content=_artwork_to_jsonld(artwork),
                media_type="application/ld+json"
            )
        elif "application/rdf+xml" in accept:
            return Response(
                content=_artwork_to_rdf(artwork, "xml"),
                media_type="application/rdf+xml"
            )
        elif "text/turtle" in accept:
            return Response(
                content=_artwork_to_rdf(artwork, "turtle"),
                media_type="text/turtle"
            )
        else:
            # Default: return JSON (Pydantic model)
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


# --- Recommendations Endpoint ---

@router.get("/{artwork_id}/recommendations", tags=["recommendations"])
async def get_recommendations(
    artwork_id: str,
    limit: int = Query(5, ge=1, le=20, description="Maximum number of recommendations")
):
    """
    Get artwork recommendations based on the specified artwork.
    
    Returns similar artworks that share the same artist, period, or style.
    Artworks are scored by similarity (same artist = 3, same period = 2, same style = 1)
    and returned in order of total score.
    
    **Path Parameters:**
    - `artwork_id`: The ID of the artwork to get recommendations for
    
    **Query Parameters:**
    - `limit` (optional): Maximum number of recommendations (default: 5, max: 20)
    
    **Response:**
    Array of similar artworks with their details.
    """
    try:
        # Verify artwork exists
        artwork = artwork_service.get_artwork(artwork_id)
        if not artwork:
            raise HTTPException(status_code=404, detail=f"Artwork '{artwork_id}' not found")
        
        return artwork_service.get_recommendations(artwork_id, limit=limit)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting recommendations: {str(e)}")


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
        
        # Query local Fuseki for owl:sameAs links, Getty material URIs, and local artist info
        query = f"""
        PREFIX owl: <{OWL_NS}>
        PREFIX schema: <{SCHEMA_NS}>
        PREFIX arp: <{ARP_NS}>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        
        SELECT ?sameAs ?artMedium ?artistUri ?artistSameAs 
               ?artistName ?artistBirthDate ?artistDeathDate ?artistNationality ?artistDescription WHERE {{
            <{artwork_uri}> a arp:Artwork .
            OPTIONAL {{ <{artwork_uri}> owl:sameAs ?sameAs }}
            OPTIONAL {{ <{artwork_uri}> schema:artMedium ?artMedium }}
            OPTIONAL {{ 
                <{artwork_uri}> dc:creator ?artistUri .
                OPTIONAL {{ ?artistUri owl:sameAs ?artistSameAs }}
                OPTIONAL {{ ?artistUri schema:name ?artistName }}
                OPTIONAL {{ ?artistUri schema:birthDate ?artistBirthDate }}
                OPTIONAL {{ ?artistUri schema:deathDate ?artistDeathDate }}
                OPTIONAL {{ ?artistUri schema:nationality ?artistNationality }}
                OPTIONAL {{ ?artistUri dc:description ?artistDescription }}
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
        local_artist_info = None
        
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
            
            # Extract local artist info (only once)
            if local_artist_info is None:
                artist_uri = binding.get("artistUri", {}).get("value")
                artist_name = binding.get("artistName", {}).get("value")
                if artist_uri or artist_name:
                    local_artist_info = LocalArtistInfo(
                        uri=artist_uri,
                        name=artist_name,
                        birthDate=binding.get("artistBirthDate", {}).get("value"),
                        deathDate=binding.get("artistDeathDate", {}).get("value"),
                        nationality=binding.get("artistNationality", {}).get("value"),
                        description=binding.get("artistDescription", {}).get("value")
                    )
        
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
        
        # Include local artist info
        if local_artist_info:
            enrichment.artist_local = local_artist_info
        
        return enrichment
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error enriching artwork: {str(e)}")
