"""Artwork service for RDF/SPARQL operations."""

import uuid
import re
from typing import Any, Dict, List, Optional

from ..models.artwork import (
    ArtworkCreate,
    ArtworkListResponse,
    ArtworkResponse,
    ExternalLinks,
)
from ..models.provenance import ProvenanceRecord
from .sparql_service import sparql_service

# RDF Namespaces and JSON-LD context
# Match the namespace used in fuseki/data/*.ttl files
ARP_NS = "http://example.org/arp#"
DC_NS = "http://purl.org/dc/elements/1.1/"
DCTERMS_NS = "http://purl.org/dc/terms/"
PROV_NS = "http://www.w3.org/ns/prov#"
SCHEMA_NS = "http://schema.org/"
OWL_NS = "http://www.w3.org/2002/07/owl#"

JSONLD_CONTEXT = {
    "@vocab": ARP_NS,
    "dc": DC_NS,
    "dcterms": DCTERMS_NS,
    "prov": PROV_NS,
    "schema": SCHEMA_NS,
    "title": "dc:title",
    "artist": "schema:name",
    "description": "dc:description",
    "dateCreated": "dcterms:created",
    "medium": "arp:artworkMedium",
    "dimensions": "arp:artworkDimensions",
    "currentLocation": "arp:currentLocation",
    "period": "arp:artworkPeriod",
    "style": "arp:artworkStyle",
    "imageUrl": "schema:image",
}


class ArtworkService:
    """Service for artwork CRUD operations using SPARQL."""

    def _generate_id(self) -> str:
        """Generate a unique artwork ID."""
        return f"artwork_{uuid.uuid4().hex[:12]}"

    def _uri_to_id(self, uri: str) -> str:
        """Extract ID from full URI."""
        if uri.startswith(ARP_NS):
            return uri.replace(ARP_NS, "")
        return uri

    def _id_to_uri(self, id: str) -> str:
        """Convert ID to full URI."""
        return f"{ARP_NS}{id}" if not id.startswith("http") else id

    def _escape_literal(self, value: str) -> str:
        """Escape special characters in SPARQL literals."""
        if value is None:
            return ""
        return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")

    def list_artworks(
        self,
        page: int = 1,
        limit: int = 20,
        artist: Optional[str] = None,
        period: Optional[str] = None,
        search: Optional[str] = None,
    ) -> ArtworkListResponse:
        """List artworks with pagination and optional filters."""
        offset = (page - 1) * limit

        # Build filter clauses
        filters = []
        if artist:
            filters.append(
                f'FILTER(CONTAINS(LCASE(?artist), LCASE("{self._escape_literal(artist)}")))'
            )
        if period:
            filters.append(
                f'FILTER(CONTAINS(LCASE(?period), LCASE("{self._escape_literal(period)}")))'
            )
        if search:
            filters.append(
                f'FILTER(CONTAINS(LCASE(?title), LCASE("{self._escape_literal(search)}")) || CONTAINS(LCASE(?description), LCASE("{self._escape_literal(search)}")))'
            )

        filter_clause = "\n".join(filters)

        # Count query - count unique artworks (prefer English titles to match main query)
        count_query = f"""
        PREFIX dc: <{DC_NS}>
        PREFIX dcterms: <{DCTERMS_NS}>
        PREFIX arp: <{ARP_NS}>
        PREFIX schema: <{SCHEMA_NS}>
        
        SELECT (COUNT(DISTINCT ?artwork) AS ?total) WHERE {{
            ?artwork a arp:Artwork .
            ?artwork dc:title ?title .
            # Prefer English title, fallback to any title if no English version exists
            FILTER(LANG(?title) = "en" || NOT EXISTS {{ ?artwork dc:title ?enTitle . FILTER(LANG(?enTitle) = "en") }})
            OPTIONAL {{ ?artwork dc:creator ?artistUri . ?artistUri schema:name ?artist }}
            OPTIONAL {{ ?artwork arp:artworkPeriod ?period }}
            OPTIONAL {{ 
                ?artwork dc:description ?description .
                FILTER(LANG(?description) = "en" || LANG(?description) = "" || NOT EXISTS {{ ?artwork dc:description ?enDesc . FILTER(LANG(?enDesc) = "en") }})
            }}
            {filter_clause}
        }}
        """

        count_result = sparql_service.execute_query(count_query)
        total = (
            int(count_result["results"]["bindings"][0]["total"]["value"])
            if count_result["results"]["bindings"]
            else 0
        )

        # Main query - prefer English titles to avoid duplicates from multi-language titles
        query = f"""
        PREFIX dc: <{DC_NS}>
        PREFIX dcterms: <{DCTERMS_NS}>
        PREFIX arp: <{ARP_NS}>
        PREFIX schema: <{SCHEMA_NS}>
        
        SELECT DISTINCT ?artwork ?title ?artist ?dateCreated ?medium ?dimensions 
               ?description ?imageUrl ?currentLocation ?period ?style
        WHERE {{
            ?artwork a arp:Artwork .
            ?artwork dc:title ?title .
            # Prefer English title, fallback to any title if no English version exists
            FILTER(LANG(?title) = "en" || NOT EXISTS {{ ?artwork dc:title ?enTitle . FILTER(LANG(?enTitle) = "en") }})
            OPTIONAL {{ ?artwork dc:creator ?artistUri . ?artistUri schema:name ?artist }}
            OPTIONAL {{ ?artwork dcterms:created ?dateCreated }}
            OPTIONAL {{ ?artwork arp:artworkMedium ?medium }}
            OPTIONAL {{ ?artwork arp:artworkDimensions ?dimensions }}
            OPTIONAL {{ 
                ?artwork dc:description ?description .
                FILTER(LANG(?description) = "en" || LANG(?description) = "" || NOT EXISTS {{ ?artwork dc:description ?enDesc . FILTER(LANG(?enDesc) = "en") }})
            }}
            OPTIONAL {{ ?artwork schema:image ?imageUrl }}
            OPTIONAL {{ ?artwork arp:currentLocation ?locUri . ?locUri schema:name ?currentLocation }}
            OPTIONAL {{ ?artwork arp:artworkPeriod ?period }}
            OPTIONAL {{ ?artwork arp:artworkStyle ?style }}
            {filter_clause}
        }}
        ORDER BY ?title
        LIMIT {limit}
        OFFSET {offset}
        """

        result = sparql_service.execute_query(query)

        items = []
        for binding in result["results"]["bindings"]:
            artwork = ArtworkResponse(
                id=self._uri_to_id(binding["artwork"]["value"]),
                title=binding["title"]["value"],
                artist=binding.get("artist", {}).get("value"),
                dateCreated=binding.get("dateCreated", {}).get("value"),
                medium=binding.get("medium", {}).get("value"),
                dimensions=binding.get("dimensions", {}).get("value"),
                description=binding.get("description", {}).get("value"),
                imageUrl=binding.get("imageUrl", {}).get("value"),
                currentLocation=binding.get("currentLocation", {}).get("value"),
                period=binding.get("period", {}).get("value"),
                style=binding.get("style", {}).get("value"),
            )
            items.append(artwork)

        return ArtworkListResponse(
            items=items,
            total=total,
            page=page,
            limit=limit,
            hasMore=(page * limit) < total,
            context=JSONLD_CONTEXT,
        )

    def get_artwork(self, artwork_id: str) -> Optional[ArtworkResponse]:
        """Get a single artwork by ID."""
        uri = self._id_to_uri(artwork_id)

        query = f"""
        PREFIX dc: <{DC_NS}>
        PREFIX dcterms: <{DCTERMS_NS}>
        PREFIX arp: <{ARP_NS}>
        PREFIX schema: <{SCHEMA_NS}>
        PREFIX owl: <{OWL_NS}>
        
        SELECT ?title ?artist ?dateCreated ?medium ?dimensions 
               ?description ?imageUrl ?currentLocation ?period ?style ?sameAs ?artMedium
        WHERE {{
            <{uri}> a arp:Artwork .
            <{uri}> dc:title ?title .
            # Prefer English title
            FILTER(LANG(?title) = "en" || NOT EXISTS {{ <{uri}> dc:title ?enTitle . FILTER(LANG(?enTitle) = "en") }})
            OPTIONAL {{ <{uri}> dc:creator ?artistUri . ?artistUri schema:name ?artist }}
            OPTIONAL {{ <{uri}> dcterms:created ?dateCreated }}
            OPTIONAL {{ <{uri}> arp:artworkMedium ?medium }}
            OPTIONAL {{ <{uri}> arp:artworkDimensions ?dimensions }}
            OPTIONAL {{ 
                <{uri}> dc:description ?description .
                FILTER(LANG(?description) = "en" || LANG(?description) = "" || NOT EXISTS {{ <{uri}> dc:description ?enDesc . FILTER(LANG(?enDesc) = "en") }})
            }}
            OPTIONAL {{ <{uri}> schema:image ?imageUrl }}
            OPTIONAL {{ <{uri}> arp:currentLocation ?locUri . ?locUri schema:name ?currentLocation }}
            OPTIONAL {{ <{uri}> arp:artworkPeriod ?period }}
            OPTIONAL {{ <{uri}> arp:artworkStyle ?style }}
            OPTIONAL {{ <{uri}> owl:sameAs ?sameAs }}
            OPTIONAL {{ <{uri}> schema:artMedium ?artMedium }}
        }}
        """

        result = sparql_service.execute_query(query)

        if not result["results"]["bindings"]:
            return None

        binding = result["results"]["bindings"][0]

        # Extract external links from all bindings (owl:sameAs may have multiple values)
        dbpedia_uri = None
        wikidata_uri = None
        getty_uri = None

        for b in result["results"]["bindings"]:
            same_as = b.get("sameAs", {}).get("value", "")
            if "dbpedia.org" in same_as and not dbpedia_uri:
                dbpedia_uri = same_as
            elif "wikidata.org" in same_as and not wikidata_uri:
                wikidata_uri = same_as

            art_medium = b.get("artMedium", {}).get("value", "")
            if "vocab.getty.edu" in art_medium and not getty_uri:
                getty_uri = art_medium

        # Build external links if any found
        external_links = None
        if dbpedia_uri or wikidata_uri or getty_uri:
            external_links = ExternalLinks(
                dbpedia=dbpedia_uri, wikidata=wikidata_uri, getty=getty_uri
            )

        return ArtworkResponse(
            id=artwork_id,
            title=binding["title"]["value"],
            artist=binding.get("artist", {}).get("value"),
            dateCreated=binding.get("dateCreated", {}).get("value"),
            medium=binding.get("medium", {}).get("value"),
            dimensions=binding.get("dimensions", {}).get("value"),
            description=binding.get("description", {}).get("value"),
            imageUrl=binding.get("imageUrl", {}).get("value"),
            currentLocation=binding.get("currentLocation", {}).get("value"),
            period=binding.get("period", {}).get("value"),
            style=binding.get("style", {}).get("value"),
            externalLinks=external_links,
            context=JSONLD_CONTEXT,
            type="Artwork",
        )

    def create_artwork(self, data: ArtworkCreate) -> ArtworkResponse:
        """Create a new artwork in Fuseki."""
        artwork_id = self._generate_id()
        uri = self._id_to_uri(artwork_id)

        triples = [
            f"<{uri}> a arp:Artwork",
            f'<{uri}> dc:title "{self._escape_literal(data.title)}"',
        ]

        if data.artist:
            triples.append(
                f'<{uri}> arp:artistName "{self._escape_literal(data.artist)}"'
            )
        if data.dateCreated:
            triples.append(
                f'<{uri}> dcterms:created "{self._escape_literal(data.dateCreated)}"'
            )
        if data.medium:
            triples.append(
                f'<{uri}> arp:artworkMedium "{self._escape_literal(data.medium)}"'
            )
        if data.dimensions:
            triples.append(
                f'<{uri}> arp:artworkDimensions "{self._escape_literal(data.dimensions)}"'
            )
        if data.description:
            triples.append(
                f'<{uri}> dc:description "{self._escape_literal(data.description)}"'
            )
        if data.imageUrl:
            triples.append(f"<{uri}> schema:image <{data.imageUrl}>")
        if data.currentLocation:
            triples.append(
                f'<{uri}> arp:currentLocationName "{self._escape_literal(data.currentLocation)}"'
            )
        if data.period:
            triples.append(
                f'<{uri}> arp:artworkPeriod "{self._escape_literal(data.period)}"'
            )
        if data.style:
            triples.append(
                f'<{uri}> arp:artworkStyle "{self._escape_literal(data.style)}"'
            )

        triples_str = " .\n    ".join(triples)

        update = f"""
        PREFIX dc: <{DC_NS}>
        PREFIX dcterms: <{DCTERMS_NS}>
        PREFIX arp: <{ARP_NS}>
        PREFIX schema: <{SCHEMA_NS}>
        
        INSERT DATA {{
            {triples_str} .
        }}
        """

        sparql_service.execute_update(update)

        return ArtworkResponse(
            id=artwork_id,
            title=data.title,
            artist=data.artist,
            dateCreated=data.dateCreated,
            medium=data.medium,
            dimensions=data.dimensions,
            description=data.description,
            imageUrl=data.imageUrl,
            currentLocation=data.currentLocation,
            period=data.period,
            style=data.style,
            context=JSONLD_CONTEXT,
            type="Artwork",
        )

    def get_provenance(self, artwork_id: str) -> List[ProvenanceRecord]:
        """Get provenance history for an artwork."""
        artwork_uri = self._id_to_uri(artwork_id)

        query = f"""
        PREFIX arp: <{ARP_NS}>
        PREFIX prov: <{PROV_NS}>
        PREFIX dc: <{DC_NS}>
        PREFIX schema: <{SCHEMA_NS}>
        
        SELECT ?event ?eventType ?date ?owner ?location ?description ?sourceUri ?order
        WHERE {{
            <{artwork_uri}> arp:hasProvenanceEvent ?event .
            ?event a arp:ProvenanceEvent .
            ?event arp:eventType ?eventType .
            OPTIONAL {{ ?event prov:startedAtTime ?date }}
            OPTIONAL {{ ?event arp:toOwner ?ownerUri . ?ownerUri schema:name ?owner }}
            OPTIONAL {{ ?event arp:eventLocation ?locUri . ?locUri schema:name ?location }}
            OPTIONAL {{ ?event dc:description ?description }}
            OPTIONAL {{ ?event arp:sourceUri ?sourceUri }}
            OPTIONAL {{ ?event arp:provenanceOrder ?order }}
        }}
        ORDER BY ?order ?date
        """

        result = sparql_service.execute_query(query)

        events = []
        for binding in result["results"]["bindings"]:
            event = ProvenanceRecord(
                id=self._uri_to_id(binding["event"]["value"]),
                event=binding["eventType"]["value"],
                date=binding.get("date", {}).get("value"),
                owner=binding.get("owner", {}).get("value"),
                location=binding.get("location", {}).get("value"),
                description=binding.get("description", {}).get("value"),
                sourceUri=binding.get("sourceUri", {}).get("value"),
                order=int(binding["order"]["value"]) if "order" in binding else None,
            )
            events.append(event)

        return events

    def update_artwork(
        self, artwork_id: str, data: "ArtworkUpdate"
    ) -> Optional[ArtworkResponse]:
        """Update an existing artwork."""
        existing = self.get_artwork(artwork_id)
        if not existing:
            return None

        uri = self._id_to_uri(artwork_id)

        delete_triples = []
        insert_triples = []

        field_mappings = {
            "title": ("dc:title", data.title),
            "artist": ("arp:artistName", data.artist),
            "dateCreated": ("dcterms:created", data.dateCreated),
            "medium": ("arp:artworkMedium", data.medium),
            "dimensions": ("arp:artworkDimensions", data.dimensions),
            "description": ("dc:description", data.description),
            "imageUrl": ("schema:image", data.imageUrl),
            "currentLocation": ("arp:currentLocationName", data.currentLocation),
            "period": ("arp:artworkPeriod", data.period),
            "style": ("arp:artworkStyle", data.style),
        }

        for field, (predicate, value) in field_mappings.items():
            if value is not None:
                delete_triples.append(f"<{uri}> {predicate} ?old_{field}")
                insert_triples.append(
                    f'<{uri}> {predicate} "{self._escape_literal(value)}"'
                )

        if not insert_triples:
            return existing

        delete_clause = " .\n        ".join(delete_triples)
        insert_clause = " .\n        ".join(insert_triples)
        optional_clauses = "\n        ".join(
            [f"OPTIONAL {{ {t} }}" for t in delete_triples]
        )

        update = f"""
        PREFIX dc: <{DC_NS}>
        PREFIX dcterms: <{DCTERMS_NS}>
        PREFIX arp: <{ARP_NS}>
        PREFIX schema: <{SCHEMA_NS}>
        
        DELETE {{
            {delete_clause} .
        }}
        INSERT {{
            {insert_clause} .
        }}
        WHERE {{
            <{uri}> a arp:Artwork .
            {optional_clauses}
        }}
        """

        sparql_service.execute_update(update)
        return self.get_artwork(artwork_id)

    def delete_artwork(self, artwork_id: str) -> bool:
        """Delete an artwork and its provenance."""
        uri = self._id_to_uri(artwork_id)

        existing = self.get_artwork(artwork_id)
        if not existing:
            return False

        update = f"""
        PREFIX arp: <{ARP_NS}>
        
        DELETE {{
            <{uri}> ?p ?o .
            ?prov ?pp ?po .
        }}
        WHERE {{
            <{uri}> ?p ?o .
            OPTIONAL {{
                <{uri}> arp:hasProvenanceEvent ?prov .
                ?prov ?pp ?po .
            }}
        }}
        """

        sparql_service.execute_update(update)
        return True

    def add_provenance_event(
        self, artwork_id: str, data: "ProvenanceEventCreate"
    ) -> ProvenanceRecord:
        """Add a provenance event to an artwork."""
        from ..models.provenance import ProvenanceEventCreate

        artwork_uri = self._id_to_uri(artwork_id)
        event_id = f"provenance_{uuid.uuid4().hex[:12]}"
        event_uri = f"{ARP_NS}{event_id}"

        order_query = f"""
        PREFIX arp: <{ARP_NS}>
        
        SELECT (MAX(?order) AS ?maxOrder) WHERE {{
            <{artwork_uri}> arp:hasProvenanceEvent ?event .
            OPTIONAL {{ ?event arp:provenanceOrder ?order }}
        }}
        """
        order_result = sparql_service.execute_query(order_query)
        max_order = 0
        if order_result["results"]["bindings"]:
            max_val = (
                order_result["results"]["bindings"][0].get("maxOrder", {}).get("value")
            )
            if max_val:
                max_order = int(max_val)
        new_order = max_order + 1

        triples = [
            f"<{artwork_uri}> arp:hasProvenanceEvent <{event_uri}>",
            f"<{event_uri}> a arp:ProvenanceEvent",
            f'<{event_uri}> arp:eventType "{self._escape_literal(data.event.value)}"',
            f'<{event_uri}> prov:startedAtTime "{self._escape_literal(data.date)}"',
            f"<{event_uri}> arp:provenanceOrder {new_order}",
        ]

        if data.owner:
            triples.append(
                f'<{event_uri}> arp:owner "{self._escape_literal(data.owner)}"'
            )
        if data.location:
            triples.append(
                f'<{event_uri}> arp:location "{self._escape_literal(data.location)}"'
            )
        if data.description:
            triples.append(
                f'<{event_uri}> arp:description "{self._escape_literal(data.description)}"'
            )
        if data.sourceUri:
            triples.append(
                f'<{event_uri}> arp:sourceUri "{self._escape_literal(data.sourceUri)}"'
            )

        triples_str = " .\n        ".join(triples)

        update = f"""
        PREFIX arp: <{ARP_NS}>
        PREFIX prov: <{PROV_NS}>
        
        INSERT DATA {{
            {triples_str} .
        }}
        """

        sparql_service.execute_update(update)

        return ProvenanceRecord(
            id=event_id,
            event=data.event,
            date=data.date,
            owner=data.owner,
            location=data.location,
            description=data.description,
            sourceUri=data.sourceUri,
            order=new_order,
        )

    def update_provenance_event(
        self, artwork_id: str, event_id: str, data: "ProvenanceEventUpdate"
    ) -> Optional[ProvenanceRecord]:
        """Update a provenance event."""
        from ..models.provenance import ProvenanceEventUpdate

        event_uri = self._id_to_uri(event_id)

        check_query = f"""
        PREFIX arp: <{ARP_NS}>
        
        ASK {{ <{event_uri}> a arp:ProvenanceEvent }}
        """
        try:
            result = sparql_service.execute_query(check_query)
            if not result.get("boolean", False):
                return None
        except:
            return None

        delete_triples = []
        insert_triples = []

        if data.event is not None:
            delete_triples.append(f"<{event_uri}> arp:eventType ?oldEventType")
            insert_triples.append(
                f'<{event_uri}> arp:eventType "{self._escape_literal(data.event.value)}"'
            )
        if data.date is not None:
            delete_triples.append(f"<{event_uri}> prov:startedAtTime ?oldDate")
            insert_triples.append(
                f'<{event_uri}> prov:startedAtTime "{self._escape_literal(data.date)}"'
            )
        if data.owner is not None:
            delete_triples.append(f"<{event_uri}> arp:owner ?oldOwner")
            insert_triples.append(
                f'<{event_uri}> arp:owner "{self._escape_literal(data.owner)}"'
            )
        if data.location is not None:
            delete_triples.append(f"<{event_uri}> arp:location ?oldLocation")
            insert_triples.append(
                f'<{event_uri}> arp:location "{self._escape_literal(data.location)}"'
            )
        if data.description is not None:
            delete_triples.append(f"<{event_uri}> arp:description ?oldDescription")
            insert_triples.append(
                f'<{event_uri}> arp:description "{self._escape_literal(data.description)}"'
            )
        if data.sourceUri is not None:
            delete_triples.append(f"<{event_uri}> arp:sourceUri ?oldSourceUri")
            insert_triples.append(
                f'<{event_uri}> arp:sourceUri "{self._escape_literal(data.sourceUri)}"'
            )

        if not insert_triples:
            events = self.get_provenance(artwork_id)
            return next((e for e in events if e.id == event_id), None)

        delete_clause = " .\n        ".join(delete_triples)
        insert_clause = " .\n        ".join(insert_triples)
        optional_clauses = "\n        ".join(
            [f"OPTIONAL {{ {t} }}" for t in delete_triples]
        )

        update = f"""
        PREFIX arp: <{ARP_NS}>
        PREFIX prov: <{PROV_NS}>
        
        DELETE {{
            {delete_clause} .
        }}
        INSERT {{
            {insert_clause} .
        }}
        WHERE {{
            <{event_uri}> a arp:ProvenanceEvent .
            {optional_clauses}
        }}
        """

        sparql_service.execute_update(update)

        events = self.get_provenance(artwork_id)
        return next((e for e in events if e.id == event_id), None)

    def delete_provenance_event(self, artwork_id: str, event_id: str) -> bool:
        """Delete a provenance event."""
        artwork_uri = self._id_to_uri(artwork_id)
        event_uri = self._id_to_uri(event_id)

        update = f"""
        PREFIX arp: <{ARP_NS}>
        
        DELETE {{
            <{artwork_uri}> arp:hasProvenanceEvent <{event_uri}> .
            <{event_uri}> ?p ?o .
        }}
        WHERE {{
            <{artwork_uri}> arp:hasProvenanceEvent <{event_uri}> .
            <{event_uri}> ?p ?o .
        }}
        """

        sparql_service.execute_update(update)
        return True

    def search_artworks(
        self,
        q: Optional[str],
        fields: Optional[List[str]] = None,
        page: int = 1,
        limit: int = 20,
        artist: Optional[str] = None,
        period: Optional[str] = None,
        medium: Optional[str] = None,
        location: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Full-text search across artworks with faceted filtering."""
        from ..models.artwork import FacetItem, SearchFacets, SearchResponse

        offset = (page - 1) * limit

        if not fields:
            fields = ["title", "artist", "description"]

        field_mappings = {
            "title": "?title",
            "artist": "?artist",
            "description": "?description",
        }

        # Build search filter expression (only if q is provided)
        search_filter_clause = ""
        filter_expression = ""
        if q:
            search_filters = []
            for field in fields:
                if field in field_mappings:
                    var = field_mappings[field]
                    search_filters.append(
                        f'CONTAINS(LCASE({var}), LCASE("{self._escape_literal(q)}"))'
                    )

            if not search_filters:
                search_filters = [
                    f'CONTAINS(LCASE(?title), LCASE("{self._escape_literal(q)}"))'
                ]

            filter_expression = " || ".join(search_filters)
            search_filter_clause = f"FILTER({filter_expression})"

        # Build additional filter clauses
        additional_filters = []
        if artist:
            additional_filters.append(
                f'FILTER(CONTAINS(LCASE(?artist), LCASE("{self._escape_literal(artist)}")))'
            )
        if period:
            additional_filters.append(
                f'FILTER(CONTAINS(LCASE(?period), LCASE("{self._escape_literal(period)}")))'
            )
        if medium:
            additional_filters.append(
                f'FILTER(CONTAINS(LCASE(?medium), LCASE("{self._escape_literal(medium)}")))'
            )
        if location:
            additional_filters.append(
                f'FILTER(CONTAINS(LCASE(?currentLocation), LCASE("{self._escape_literal(location)}")))'
            )

        additional_filter_clause = "\n            ".join(additional_filters)

        count_query = f"""
        PREFIX dc: <{DC_NS}>
        PREFIX dcterms: <{DCTERMS_NS}>
        PREFIX arp: <{ARP_NS}>
        PREFIX schema: <{SCHEMA_NS}>
        
        SELECT (COUNT(DISTINCT ?artwork) AS ?total) WHERE {{
            ?artwork a arp:Artwork .
            ?artwork dc:title ?title .
            FILTER(LANG(?title) = "en" || NOT EXISTS {{ ?artwork dc:title ?enTitle . FILTER(LANG(?enTitle) = "en") }})
            OPTIONAL {{ ?artwork dc:creator ?artistUri . ?artistUri schema:name ?artist }}
            OPTIONAL {{ ?artwork arp:artworkMedium ?medium }}
            OPTIONAL {{ ?artwork arp:currentLocation ?locUri . ?locUri schema:name ?currentLocation }}
            OPTIONAL {{ ?artwork arp:artworkPeriod ?period }}
            OPTIONAL {{ 
                ?artwork dc:description ?description .
                FILTER(LANG(?description) = "en" || LANG(?description) = "" || NOT EXISTS {{ ?artwork dc:description ?enDesc . FILTER(LANG(?enDesc) = "en") }})
            }}
            {search_filter_clause}
            {additional_filter_clause}
        }}
        """

        count_result = sparql_service.execute_query(count_query)
        total = (
            int(count_result["results"]["bindings"][0]["total"]["value"])
            if count_result["results"]["bindings"]
            else 0
        )

        query = f"""
        PREFIX dc: <{DC_NS}>
        PREFIX dcterms: <{DCTERMS_NS}>
        PREFIX arp: <{ARP_NS}>
        PREFIX schema: <{SCHEMA_NS}>
        
        SELECT DISTINCT ?artwork ?title ?artist ?dateCreated ?medium ?dimensions 
               ?description ?imageUrl ?currentLocation ?period ?style
        WHERE {{
            ?artwork a arp:Artwork .
            ?artwork dc:title ?title .
            FILTER(LANG(?title) = "en" || NOT EXISTS {{ ?artwork dc:title ?enTitle . FILTER(LANG(?enTitle) = "en") }})
            OPTIONAL {{ ?artwork dc:creator ?artistUri . ?artistUri schema:name ?artist }}
            OPTIONAL {{ ?artwork dcterms:created ?dateCreated }}
            OPTIONAL {{ ?artwork arp:artworkMedium ?medium }}
            OPTIONAL {{ ?artwork arp:artworkDimensions ?dimensions }}
            OPTIONAL {{ 
                ?artwork dc:description ?description .
                FILTER(LANG(?description) = "en" || LANG(?description) = "" || NOT EXISTS {{ ?artwork dc:description ?enDesc . FILTER(LANG(?enDesc) = "en") }})
            }}
            OPTIONAL {{ ?artwork schema:image ?imageUrl }}
            OPTIONAL {{ ?artwork arp:currentLocation ?locUri . ?locUri schema:name ?currentLocation }}
            OPTIONAL {{ ?artwork arp:artworkPeriod ?period }}
            OPTIONAL {{ ?artwork arp:artworkStyle ?style }}
            {search_filter_clause}
            {additional_filter_clause}
        }}
        ORDER BY ?title
        LIMIT {limit}
        OFFSET {offset}
        """

        result = sparql_service.execute_query(query)

        items = []
        for binding in result["results"]["bindings"]:
            artwork = {
                "id": self._uri_to_id(binding["artwork"]["value"]),
                "title": binding["title"]["value"],
                "artist": binding.get("artist", {}).get("value"),
                "dateCreated": binding.get("dateCreated", {}).get("value"),
                "medium": binding.get("medium", {}).get("value"),
                "dimensions": binding.get("dimensions", {}).get("value"),
                "description": binding.get("description", {}).get("value"),
                "imageUrl": binding.get("imageUrl", {}).get("value"),
                "currentLocation": binding.get("currentLocation", {}).get("value"),
                "period": binding.get("period", {}).get("value"),
                "style": binding.get("style", {}).get("value"),
            }
            items.append(artwork)

        # Get facets
        facets = self._get_facets(q, search_filter_clause)

        return SearchResponse(
            query=q if q else "",
            total=total,
            page=page,
            limit=limit,
            results=items,
            facets=facets,
        ).model_dump()

    def _get_facets(self, q: Optional[str], search_filter_clause: str) -> "SearchFacets":
        """Get facet counts for search results."""
        from ..models.artwork import FacetItem, SearchFacets

        facets = SearchFacets()

        # Artist facets
        artist_query = f"""
        PREFIX dc: <{DC_NS}>
        PREFIX arp: <{ARP_NS}>
        PREFIX schema: <{SCHEMA_NS}>
        
        SELECT ?artist (COUNT(DISTINCT ?artwork) AS ?count) WHERE {{
            ?artwork a arp:Artwork .
            ?artwork dc:title ?title .
            FILTER(LANG(?title) = "en" || NOT EXISTS {{ ?artwork dc:title ?enTitle . FILTER(LANG(?enTitle) = "en") }})
            ?artwork dc:creator ?artistUri .
            ?artistUri schema:name ?artist .
            OPTIONAL {{ 
                ?artwork dc:description ?description .
                FILTER(LANG(?description) = "en" || LANG(?description) = "" || NOT EXISTS {{ ?artwork dc:description ?enDesc . FILTER(LANG(?enDesc) = "en") }})
            }}
            {search_filter_clause}
        }}
        GROUP BY ?artist
        ORDER BY DESC(?count)
        LIMIT 20
        """
        try:
            result = sparql_service.execute_query(artist_query)
            for binding in result["results"]["bindings"]:
                name = binding.get("artist", {}).get("value")
                count = binding.get("count", {}).get("value")
                if name and count:
                    facets.artists.append(FacetItem(name=name, count=int(count)))
        except Exception:
            pass

        # Period facets
        period_query = f"""
        PREFIX dc: <{DC_NS}>
        PREFIX arp: <{ARP_NS}>
        PREFIX schema: <{SCHEMA_NS}>
        
        SELECT ?period (COUNT(DISTINCT ?artwork) AS ?count) WHERE {{
            ?artwork a arp:Artwork .
            ?artwork dc:title ?title .
            FILTER(LANG(?title) = "en" || NOT EXISTS {{ ?artwork dc:title ?enTitle . FILTER(LANG(?enTitle) = "en") }})
            ?artwork arp:artworkPeriod ?period .
            OPTIONAL {{ ?artwork dc:creator ?artistUri . ?artistUri schema:name ?artist }}
            OPTIONAL {{ 
                ?artwork dc:description ?description .
                FILTER(LANG(?description) = "en" || LANG(?description) = "" || NOT EXISTS {{ ?artwork dc:description ?enDesc . FILTER(LANG(?enDesc) = "en") }})
            }}
            {search_filter_clause}
        }}
        GROUP BY ?period
        ORDER BY DESC(?count)
        LIMIT 20
        """
        try:
            result = sparql_service.execute_query(period_query)
            for binding in result["results"]["bindings"]:
                name = binding.get("period", {}).get("value")
                count = binding.get("count", {}).get("value")
                if name and count:
                    facets.periods.append(FacetItem(name=name, count=int(count)))
        except Exception:
            pass

        # Medium facets
        medium_query = f"""
        PREFIX dc: <{DC_NS}>
        PREFIX arp: <{ARP_NS}>
        PREFIX schema: <{SCHEMA_NS}>
        
        SELECT ?medium (COUNT(DISTINCT ?artwork) AS ?count) WHERE {{
            ?artwork a arp:Artwork .
            ?artwork dc:title ?title .
            FILTER(LANG(?title) = "en" || NOT EXISTS {{ ?artwork dc:title ?enTitle . FILTER(LANG(?enTitle) = "en") }})
            ?artwork arp:artworkMedium ?medium .
            OPTIONAL {{ ?artwork dc:creator ?artistUri . ?artistUri schema:name ?artist }}
            OPTIONAL {{ 
                ?artwork dc:description ?description .
                FILTER(LANG(?description) = "en" || LANG(?description) = "" || NOT EXISTS {{ ?artwork dc:description ?enDesc . FILTER(LANG(?enDesc) = "en") }})
            }}
            {search_filter_clause}
        }}
        GROUP BY ?medium
        ORDER BY DESC(?count)
        LIMIT 20
        """
        try:
            result = sparql_service.execute_query(medium_query)
            for binding in result["results"]["bindings"]:
                name = binding.get("medium", {}).get("value")
                count = binding.get("count", {}).get("value")
                if name and count:
                    facets.media.append(FacetItem(name=name, count=int(count)))
        except Exception:
            pass

        # Location facets
        location_query = f"""
        PREFIX dc: <{DC_NS}>
        PREFIX arp: <{ARP_NS}>
        PREFIX schema: <{SCHEMA_NS}>
        
        SELECT ?location (COUNT(DISTINCT ?artwork) AS ?count) WHERE {{
            ?artwork a arp:Artwork .
            ?artwork dc:title ?title .
            FILTER(LANG(?title) = "en" || NOT EXISTS {{ ?artwork dc:title ?enTitle . FILTER(LANG(?enTitle) = "en") }})
            ?artwork arp:currentLocation ?locUri .
            ?locUri schema:name ?location .
            OPTIONAL {{ ?artwork dc:creator ?artistUri . ?artistUri schema:name ?artist }}
            OPTIONAL {{ 
                ?artwork dc:description ?description .
                FILTER(LANG(?description) = "en" || LANG(?description) = "" || NOT EXISTS {{ ?artwork dc:description ?enDesc . FILTER(LANG(?enDesc) = "en") }})
            }}
            {search_filter_clause}
        }}
        GROUP BY ?location
        ORDER BY DESC(?count)
        LIMIT 20
        """
        try:
            result = sparql_service.execute_query(location_query)
            for binding in result["results"]["bindings"]:
                name = binding.get("location", {}).get("value")
                count = binding.get("count", {}).get("value")
                if name and count:
                    facets.locations.append(FacetItem(name=name, count=int(count)))
        except Exception:
            pass

        return facets

    def _extract_keywords(self, text: str) -> List[str]:
        """Extract significant keywords from text."""
        if not text:
            return []
        
        # Simple stop words list
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "of", 
            "for", "with", "is", "was", "are", "were", "by", "from", "as", "it", 
            "that", "this", "which", "be", "has", "have", "had", "not", "but"
        }
        
        # Tokenize and clean
        words = re.findall(r'\b[a-zA-Z]{3,}\b', text.lower())
        keywords = [w for w in words if w not in stop_words]
        
        # Return unique keywords, top 5
        return list(set(keywords))[:5]

    def get_recommendations(
        self, artwork_id: str, limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get recommendations for similar artworks based on artist, period, and style."""
        # Get the source artwork to find its attributes
        source = self.get_artwork(artwork_id)
        if not source:
            return []

        source_uri = self._id_to_uri(artwork_id)
        
        # Build conditions for finding similar artworks
        union_clauses = []
        
        if source.description:
            # Description keywords
            keywords = self._extract_keywords(source.description)
            if keywords:
                # Construct values string for SPARQL: "kw1" "kw2" ...
                values_str = " ".join([f'"{kw}"' for kw in keywords])
                union_clauses.append(f"""
                    {{
                        ?artwork dc:description ?desc .
                        VALUES ?keyword {{ {values_str} }}
                        FILTER(CONTAINS(LCASE(?desc), ?keyword))
                        BIND(2 AS ?score)
                    }}
                """)

        if source.artist:
            # Same artist
            union_clauses.append(f"""
                {{
                    ?artwork dc:creator ?artistUri .
                    ?artistUri schema:name ?matchArtist .
                    FILTER(LCASE(?matchArtist) = LCASE("{self._escape_literal(source.artist)}"))
                    BIND(3 AS ?score)
                }}
            """)
        
        if source.period:
            # Same period
            union_clauses.append(f"""
                {{
                    ?artwork arp:artworkPeriod ?matchPeriod .
                    FILTER(LCASE(?matchPeriod) = LCASE("{self._escape_literal(source.period)}"))
                    BIND(1 AS ?score)
                }}
            """)
        
        if source.style:
            # Same style
            union_clauses.append(f"""
                {{
                    ?artwork arp:artworkStyle ?matchStyle .
                    FILTER(CONTAINS(LCASE(?matchStyle), LCASE("{self._escape_literal(source.style)}")))
                    BIND(1 AS ?score)
                }}
            """)

        if not union_clauses:
            return []

        union_clause = " UNION ".join(union_clauses)

        query = f"""
        PREFIX dc: <{DC_NS}>
        PREFIX dcterms: <{DCTERMS_NS}>
        PREFIX arp: <{ARP_NS}>
        PREFIX schema: <{SCHEMA_NS}>
        
        SELECT DISTINCT ?artwork ?title ?artist ?dateCreated ?medium ?dimensions 
               ?description ?imageUrl ?currentLocation ?period ?style (SUM(?score) AS ?totalScore)
        WHERE {{
            ?artwork a arp:Artwork .
            ?artwork dc:title ?title .
            FILTER(LANG(?title) = "en" || NOT EXISTS {{ ?artwork dc:title ?enTitle . FILTER(LANG(?enTitle) = "en") }})
            FILTER(?artwork != <{source_uri}>)
            
            {union_clause}
            
            OPTIONAL {{ ?artwork dc:creator ?artistUri . ?artistUri schema:name ?artist }}
            OPTIONAL {{ ?artwork dcterms:created ?dateCreated }}
            OPTIONAL {{ ?artwork arp:artworkMedium ?medium }}
            OPTIONAL {{ ?artwork arp:artworkDimensions ?dimensions }}
            OPTIONAL {{ 
                ?artwork dc:description ?description .
                FILTER(LANG(?description) = "en" || LANG(?description) = "" || NOT EXISTS {{ ?artwork dc:description ?enDesc . FILTER(LANG(?enDesc) = "en") }})
            }}
            OPTIONAL {{ ?artwork schema:image ?imageUrl }}
            OPTIONAL {{ ?artwork arp:currentLocation ?locUri . ?locUri schema:name ?currentLocation }}
            OPTIONAL {{ ?artwork arp:artworkPeriod ?period }}
            OPTIONAL {{ ?artwork arp:artworkStyle ?style }}
        }}
        GROUP BY ?artwork ?title ?artist ?dateCreated ?medium ?dimensions ?description ?imageUrl ?currentLocation ?period ?style
        ORDER BY DESC(?totalScore)
        LIMIT {limit}
        """

        result = sparql_service.execute_query(query)

        recommendations = []
        for binding in result["results"]["bindings"]:
            artwork = {
                "id": self._uri_to_id(binding["artwork"]["value"]),
                "title": binding["title"]["value"],
                "artist": binding.get("artist", {}).get("value"),
                "dateCreated": binding.get("dateCreated", {}).get("value"),
                "medium": binding.get("medium", {}).get("value"),
                "dimensions": binding.get("dimensions", {}).get("value"),
                "description": binding.get("description", {}).get("value"),
                "imageUrl": binding.get("imageUrl", {}).get("value"),
                "currentLocation": binding.get("currentLocation", {}).get("value"),
                "period": binding.get("period", {}).get("value"),
                "style": binding.get("style", {}).get("value"),
            }
            recommendations.append(artwork)

        return recommendations


artwork_service = ArtworkService()
