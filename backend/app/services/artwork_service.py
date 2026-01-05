"""Artwork service for RDF/SPARQL operations."""

import uuid
from typing import Optional, List, Dict, Any

from ..models.artwork import ArtworkCreate, ArtworkResponse, ArtworkListResponse
from ..models.provenance import ProvenanceRecord
from .sparql_service import sparql_service


# RDF Namespaces and JSON-LD context
ARP_NS = "http://arp.example.org/ontology#"
ARP_DATA = "http://arp.example.org/data/"
DC_NS = "http://purl.org/dc/elements/1.1/"
PROV_NS = "http://www.w3.org/ns/prov#"

JSONLD_CONTEXT = {
    "@vocab": ARP_NS,
    "dc": DC_NS,
    "prov": PROV_NS,
    "title": "dc:title",
    "artist": "dc:creator",
    "description": "dc:description",
    "dateCreated": "dc:date",
    "medium": "arp:medium",
    "dimensions": "arp:dimensions",
    "currentLocation": "arp:currentLocation",
    "period": "arp:period",
    "style": "arp:style",
    "imageUrl": "arp:imageUrl"
}


class ArtworkService:
    """Service for artwork CRUD operations using SPARQL."""
    
    def _generate_id(self) -> str:
        """Generate a unique artwork ID."""
        return f"artwork_{uuid.uuid4().hex[:12]}"
    
    def _uri_to_id(self, uri: str) -> str:
        """Extract ID from full URI."""
        return uri.replace(ARP_DATA, "") if uri.startswith(ARP_DATA) else uri
    
    def _id_to_uri(self, id: str) -> str:
        """Convert ID to full URI."""
        return f"{ARP_DATA}{id}" if not id.startswith("http") else id
    
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
        search: Optional[str] = None
    ) -> ArtworkListResponse:
        """List artworks with pagination and optional filters."""
        offset = (page - 1) * limit
        
        # Build filter clauses
        filters = []
        if artist:
            filters.append(f'FILTER(CONTAINS(LCASE(?artist), LCASE("{self._escape_literal(artist)}")))')
        if period:
            filters.append(f'FILTER(CONTAINS(LCASE(?period), LCASE("{self._escape_literal(period)}")))')
        if search:
            filters.append(f'FILTER(CONTAINS(LCASE(?title), LCASE("{self._escape_literal(search)}")) || CONTAINS(LCASE(?description), LCASE("{self._escape_literal(search)}")))')
        
        filter_clause = "\n".join(filters)
        
        # Count query
        count_query = f"""
        PREFIX dc: <{DC_NS}>
        PREFIX arp: <{ARP_NS}>
        
        SELECT (COUNT(DISTINCT ?artwork) AS ?total) WHERE {{
            ?artwork a arp:Artwork .
            ?artwork dc:title ?title .
            OPTIONAL {{ ?artwork dc:creator ?artist }}
            OPTIONAL {{ ?artwork arp:period ?period }}
            OPTIONAL {{ ?artwork dc:description ?description }}
            {filter_clause}
        }}
        """
        
        count_result = sparql_service.execute_query(count_query)
        total = int(count_result["results"]["bindings"][0]["total"]["value"]) if count_result["results"]["bindings"] else 0
        
        # Main query
        query = f"""
        PREFIX dc: <{DC_NS}>
        PREFIX arp: <{ARP_NS}>
        
        SELECT DISTINCT ?artwork ?title ?artist ?dateCreated ?medium ?dimensions 
               ?description ?imageUrl ?currentLocation ?period ?style
        WHERE {{
            ?artwork a arp:Artwork .
            ?artwork dc:title ?title .
            OPTIONAL {{ ?artwork dc:creator ?artist }}
            OPTIONAL {{ ?artwork dc:date ?dateCreated }}
            OPTIONAL {{ ?artwork arp:medium ?medium }}
            OPTIONAL {{ ?artwork arp:dimensions ?dimensions }}
            OPTIONAL {{ ?artwork dc:description ?description }}
            OPTIONAL {{ ?artwork arp:imageUrl ?imageUrl }}
            OPTIONAL {{ ?artwork arp:currentLocation ?currentLocation }}
            OPTIONAL {{ ?artwork arp:period ?period }}
            OPTIONAL {{ ?artwork arp:style ?style }}
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
            context=JSONLD_CONTEXT
        )
    
    def get_artwork(self, artwork_id: str) -> Optional[ArtworkResponse]:
        """Get a single artwork by ID."""
        uri = self._id_to_uri(artwork_id)
        
        query = f"""
        PREFIX dc: <{DC_NS}>
        PREFIX arp: <{ARP_NS}>
        
        SELECT ?title ?artist ?dateCreated ?medium ?dimensions 
               ?description ?imageUrl ?currentLocation ?period ?style
        WHERE {{
            <{uri}> a arp:Artwork .
            <{uri}> dc:title ?title .
            OPTIONAL {{ <{uri}> dc:creator ?artist }}
            OPTIONAL {{ <{uri}> dc:date ?dateCreated }}
            OPTIONAL {{ <{uri}> arp:medium ?medium }}
            OPTIONAL {{ <{uri}> arp:dimensions ?dimensions }}
            OPTIONAL {{ <{uri}> dc:description ?description }}
            OPTIONAL {{ <{uri}> arp:imageUrl ?imageUrl }}
            OPTIONAL {{ <{uri}> arp:currentLocation ?currentLocation }}
            OPTIONAL {{ <{uri}> arp:period ?period }}
            OPTIONAL {{ <{uri}> arp:style ?style }}
        }}
        """
        
        result = sparql_service.execute_query(query)
        
        if not result["results"]["bindings"]:
            return None
        
        binding = result["results"]["bindings"][0]
        
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
            context=JSONLD_CONTEXT,
            type="Artwork"
        )
    
    def create_artwork(self, data: ArtworkCreate) -> ArtworkResponse:
        """Create a new artwork in Fuseki."""
        artwork_id = self._generate_id()
        uri = self._id_to_uri(artwork_id)
        
        # Build INSERT query with triples
        triples = [
            f'<{uri}> a arp:Artwork',
            f'<{uri}> dc:title "{self._escape_literal(data.title)}"'
        ]
        
        if data.artist:
            triples.append(f'<{uri}> dc:creator "{self._escape_literal(data.artist)}"')
        if data.dateCreated:
            triples.append(f'<{uri}> dc:date "{self._escape_literal(data.dateCreated)}"')
        if data.medium:
            triples.append(f'<{uri}> arp:medium "{self._escape_literal(data.medium)}"')
        if data.dimensions:
            triples.append(f'<{uri}> arp:dimensions "{self._escape_literal(data.dimensions)}"')
        if data.description:
            triples.append(f'<{uri}> dc:description "{self._escape_literal(data.description)}"')
        if data.imageUrl:
            triples.append(f'<{uri}> arp:imageUrl "{self._escape_literal(data.imageUrl)}"')
        if data.currentLocation:
            triples.append(f'<{uri}> arp:currentLocation "{self._escape_literal(data.currentLocation)}"')
        if data.period:
            triples.append(f'<{uri}> arp:period "{self._escape_literal(data.period)}"')
        if data.style:
            triples.append(f'<{uri}> arp:style "{self._escape_literal(data.style)}"')
        
        triples_str = " .\n    ".join(triples)
        
        update = f"""
        PREFIX dc: <{DC_NS}>
        PREFIX arp: <{ARP_NS}>
        
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
            type="Artwork"
        )
    
    def get_provenance(self, artwork_id: str) -> List[ProvenanceRecord]:
        """Get provenance history for an artwork."""
        artwork_uri = self._id_to_uri(artwork_id)
        
        query = f"""
        PREFIX arp: <{ARP_NS}>
        PREFIX prov: <{PROV_NS}>
        
        SELECT ?event ?eventType ?date ?owner ?location ?description ?sourceUri ?order
        WHERE {{
            <{artwork_uri}> arp:hasProvenance ?event .
            ?event a arp:ProvenanceEvent .
            ?event arp:eventType ?eventType .
            ?event prov:atTime ?date .
            OPTIONAL {{ ?event arp:owner ?owner }}
            OPTIONAL {{ ?event arp:location ?location }}
            OPTIONAL {{ ?event arp:description ?description }}
            OPTIONAL {{ ?event arp:sourceUri ?sourceUri }}
            OPTIONAL {{ ?event arp:order ?order }}
        }}
        ORDER BY ?order ?date
        """
        
        result = sparql_service.execute_query(query)
        
        events = []
        for binding in result["results"]["bindings"]:
            event = ProvenanceRecord(
                id=self._uri_to_id(binding["event"]["value"]),
                event=binding["eventType"]["value"],
                date=binding["date"]["value"],
                owner=binding.get("owner", {}).get("value"),
                location=binding.get("location", {}).get("value"),
                description=binding.get("description", {}).get("value"),
                sourceUri=binding.get("sourceUri", {}).get("value"),
                order=int(binding["order"]["value"]) if "order" in binding else None
            )
            events.append(event)
        
        return events
    
    def update_artwork(self, artwork_id: str, data: 'ArtworkUpdate') -> Optional[ArtworkResponse]:
        """Update an existing artwork."""
        # First check if artwork exists
        existing = self.get_artwork(artwork_id)
        if not existing:
            return None
        
        uri = self._id_to_uri(artwork_id)
        
        # Build DELETE/INSERT for each provided field
        delete_triples = []
        insert_triples = []
        
        field_mappings = {
            'title': ('dc:title', data.title),
            'artist': ('dc:creator', data.artist),
            'dateCreated': ('dc:date', data.dateCreated),
            'medium': ('arp:medium', data.medium),
            'dimensions': ('arp:dimensions', data.dimensions),
            'description': ('dc:description', data.description),
            'imageUrl': ('arp:imageUrl', data.imageUrl),
            'currentLocation': ('arp:currentLocation', data.currentLocation),
            'period': ('arp:period', data.period),
            'style': ('arp:style', data.style),
        }
        
        for field, (predicate, value) in field_mappings.items():
            if value is not None:
                delete_triples.append(f'<{uri}> {predicate} ?old_{field}')
                insert_triples.append(f'<{uri}> {predicate} "{self._escape_literal(value)}"')
        
        if not insert_triples:
            # No fields to update
            return existing
        
        # Build the SPARQL UPDATE query
        delete_clause = " .\n        ".join(delete_triples)
        insert_clause = " .\n        ".join(insert_triples)
        optional_clauses = "\n        ".join([f'OPTIONAL {{ {t} }}' for t in delete_triples])
        
        update = f"""
        PREFIX dc: <{DC_NS}>
        PREFIX arp: <{ARP_NS}>
        
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
        
        # Return the updated artwork
        return self.get_artwork(artwork_id)
    
    def delete_artwork(self, artwork_id: str) -> bool:
        """Delete an artwork and its provenance."""
        uri = self._id_to_uri(artwork_id)
        
        # First check if artwork exists
        existing = self.get_artwork(artwork_id)
        if not existing:
            return False
        
        # Delete all triples related to this artwork (including provenance)
        update = f"""
        PREFIX arp: <{ARP_NS}>
        
        DELETE {{
            <{uri}> ?p ?o .
            ?prov ?pp ?po .
        }}
        WHERE {{
            <{uri}> ?p ?o .
            OPTIONAL {{
                <{uri}> arp:hasProvenance ?prov .
                ?prov ?pp ?po .
            }}
        }}
        """
        
        sparql_service.execute_update(update)
        return True
    
    def add_provenance_event(self, artwork_id: str, data: 'ProvenanceEventCreate') -> ProvenanceRecord:
        """Add a provenance event to an artwork."""
        from ..models.provenance import ProvenanceEventCreate
        
        artwork_uri = self._id_to_uri(artwork_id)
        event_id = f"provenance_{uuid.uuid4().hex[:12]}"
        event_uri = f"{ARP_DATA}{event_id}"
        
        # Get current max order
        order_query = f"""
        PREFIX arp: <{ARP_NS}>
        
        SELECT (MAX(?order) AS ?maxOrder) WHERE {{
            <{artwork_uri}> arp:hasProvenance ?event .
            OPTIONAL {{ ?event arp:order ?order }}
        }}
        """
        order_result = sparql_service.execute_query(order_query)
        max_order = 0
        if order_result["results"]["bindings"]:
            max_val = order_result["results"]["bindings"][0].get("maxOrder", {}).get("value")
            if max_val:
                max_order = int(max_val)
        new_order = max_order + 1
        
        # Build INSERT query
        triples = [
            f'<{artwork_uri}> arp:hasProvenance <{event_uri}>',
            f'<{event_uri}> a arp:ProvenanceEvent',
            f'<{event_uri}> arp:eventType "{self._escape_literal(data.event.value)}"',
            f'<{event_uri}> prov:atTime "{self._escape_literal(data.date)}"',
            f'<{event_uri}> arp:order {new_order}',
        ]
        
        if data.owner:
            triples.append(f'<{event_uri}> arp:owner "{self._escape_literal(data.owner)}"')
        if data.location:
            triples.append(f'<{event_uri}> arp:location "{self._escape_literal(data.location)}"')
        if data.description:
            triples.append(f'<{event_uri}> arp:description "{self._escape_literal(data.description)}"')
        if data.sourceUri:
            triples.append(f'<{event_uri}> arp:sourceUri "{self._escape_literal(data.sourceUri)}"')
        
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
            order=new_order
        )
    
    def update_provenance_event(self, artwork_id: str, event_id: str, data: 'ProvenanceEventUpdate') -> Optional[ProvenanceRecord]:
        """Update a provenance event."""
        from ..models.provenance import ProvenanceEventUpdate
        
        event_uri = self._id_to_uri(event_id)
        
        # Check if event exists
        check_query = f"""
        PREFIX arp: <{ARP_NS}>
        
        ASK {{ <{event_uri}> a arp:ProvenanceEvent }}
        """
        # For ASK queries, we need to handle differently
        try:
            result = sparql_service.execute_query(check_query)
            if not result.get("boolean", False):
                return None
        except:
            return None
        
        # Build DELETE/INSERT for provided fields
        delete_triples = []
        insert_triples = []
        
        if data.event is not None:
            delete_triples.append(f'<{event_uri}> arp:eventType ?oldEventType')
            insert_triples.append(f'<{event_uri}> arp:eventType "{self._escape_literal(data.event.value)}"')
        if data.date is not None:
            delete_triples.append(f'<{event_uri}> prov:atTime ?oldDate')
            insert_triples.append(f'<{event_uri}> prov:atTime "{self._escape_literal(data.date)}"')
        if data.owner is not None:
            delete_triples.append(f'<{event_uri}> arp:owner ?oldOwner')
            insert_triples.append(f'<{event_uri}> arp:owner "{self._escape_literal(data.owner)}"')
        if data.location is not None:
            delete_triples.append(f'<{event_uri}> arp:location ?oldLocation')
            insert_triples.append(f'<{event_uri}> arp:location "{self._escape_literal(data.location)}"')
        if data.description is not None:
            delete_triples.append(f'<{event_uri}> arp:description ?oldDescription')
            insert_triples.append(f'<{event_uri}> arp:description "{self._escape_literal(data.description)}"')
        if data.sourceUri is not None:
            delete_triples.append(f'<{event_uri}> arp:sourceUri ?oldSourceUri')
            insert_triples.append(f'<{event_uri}> arp:sourceUri "{self._escape_literal(data.sourceUri)}"')
        
        if not insert_triples:
            # Fetch and return current event
            events = self.get_provenance(artwork_id)
            return next((e for e in events if e.id == event_id), None)
        
        delete_clause = " .\n        ".join(delete_triples)
        insert_clause = " .\n        ".join(insert_triples)
        optional_clauses = "\n        ".join([f'OPTIONAL {{ {t} }}' for t in delete_triples])
        
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
        
        # Return updated event
        events = self.get_provenance(artwork_id)
        return next((e for e in events if e.id == event_id), None)
    
    def delete_provenance_event(self, artwork_id: str, event_id: str) -> bool:
        """Delete a provenance event."""
        artwork_uri = self._id_to_uri(artwork_id)
        event_uri = self._id_to_uri(event_id)
        
        # Delete all triples related to this event
        update = f"""
        PREFIX arp: <{ARP_NS}>
        
        DELETE {{
            <{artwork_uri}> arp:hasProvenance <{event_uri}> .
            <{event_uri}> ?p ?o .
        }}
        WHERE {{
            <{artwork_uri}> arp:hasProvenance <{event_uri}> .
            <{event_uri}> ?p ?o .
        }}
        """
        
        sparql_service.execute_update(update)
        return True
    
    def search_artworks(
        self,
        q: str,
        fields: Optional[List[str]] = None,
        page: int = 1,
        limit: int = 20
    ) -> Dict[str, Any]:
        """Full-text search across artworks."""
        offset = (page - 1) * limit
        
        # Default search fields
        if not fields:
            fields = ['title', 'artist', 'description']
        
        # Build filter for each field
        field_mappings = {
            'title': '?title',
            'artist': '?artist',
            'description': '?description',
        }
        
        search_filters = []
        for field in fields:
            if field in field_mappings:
                var = field_mappings[field]
                search_filters.append(f'CONTAINS(LCASE({var}), LCASE("{self._escape_literal(q)}"))')
        
        if not search_filters:
            search_filters = [f'CONTAINS(LCASE(?title), LCASE("{self._escape_literal(q)}"))']
        
        filter_expression = " || ".join(search_filters)
        
        # Count query
        count_query = f"""
        PREFIX dc: <{DC_NS}>
        PREFIX arp: <{ARP_NS}>
        
        SELECT (COUNT(DISTINCT ?artwork) AS ?total) WHERE {{
            ?artwork a arp:Artwork .
            ?artwork dc:title ?title .
            OPTIONAL {{ ?artwork dc:creator ?artist }}
            OPTIONAL {{ ?artwork dc:description ?description }}
            FILTER({filter_expression})
        }}
        """
        
        count_result = sparql_service.execute_query(count_query)
        total = int(count_result["results"]["bindings"][0]["total"]["value"]) if count_result["results"]["bindings"] else 0
        
        # Main search query
        query = f"""
        PREFIX dc: <{DC_NS}>
        PREFIX arp: <{ARP_NS}>
        
        SELECT DISTINCT ?artwork ?title ?artist ?dateCreated ?medium ?dimensions 
               ?description ?imageUrl ?currentLocation ?period ?style
        WHERE {{
            ?artwork a arp:Artwork .
            ?artwork dc:title ?title .
            OPTIONAL {{ ?artwork dc:creator ?artist }}
            OPTIONAL {{ ?artwork dc:date ?dateCreated }}
            OPTIONAL {{ ?artwork arp:medium ?medium }}
            OPTIONAL {{ ?artwork arp:dimensions ?dimensions }}
            OPTIONAL {{ ?artwork dc:description ?description }}
            OPTIONAL {{ ?artwork arp:imageUrl ?imageUrl }}
            OPTIONAL {{ ?artwork arp:currentLocation ?currentLocation }}
            OPTIONAL {{ ?artwork arp:period ?period }}
            OPTIONAL {{ ?artwork arp:style ?style }}
            FILTER({filter_expression})
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
        
        return {
            "query": q,
            "total": total,
            "page": page,
            "limit": limit,
            "results": items
        }


artwork_service = ArtworkService()

