#!/usr/bin/env python3
"""
Romanian Heritage XML to TTL Converter

Parses LIDO XML files containing Romanian cultural heritage data,
enriches with Wikidata/DBpedia, and generates RDF/TTL output
conforming to the ArP ontology.

Usage:
    python romanian_heritage_parser.py --count 10
    python romanian_heritage_parser.py --all
    python romanian_heritage_parser.py --count 50 --output-dir ./output
"""

import argparse
import re
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from lxml import etree
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DC, DCTERMS, OWL, RDF, RDFS, XSD
from SPARQLWrapper import JSON, SPARQLWrapper

# =============================================================================
# NAMESPACE DEFINITIONS
# =============================================================================

# LIDO namespace for XML parsing
LIDO_NS = "http://www.lido-schema.org"
LIDO = "{" + LIDO_NS + "}"

# RDF namespaces for TTL output
ARP = Namespace("http://example.org/arp#")
SCHEMA = Namespace("http://schema.org/")
PROV = Namespace("http://www.w3.org/ns/prov#")
CRM = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
AAT = Namespace("http://vocab.getty.edu/aat/")
DBR = Namespace("http://dbpedia.org/resource/")
WD = Namespace("http://www.wikidata.org/entity/")


# =============================================================================
# SPARQL ENDPOINTS
# =============================================================================

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
DBPEDIA_ENDPOINT = "https://dbpedia.org/sparql"
GETTY_ENDPOINT = "https://vocab.getty.edu/sparql"


# =============================================================================
# GETTY AAT VOCABULARY MAPPINGS
# =============================================================================

# Map Romanian artwork types to Getty AAT concept URIs
# Reference: https://vocab.getty.edu/aat/
GETTY_AAT_MAPPINGS = {
    # Artwork types
    "pictură": "http://vocab.getty.edu/aat/300033618",  # paintings (visual works)
    "painting": "http://vocab.getty.edu/aat/300033618",
    "pictură de șevalet": "http://vocab.getty.edu/aat/300033618",
    "acuarelă": "http://vocab.getty.edu/aat/300078925",  # watercolors (paintings)
    "watercolor": "http://vocab.getty.edu/aat/300078925",
    "desen": "http://vocab.getty.edu/aat/300033973",  # drawings (visual works)
    "drawing": "http://vocab.getty.edu/aat/300033973",
    "sculptură": "http://vocab.getty.edu/aat/300047090",  # sculpture (visual works)
    "sculpture": "http://vocab.getty.edu/aat/300047090",
    "gravură": "http://vocab.getty.edu/aat/300041340",  # prints (visual works)
    "print": "http://vocab.getty.edu/aat/300041340",
    "icoană": "http://vocab.getty.edu/aat/300074603",  # icons (religious images)
    "icon": "http://vocab.getty.edu/aat/300074603",
    "mozaic": "http://vocab.getty.edu/aat/300015342",  # mosaics
    "mosaic": "http://vocab.getty.edu/aat/300015342",
    "frescă": "http://vocab.getty.edu/aat/300177433",  # frescoes
    "fresco": "http://vocab.getty.edu/aat/300177433",
    "portret": "http://vocab.getty.edu/aat/300015637",  # portraits
    "portrait": "http://vocab.getty.edu/aat/300015637",
    "peisaj": "http://vocab.getty.edu/aat/300015636",  # landscapes (representations)
    "landscape": "http://vocab.getty.edu/aat/300015636",
    "natură moartă": "http://vocab.getty.edu/aat/300015638",  # still lifes
    "still life": "http://vocab.getty.edu/aat/300015638",
    # Materials
    "ulei": "http://vocab.getty.edu/aat/300015050",  # oil paint
    "oil": "http://vocab.getty.edu/aat/300015050",
    "ulei pe pânză": "http://vocab.getty.edu/aat/300015050",
    "tempera": "http://vocab.getty.edu/aat/300015062",  # tempera
    "bronz": "http://vocab.getty.edu/aat/300010957",  # bronze
    "bronze": "http://vocab.getty.edu/aat/300010957",
    "marmură": "http://vocab.getty.edu/aat/300011443",  # marble
    "marble": "http://vocab.getty.edu/aat/300011443",
    "lemn": "http://vocab.getty.edu/aat/300011914",  # wood
    "wood": "http://vocab.getty.edu/aat/300011914",
    "hârtie": "http://vocab.getty.edu/aat/300014109",  # paper
    "paper": "http://vocab.getty.edu/aat/300014109",
    "pânză": "http://vocab.getty.edu/aat/300014078",  # canvas
    "canvas": "http://vocab.getty.edu/aat/300014078",
    "carton": "http://vocab.getty.edu/aat/300014224",  # cardboard
    "cardboard": "http://vocab.getty.edu/aat/300014224",
    # Techniques
    "pictare": "http://vocab.getty.edu/aat/300054216",  # painting (image-making)
    "desenare": "http://vocab.getty.edu/aat/300054196",  # drawing (image-making)
    "turnare": "http://vocab.getty.edu/aat/300053104",  # casting
    "cizelure": "http://vocab.getty.edu/aat/300053149",  # chasing
    # Art periods/movements
    "impresionism": "http://vocab.getty.edu/aat/300021503",  # Impressionism
    "post-impresionism": "http://vocab.getty.edu/aat/300021508",  # Post-Impressionism
    "romantism": "http://vocab.getty.edu/aat/300172863",  # Romanticism
    "realism": "http://vocab.getty.edu/aat/300172861",  # Realism
    "expresionism": "http://vocab.getty.edu/aat/300021505",  # Expressionism
    "baroc": "http://vocab.getty.edu/aat/300021147",  # Baroque
    "renascentist": "http://vocab.getty.edu/aat/300021140",  # Renaissance
}


# =============================================================================
# ARTIST ENRICHMENT CACHE
# =============================================================================


class ArtistCache:
    """Cache for artist enrichment data to avoid duplicate SPARQL queries."""

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}
        self._query_delay = 1.0  # Delay between SPARQL queries (rate limiting)

    def get(self, artist_name: str) -> Optional[Dict[str, Any]]:
        """Get cached artist data."""
        return self._cache.get(self._normalize_name(artist_name))

    def set(self, artist_name: str, data: Dict[str, Any]) -> None:
        """Cache artist data."""
        self._cache[self._normalize_name(artist_name)] = data

    def has(self, artist_name: str) -> bool:
        """Check if artist is cached."""
        return self._normalize_name(artist_name) in self._cache

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize artist name for cache key."""
        return name.lower().strip()


# =============================================================================
# LIDO XML PARSER
# =============================================================================


class LIDOParser:
    """Parser for LIDO XML format artwork records."""

    def __init__(self, xml_path: Path):
        self.xml_path = xml_path
        self.ns = {"lido": LIDO_NS}

    def parse_artworks(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """
        Parse artwork records from LIDO XML file.

        Args:
            limit: Maximum number of artworks to parse (None for all)

        Returns:
            List of artwork dictionaries
        """
        artworks = []
        count = 0

        # Use iterparse for memory efficiency with large files
        context = etree.iterparse(
            str(self.xml_path), events=("end",), tag=f"{LIDO}lido"
        )

        for event, elem in context:
            artwork = self._parse_artwork_element(elem)
            if artwork:
                artworks.append(artwork)
                count += 1

                if limit and count >= limit:
                    break

            # Clear element to free memory
            elem.clear()
            while elem.getprevious() is not None:
                del elem.getparent()[0]

        return artworks

    def _parse_artwork_element(self, elem: etree._Element) -> Optional[Dict[str, Any]]:
        """Parse a single lido:lido element into an artwork dictionary."""
        try:
            artwork = {
                "id": self._get_text(elem, ".//lido:lidoRecID"),
                "title": self._get_title(elem),
                "title_lang": "ro",
                "object_type": self._get_object_type(elem),
                "classification": self._get_classification(elem),
                "description": self._get_description(elem),
                "dimensions": self._get_dimensions(elem),
                "materials_technique": self._get_materials_technique(elem),
                "creator": self._get_creator(elem),
                "creation_date": self._get_creation_date(elem),
                "creation_place": self._get_creation_place(elem),
                "repository": self._get_repository(elem),
                "inventory_number": self._get_inventory_number(elem),
                "condition": self._get_condition(elem),
                "image_url": self._get_image_url(elem),
                "record_url": self._get_record_url(elem),
            }

            # Skip records without essential data
            if not artwork["id"] or not artwork["title"]:
                return None

            return artwork

        except Exception as e:
            print(f"Warning: Error parsing artwork element: {e}", file=sys.stderr)
            return None

    def _get_text(self, elem: etree._Element, xpath: str) -> Optional[str]:
        """Get text content from xpath result."""
        result = elem.xpath(xpath, namespaces=self.ns)
        if result:
            text = result[0].text if hasattr(result[0], "text") else str(result[0])
            return text.strip() if text else None
        return None

    def _get_title(self, elem: etree._Element) -> Optional[str]:
        """Extract artwork title."""
        # Try preferred title first
        title = self._get_text(
            elem,
            ".//lido:titleWrap/lido:titleSet/lido:appellationValue[@lido:pref='preferred']",
        )
        if not title:
            # Fall back to any title
            title = self._get_text(
                elem, ".//lido:titleWrap/lido:titleSet/lido:appellationValue"
            )
        return title

    def _get_object_type(self, elem: etree._Element) -> Optional[str]:
        """Extract object type (Pictură, Acuarelă, etc.)."""
        return self._get_text(
            elem,
            ".//lido:objectWorkTypeWrap/lido:objectWorkType/lido:term[@xml:lang='ro']",
        ) or self._get_text(
            elem, ".//lido:objectWorkTypeWrap/lido:objectWorkType/lido:term"
        )

    def _get_classification(self, elem: etree._Element) -> List[str]:
        """Extract classification terms."""
        classifications = []
        for term in elem.xpath(
            ".//lido:classificationWrap/lido:classification/lido:term[@xml:lang='en']",
            namespaces=self.ns,
        ):
            if term.text:
                classifications.append(term.text.strip())
        return classifications

    def _get_description(self, elem: etree._Element) -> Optional[str]:
        """Extract artwork description."""
        return self._get_text(
            elem,
            ".//lido:objectDescriptionWrap/lido:objectDescriptionSet/lido:descriptiveNoteValue",
        )

    def _get_dimensions(self, elem: etree._Element) -> Optional[str]:
        """Extract artwork dimensions."""
        dimensions = []
        for dim in elem.xpath(
            ".//lido:objectMeasurementsWrap/lido:objectMeasurementsSet/lido:displayObjectMeasurements",
            namespaces=self.ns,
        ):
            if dim.text:
                label = dim.get(f"{LIDO}label", "")
                text = dim.text.strip()
                if label == "dimensions":
                    return text
                dimensions.append(text)

        return "; ".join(dimensions) if dimensions else None

    def _get_materials_technique(
        self, elem: etree._Element
    ) -> Dict[str, Optional[str]]:
        """Extract materials and technique."""
        result = {"material": None, "technique": None}

        for mat in elem.xpath(
            ".//lido:eventMaterialsTech/lido:displayMaterialsTech", namespaces=self.ns
        ):
            label = mat.get(f"{LIDO}label", "")
            if mat.text:
                if label == "material":
                    result["material"] = mat.text.strip()
                elif label == "technique":
                    result["technique"] = mat.text.strip()

        return result

    def _get_creator(self, elem: etree._Element) -> Optional[str]:
        """Extract creator/artist name."""
        return self._get_text(
            elem,
            ".//lido:eventActor/lido:actorInRole/lido:actor/lido:nameActorSet/lido:appellationValue",
        )

    def _get_creation_date(self, elem: etree._Element) -> Optional[str]:
        """Extract creation date."""
        return self._get_text(elem, ".//lido:eventDate/lido:displayDate")

    def _get_creation_place(self, elem: etree._Element) -> Optional[str]:
        """Extract creation place."""
        return self._get_text(
            elem,
            ".//lido:eventPlace/lido:place/lido:namePlaceSet/lido:appellationValue",
        )

    def _get_repository(self, elem: etree._Element) -> Optional[str]:
        """Extract repository/museum name."""
        return self._get_text(
            elem,
            ".//lido:repositoryWrap/lido:repositorySet/lido:repositoryName/lido:legalBodyName/lido:appellationValue",
        )

    def _get_inventory_number(self, elem: etree._Element) -> Optional[str]:
        """Extract inventory number."""
        return self._get_text(
            elem,
            ".//lido:repositoryWrap/lido:repositorySet/lido:workID[@lido:type='inventory number']",
        )

    def _get_condition(self, elem: etree._Element) -> Optional[str]:
        """Extract condition/state."""
        return self._get_text(elem, ".//lido:displayStateEditionWrap/lido:displayState")

    def _get_image_url(self, elem: etree._Element) -> Optional[str]:
        """Extract image URL."""
        return self._get_text(
            elem,
            ".//lido:resourceWrap/lido:resourceSet/lido:resourceRepresentation/lido:linkResource",
        )

    def _get_record_url(self, elem: etree._Element) -> Optional[str]:
        """Extract record info URL."""
        return self._get_text(elem, ".//lido:recordInfoSet/lido:recordInfoLink")


# =============================================================================
# WIKIDATA/DBPEDIA/GETTY ENRICHER
# =============================================================================


class DataEnricher:
    """Enriches data using Wikidata, DBpedia, and Getty SPARQL endpoints."""

    def __init__(self, cache: ArtistCache):
        self.cache = cache
        self._artwork_cache: Dict[str, Dict[str, Any]] = {}
        self._query_delay = 1.0  # Rate limiting

    def enrich_artist(self, artist_name: str) -> Dict[str, Any]:
        """
        Enrich artist information from BOTH Wikidata AND DBpedia.

        Args:
            artist_name: Artist name (may be in "Surname, FirstName" format)

        Returns:
            Dictionary with enriched artist data including links to both sources
        """
        if not artist_name:
            return {}

        # Skip generic names
        if artist_name.lower() in ["anonim", "necunoscut", "unknown", "anonymous"]:
            return {}

        # Check cache first
        if self.cache.has(artist_name):
            return self.cache.get(artist_name)

        # Normalize name format
        normalized_name = self._normalize_artist_name(artist_name)

        # Query Wikidata
        result = self._query_wikidata_artist(normalized_name)

        # ALSO query DBpedia (not just fallback) to get both links
        dbpedia_result = self._query_dbpedia_artist(normalized_name)

        # Merge results - prefer Wikidata data but add DBpedia URI
        if dbpedia_result.get("dbpedia_uri"):
            result["dbpedia_uri"] = dbpedia_result["dbpedia_uri"]
            # Fill in missing data from DBpedia
            if not result.get("birth_date") and dbpedia_result.get("birth_date"):
                result["birth_date"] = dbpedia_result["birth_date"]
            if not result.get("death_date") and dbpedia_result.get("death_date"):
                result["death_date"] = dbpedia_result["death_date"]
            if not result.get("nationality") and dbpedia_result.get("nationality"):
                result["nationality"] = dbpedia_result["nationality"]

        # Cache the result
        self.cache.set(artist_name, result)

        return result

    def enrich_artwork(
        self, title: str, artist_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Try to find artwork in Wikidata to get external links.

        Args:
            title: Artwork title
            artist_name: Optional artist name for better matching

        Returns:
            Dictionary with artwork Wikidata/DBpedia URIs if found
        """
        cache_key = f"{title}|{artist_name or ''}"
        if cache_key in self._artwork_cache:
            return self._artwork_cache[cache_key]

        result = {"wikidata_uri": None, "dbpedia_uri": None}

        # Try Wikidata search for artwork
        normalized_artist = (
            self._normalize_artist_name(artist_name) if artist_name else None
        )
        wikidata_result = self._query_wikidata_artwork(title, normalized_artist)
        result.update(wikidata_result)

        self._artwork_cache[cache_key] = result
        return result

    def get_getty_aat_uris(self, artwork: Dict[str, Any]) -> List[str]:
        """
        Get Getty AAT URIs for an artwork based on its type and materials.

        Args:
            artwork: Parsed artwork data

        Returns:
            List of Getty AAT URIs applicable to this artwork
        """
        aat_uris = []

        # Check object type
        if artwork.get("object_type"):
            obj_type = artwork["object_type"].lower()
            for key, uri in GETTY_AAT_MAPPINGS.items():
                if key in obj_type:
                    aat_uris.append(uri)
                    break

        # Check materials/technique
        materials = artwork.get("materials_technique", {})
        material_text = materials.get("material", "") or ""
        technique_text = materials.get("technique", "") or ""
        combined = f"{material_text} {technique_text}".lower()

        for key, uri in GETTY_AAT_MAPPINGS.items():
            if key in combined and uri not in aat_uris:
                aat_uris.append(uri)

        return aat_uris

    @staticmethod
    def _normalize_artist_name(name: str) -> str:
        """Convert 'Surname, FirstName' to 'FirstName Surname' format."""
        if "," in name:
            parts = name.split(",", 1)
            if len(parts) == 2:
                return f"{parts[1].strip()} {parts[0].strip()}"
        return name.strip()

    def _query_wikidata_artist(self, artist_name: str) -> Dict[str, Any]:
        """Query Wikidata for artist information."""
        result = {
            "wikidata_uri": None,
            "birth_date": None,
            "death_date": None,
            "nationality": None,
            "description": None,
        }

        # Escape quotes in artist name
        safe_name = artist_name.replace('"', '\\"')

        # SPARQL query for Wikidata - search for artists/painters
        query = f"""
        SELECT ?artist ?artistLabel ?birthDate ?deathDate ?nationalityLabel ?description WHERE {{
          ?artist wdt:P31 wd:Q5 .  # instance of human
          ?artist rdfs:label "{safe_name}"@en .
          
          # Prefer artists/painters
          OPTIONAL {{ ?artist wdt:P106 ?occupation . }}
          
          OPTIONAL {{ ?artist wdt:P569 ?birthDate . }}
          OPTIONAL {{ ?artist wdt:P570 ?deathDate . }}
          OPTIONAL {{ ?artist wdt:P27 ?nationality . }}
          OPTIONAL {{ ?artist schema:description ?description . FILTER(LANG(?description) = "en") }}
          
          SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,ro". }}
        }}
        LIMIT 1
        """

        try:
            sparql = SPARQLWrapper(WIKIDATA_ENDPOINT)
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            sparql.addCustomHttpHeader(
                "User-Agent", "RomanianHeritageParser/1.0 (mailto:contact@example.org)"
            )

            time.sleep(self._query_delay)  # Rate limiting

            results = sparql.query().convert()
            bindings = results.get("results", {}).get("bindings", [])

            if bindings:
                binding = bindings[0]
                result["wikidata_uri"] = binding.get("artist", {}).get("value")
                result["birth_date"] = self._extract_date(
                    binding.get("birthDate", {}).get("value")
                )
                result["death_date"] = self._extract_date(
                    binding.get("deathDate", {}).get("value")
                )
                result["nationality"] = binding.get("nationalityLabel", {}).get("value")
                result["description"] = binding.get("description", {}).get("value")

        except Exception as e:
            print(
                f"Warning: Wikidata artist query failed for '{artist_name}': {e}",
                file=sys.stderr,
            )

        return result

    def _query_wikidata_artwork(
        self, title: str, artist_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Query Wikidata for artwork information."""
        result = {"wikidata_uri": None}

        # Escape quotes
        safe_title = title.replace('"', '\\"')

        # Build query - artwork must be visual artwork or painting
        query = f"""
        SELECT ?artwork WHERE {{
          ?artwork wdt:P31/wdt:P279* wd:Q838948 .  # instance of artwork or subclass
          ?artwork rdfs:label ?label .
          FILTER(CONTAINS(LCASE(?label), LCASE("{safe_title}")))
          FILTER(LANG(?label) = "en" || LANG(?label) = "ro")
        }}
        LIMIT 1
        """

        try:
            sparql = SPARQLWrapper(WIKIDATA_ENDPOINT)
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            sparql.addCustomHttpHeader(
                "User-Agent", "RomanianHeritageParser/1.0 (mailto:contact@example.org)"
            )

            time.sleep(self._query_delay)

            results = sparql.query().convert()
            bindings = results.get("results", {}).get("bindings", [])

            if bindings:
                result["wikidata_uri"] = bindings[0].get("artwork", {}).get("value")

        except Exception as e:
            # Artwork queries may often fail - don't spam warnings
            pass

        return result

    def _query_dbpedia_artist(self, artist_name: str) -> Dict[str, Any]:
        """Query DBpedia for artist information."""
        result = {
            "dbpedia_uri": None,
            "birth_date": None,
            "death_date": None,
            "nationality": None,
        }

        # Sanitize artist name for DBpedia URI
        # Remove parenthetical annotations like "(maniera)" and special characters
        sanitized_name = re.sub(r"\s*\([^)]*\)\s*", " ", artist_name)  # Remove (...)
        sanitized_name = re.sub(r"[^\w\s-]", "", sanitized_name)  # Remove special chars
        sanitized_name = re.sub(r"\s+", " ", sanitized_name).strip()  # Normalize spaces

        if not sanitized_name:
            return result

        # Create DBpedia resource URI from name
        dbpedia_name = sanitized_name.replace(" ", "_")

        query = f"""
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX dbr: <http://dbpedia.org/resource/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT ?artist ?birthDate ?deathDate ?nationality WHERE {{
          VALUES ?artist {{ dbr:{dbpedia_name} }}
          
          OPTIONAL {{ ?artist dbo:birthDate ?birthDate . }}
          OPTIONAL {{ ?artist dbo:deathDate ?deathDate . }}
          OPTIONAL {{ ?artist dbo:nationality ?nationality . }}
        }}
        LIMIT 1
        """

        try:
            sparql = SPARQLWrapper(DBPEDIA_ENDPOINT)
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            sparql.addCustomHttpHeader("User-Agent", "RomanianHeritageParser/1.0")

            time.sleep(self._query_delay)  # Rate limiting

            results = sparql.query().convert()
            bindings = results.get("results", {}).get("bindings", [])

            if bindings:
                binding = bindings[0]
                result["dbpedia_uri"] = binding.get("artist", {}).get("value")
                if not result.get("birth_date"):
                    result["birth_date"] = self._extract_date(
                        binding.get("birthDate", {}).get("value")
                    )
                if not result.get("death_date"):
                    result["death_date"] = self._extract_date(
                        binding.get("deathDate", {}).get("value")
                    )
                if not result.get("nationality"):
                    nat = binding.get("nationality", {}).get("value")
                    if nat:
                        result["nationality"] = nat.split("/")[-1].replace("_", " ")

        except Exception as e:
            print(
                f"Warning: DBpedia query failed for '{artist_name}': {e}",
                file=sys.stderr,
            )

        return result

    @staticmethod
    def _extract_date(date_str: Optional[str]) -> Optional[str]:
        """Extract date from various formats."""
        if not date_str:
            return None

        # Handle ISO date format
        match = re.match(r"(\d{4})-(\d{2})-(\d{2})", date_str)
        if match:
            return date_str[:10]

        # Handle year only
        match = re.match(r"(\d{4})", date_str)
        if match:
            return match.group(1)

        return None


# =============================================================================
# RDF GRAPH GENERATOR
# =============================================================================


class RDFGenerator:
    """Generates RDF graph following the ArP ontology."""

    def __init__(self):
        self.graph = Graph()
        self._bind_namespaces()
        self._locations: Dict[str, URIRef] = {}
        self._owners: Dict[str, URIRef] = {}
        self._artists: Dict[str, URIRef] = {}

    def _bind_namespaces(self) -> None:
        """Bind namespace prefixes to the graph."""
        self.graph.bind("rdf", RDF)
        self.graph.bind("rdfs", RDFS)
        self.graph.bind("owl", OWL)
        self.graph.bind("xsd", XSD)
        self.graph.bind("dc", DC)
        self.graph.bind("dcterms", DCTERMS)
        self.graph.bind("prov", PROV)
        self.graph.bind("schema", SCHEMA)
        self.graph.bind("crm", CRM)
        self.graph.bind("aat", AAT)
        self.graph.bind("dbr", DBR)
        self.graph.bind("wd", WD)
        self.graph.bind("arp", ARP)

    def add_artwork(
        self,
        artwork: Dict[str, Any],
        artist_enrichment: Dict[str, Any],
        artwork_enrichment: Dict[str, Any],
        getty_aat_uris: List[str],
    ) -> URIRef:
        """
        Add an artwork to the RDF graph.

        Args:
            artwork: Parsed artwork data
            artist_enrichment: Enriched artist data from Wikidata/DBpedia
            artwork_enrichment: Enriched artwork data (Wikidata links)
            getty_aat_uris: List of Getty AAT concept URIs for this artwork

        Returns:
            URIRef of the artwork
        """
        # Generate artwork URI
        artwork_uri = self._create_artwork_uri(artwork["id"])

        # Type declarations
        self.graph.add((artwork_uri, RDF.type, ARP.Artwork))
        self.graph.add((artwork_uri, RDF.type, SCHEMA.VisualArtwork))

        # Add painting type based on object_type
        if artwork.get("object_type"):
            obj_type = artwork["object_type"].lower()
            if "pictură" in obj_type or "painting" in obj_type:
                self.graph.add((artwork_uri, RDF.type, SCHEMA.Painting))

        # Title
        if artwork.get("title"):
            self.graph.add(
                (
                    artwork_uri,
                    DC.title,
                    Literal(artwork["title"], lang=artwork.get("title_lang", "ro")),
                )
            )

        # Description
        if artwork.get("description"):
            self.graph.add(
                (
                    artwork_uri,
                    DC.description,
                    Literal(artwork["description"], lang="ro"),
                )
            )

        # Dimensions
        if artwork.get("dimensions"):
            self.graph.add(
                (artwork_uri, ARP.artworkDimensions, Literal(artwork["dimensions"]))
            )

        # Medium/Materials
        materials = artwork.get("materials_technique", {})
        medium_parts = []
        if materials.get("material"):
            medium_parts.append(materials["material"])
        if materials.get("technique"):
            medium_parts.append(materials["technique"])
        if medium_parts:
            self.graph.add(
                (artwork_uri, ARP.artworkMedium, Literal("; ".join(medium_parts)))
            )

        # Object type as period/style hint
        if artwork.get("object_type"):
            self.graph.add(
                (artwork_uri, ARP.artworkStyle, Literal(artwork["object_type"]))
            )

        # =================================================================
        # GETTY AAT VOCABULARY LINKS (critical requirement)
        # =================================================================
        for aat_uri in getty_aat_uris:
            # Link artwork to Getty AAT concepts via schema:artMedium and dcterms:type
            self.graph.add((artwork_uri, SCHEMA.artMedium, URIRef(aat_uri)))
            self.graph.add((artwork_uri, DCTERMS.type, URIRef(aat_uri)))

        # =================================================================
        # ARTWORK EXTERNAL LINKS (Wikidata/DBpedia)
        # =================================================================
        if artwork_enrichment.get("wikidata_uri"):
            self.graph.add(
                (artwork_uri, OWL.sameAs, URIRef(artwork_enrichment["wikidata_uri"]))
            )
        if artwork_enrichment.get("dbpedia_uri"):
            self.graph.add(
                (artwork_uri, OWL.sameAs, URIRef(artwork_enrichment["dbpedia_uri"]))
            )

        # Creation date
        if artwork.get("creation_date"):
            date_value = self._parse_creation_date(artwork["creation_date"])
            if date_value:
                self.graph.add((artwork_uri, DCTERMS.created, date_value))

        # Image URL
        if artwork.get("image_url"):
            self.graph.add((artwork_uri, SCHEMA.image, URIRef(artwork["image_url"])))

        # Link to original record
        if artwork.get("record_url"):
            self.graph.add((artwork_uri, RDFS.seeAlso, URIRef(artwork["record_url"])))

        # Creator/Artist
        if artwork.get("creator"):
            artist_uri = self._add_artist(artwork["creator"], artist_enrichment)
            self.graph.add((artwork_uri, DC.creator, artist_uri))

        # Repository/Location
        if artwork.get("repository"):
            location_uri = self._add_location(artwork["repository"])
            owner_uri = self._add_owner(artwork["repository"], location_uri)

            self.graph.add((artwork_uri, ARP.currentLocation, location_uri))
            self.graph.add((artwork_uri, ARP.currentOwner, owner_uri))

        # Build complete provenance chain
        self._add_provenance_chain(artwork, artwork_uri, artist_enrichment)

        return artwork_uri

    def _create_artwork_uri(self, artwork_id: str) -> URIRef:
        """Create a URI for an artwork."""
        safe_id = self._slugify(artwork_id)
        return ARP[f"artwork_{safe_id}"]

    def _add_artist(self, artist_name: str, enrichment: Dict[str, Any]) -> URIRef:
        """Add an artist to the graph, returning the URI."""
        cache_key = artist_name.lower().strip()

        if cache_key in self._artists:
            return self._artists[cache_key]

        # Create artist URI
        normalized_name = DataEnricher._normalize_artist_name(artist_name)
        artist_uri = ARP[f"artist_{self._slugify(normalized_name)}"]
        self._artists[cache_key] = artist_uri

        # Type
        self.graph.add((artist_uri, RDF.type, ARP.Artist))

        # Name
        self.graph.add((artist_uri, SCHEMA.name, Literal(normalized_name, lang="en")))

        # Enriched data
        if enrichment.get("birth_date"):
            self.graph.add(
                (
                    artist_uri,
                    SCHEMA.birthDate,
                    Literal(enrichment["birth_date"], datatype=XSD.date),
                )
            )

        if enrichment.get("death_date"):
            self.graph.add(
                (
                    artist_uri,
                    SCHEMA.deathDate,
                    Literal(enrichment["death_date"], datatype=XSD.date),
                )
            )

        if enrichment.get("nationality"):
            self.graph.add(
                (artist_uri, SCHEMA.nationality, Literal(enrichment["nationality"]))
            )

        if enrichment.get("description"):
            self.graph.add(
                (
                    artist_uri,
                    DC.description,
                    Literal(enrichment["description"], lang="en"),
                )
            )

        # owl:sameAs links
        if enrichment.get("wikidata_uri"):
            self.graph.add((artist_uri, OWL.sameAs, URIRef(enrichment["wikidata_uri"])))

        if enrichment.get("dbpedia_uri"):
            self.graph.add((artist_uri, OWL.sameAs, URIRef(enrichment["dbpedia_uri"])))

        return artist_uri

    def _add_location(self, repository_name: str) -> URIRef:
        """Add a location (museum) to the graph."""
        cache_key = repository_name.lower().strip()

        if cache_key in self._locations:
            return self._locations[cache_key]

        location_uri = ARP[f"location_{self._slugify(repository_name)}"]
        self._locations[cache_key] = location_uri

        self.graph.add((location_uri, RDF.type, ARP.Location))
        self.graph.add((location_uri, RDF.type, SCHEMA.Museum))
        self.graph.add((location_uri, SCHEMA.name, Literal(repository_name, lang="ro")))

        # Add Romania as country for Romanian heritage
        self.graph.add((location_uri, SCHEMA.address, Literal("Romania")))

        return location_uri

    def _add_owner(self, repository_name: str, location_uri: URIRef) -> URIRef:
        """Add an owner (organization) to the graph."""
        cache_key = repository_name.lower().strip()

        if cache_key in self._owners:
            return self._owners[cache_key]

        owner_uri = ARP[f"owner_{self._slugify(repository_name)}"]
        self._owners[cache_key] = owner_uri

        self.graph.add((owner_uri, RDF.type, ARP.OrganizationOwner))
        self.graph.add((owner_uri, SCHEMA.name, Literal(repository_name, lang="ro")))
        self.graph.add((owner_uri, ARP.ownerLocation, location_uri))

        return owner_uri

    def _add_provenance_chain(
        self,
        artwork: Dict[str, Any],
        artwork_uri: URIRef,
        artist_enrichment: Dict[str, Any],
    ) -> List[URIRef]:
        """
        Build a complete provenance chain for the artwork.

        Extracts provenance information from the description and creates:
        1. Creation event (artist creates the work)
        2. Intermediate events (extracted from description if available)
        3. Acquisition event (current museum acquires the work)

        Returns list of created event URIs.
        """
        events = []
        event_order = 1

        # =================================================================
        # EVENT 1: Creation
        # =================================================================
        creation_uri = ARP[f"prov_{artwork['id']}_creation"]
        self.graph.add((creation_uri, RDF.type, ARP.ProvenanceEvent))
        self.graph.add((creation_uri, ARP.eventType, Literal("Creation")))
        self.graph.add(
            (
                creation_uri,
                ARP.provenanceOrder,
                Literal(event_order, datatype=XSD.integer),
            )
        )
        self.graph.add((artwork_uri, ARP.hasProvenanceEvent, creation_uri))

        # Creation date
        if artwork.get("creation_date"):
            date_str = artwork["creation_date"]
            year_match = re.match(r"(\d{4})", date_str)
            if year_match:
                self.graph.add(
                    (
                        creation_uri,
                        PROV.startedAtTime,
                        Literal(f"{year_match.group(1)}-01-01", datatype=XSD.date),
                    )
                )

        # Creator as the first owner
        if artwork.get("creator"):
            normalized_name = DataEnricher._normalize_artist_name(artwork["creator"])
            artist_uri = ARP[f"artist_{self._slugify(normalized_name)}"]
            self.graph.add((creation_uri, ARP.toOwner, artist_uri))

        # Creation place
        if artwork.get("creation_place"):
            place_uri = ARP[f"place_{self._slugify(artwork['creation_place'])}"]
            if (place_uri, RDF.type, ARP.Location) not in self.graph:
                self.graph.add((place_uri, RDF.type, ARP.Location))
                self.graph.add(
                    (
                        place_uri,
                        SCHEMA.name,
                        Literal(artwork["creation_place"], lang="ro"),
                    )
                )
            self.graph.add((creation_uri, ARP.eventLocation, place_uri))

        events.append(creation_uri)
        event_order += 1

        # =================================================================
        # EVENT 2+: Extract provenance from description
        # =================================================================
        previous_owner = None
        if artwork.get("creator"):
            normalized_name = DataEnricher._normalize_artist_name(artwork["creator"])
            previous_owner = ARP[f"artist_{self._slugify(normalized_name)}"]

        if artwork.get("description"):
            desc = artwork["description"]
            extracted_events = self._extract_provenance_from_description(
                desc, artwork["id"], event_order, previous_owner
            )
            for event_uri, new_owner in extracted_events:
                self.graph.add((artwork_uri, ARP.hasProvenanceEvent, event_uri))
                events.append(event_uri)
                event_order += 1
                if new_owner:
                    previous_owner = new_owner

        # =================================================================
        # FINAL EVENT: Acquisition by current museum
        # =================================================================
        if artwork.get("repository"):
            acquisition_uri = ARP[f"prov_{artwork['id']}_acquisition"]
            self.graph.add((acquisition_uri, RDF.type, ARP.ProvenanceEvent))
            self.graph.add((acquisition_uri, ARP.eventType, Literal("Acquisition")))
            self.graph.add(
                (
                    acquisition_uri,
                    ARP.provenanceOrder,
                    Literal(event_order, datatype=XSD.integer),
                )
            )
            self.graph.add((artwork_uri, ARP.hasProvenanceEvent, acquisition_uri))

            # Previous owner (if known)
            if previous_owner:
                self.graph.add((acquisition_uri, ARP.fromOwner, previous_owner))

            # Current owner (museum)
            owner_uri = ARP[f"owner_{self._slugify(artwork['repository'])}"]
            self.graph.add((acquisition_uri, ARP.toOwner, owner_uri))

            # Location
            location_uri = ARP[f"location_{self._slugify(artwork['repository'])}"]
            self.graph.add((acquisition_uri, ARP.eventLocation, location_uri))

            self.graph.add(
                (
                    acquisition_uri,
                    DC.description,
                    Literal(f"Acquired by {artwork['repository']}", lang="en"),
                )
            )

            events.append(acquisition_uri)

        return events

    def _extract_provenance_from_description(
        self,
        description: str,
        artwork_id: str,
        start_order: int,
        previous_owner: Optional[URIRef],
    ) -> List[tuple]:
        """
        Extract provenance events from artwork description text.

        Common patterns in Romanian heritage descriptions:
        - "Provine din colecția regelui Carol I"
        - "Achiziționat de..."
        - "Donat de..."
        - "Din colecția..."

        Returns list of (event_uri, new_owner_uri) tuples.
        """
        events = []
        desc_lower = description.lower()

        # Pattern: "Provine din colecția regelui Carol I"
        if "colecția regelui carol i" in desc_lower:
            event_uri = ARP[f"prov_{artwork_id}_royal_collection"]
            self.graph.add((event_uri, RDF.type, ARP.ProvenanceEvent))
            self.graph.add((event_uri, ARP.eventType, Literal("Private Collection")))
            self.graph.add(
                (
                    event_uri,
                    ARP.provenanceOrder,
                    Literal(start_order, datatype=XSD.integer),
                )
            )
            self.graph.add(
                (
                    event_uri,
                    DC.description,
                    Literal("Parte din colecția regelui Carol I", lang="ro"),
                )
            )

            # Create Carol I owner if not exists
            carol_uri = ARP["owner_king_carol_i"]
            if (carol_uri, RDF.type, ARP.PersonOwner) not in self.graph:
                self.graph.add((carol_uri, RDF.type, ARP.PersonOwner))
                self.graph.add(
                    (
                        carol_uri,
                        SCHEMA.name,
                        Literal("King Carol I of Romania", lang="en"),
                    )
                )
                self.graph.add(
                    (carol_uri, SCHEMA.name, Literal("Regele Carol I", lang="ro"))
                )
                # Link to Wikidata
                self.graph.add((carol_uri, OWL.sameAs, WD["Q153475"]))
                self.graph.add((carol_uri, OWL.sameAs, DBR["Carol_I_of_Romania"]))

            if previous_owner:
                self.graph.add((event_uri, ARP.fromOwner, previous_owner))
            self.graph.add((event_uri, ARP.toOwner, carol_uri))

            events.append((event_uri, carol_uri))
            start_order += 1

        # Pattern: "colecția Zambaccian"
        elif "zambaccian" in desc_lower:
            event_uri = ARP[f"prov_{artwork_id}_zambaccian"]
            self.graph.add((event_uri, RDF.type, ARP.ProvenanceEvent))
            self.graph.add((event_uri, ARP.eventType, Literal("Private Collection")))
            self.graph.add(
                (
                    event_uri,
                    ARP.provenanceOrder,
                    Literal(start_order, datatype=XSD.integer),
                )
            )

            zambaccian_uri = ARP["owner_krikor_zambaccian"]
            if (zambaccian_uri, RDF.type, ARP.PersonOwner) not in self.graph:
                self.graph.add((zambaccian_uri, RDF.type, ARP.PersonOwner))
                self.graph.add(
                    (
                        zambaccian_uri,
                        SCHEMA.name,
                        Literal("Krikor Zambaccian", lang="en"),
                    )
                )
                self.graph.add((zambaccian_uri, OWL.sameAs, WD["Q6437186"]))

            if previous_owner:
                self.graph.add((event_uri, ARP.fromOwner, previous_owner))
            self.graph.add((event_uri, ARP.toOwner, zambaccian_uri))

            events.append((event_uri, zambaccian_uri))

        # Pattern: general donation
        elif "donat" in desc_lower or "donație" in desc_lower:
            event_uri = ARP[f"prov_{artwork_id}_donation"]
            self.graph.add((event_uri, RDF.type, ARP.ProvenanceEvent))
            self.graph.add((event_uri, ARP.eventType, Literal("Donation")))
            self.graph.add(
                (
                    event_uri,
                    ARP.provenanceOrder,
                    Literal(start_order, datatype=XSD.integer),
                )
            )
            self.graph.add(
                (event_uri, DC.description, Literal(description[:200], lang="ro"))
            )

            if previous_owner:
                self.graph.add((event_uri, ARP.fromOwner, previous_owner))

            events.append((event_uri, None))

        return events

    def _parse_creation_date(self, date_str: str) -> Optional[Literal]:
        """Parse creation date string into appropriate RDF literal."""
        if not date_str:
            return None

        # Handle date ranges like "1925-1926"
        range_match = re.match(r"(\d{4})\s*[-–]\s*(\d{4})", date_str)
        if range_match:
            return Literal(range_match.group(1), datatype=XSD.gYear)

        # Handle single year
        year_match = re.match(r"(\d{4})", date_str)
        if year_match:
            return Literal(year_match.group(1), datatype=XSD.gYear)

        # Handle century references
        century_match = re.search(r"sec(?:olul)?\.?\s*(\w+)", date_str, re.IGNORECASE)
        if century_match:
            return Literal(date_str)

        return Literal(date_str)

    @staticmethod
    def _slugify(text: str) -> str:
        """Convert text to URL-safe slug."""
        # Remove diacritics (Romanian specific)
        replacements = {
            "ă": "a",
            "â": "a",
            "î": "i",
            "ș": "s",
            "ț": "t",
            "Ă": "A",
            "Â": "A",
            "Î": "I",
            "Ș": "S",
            "Ț": "T",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)

        # Convert to lowercase and replace non-alphanumeric
        text = re.sub(r"[^a-zA-Z0-9]+", "_", text.lower())
        text = re.sub(r"_+", "_", text)  # Collapse multiple underscores
        text = text.strip("_")

        return text

    def serialize(self, format: str = "turtle") -> str:
        """Serialize the graph to string."""
        return self.graph.serialize(format=format)

    def save(self, path: Path, format: str = "turtle") -> None:
        """Save the graph to file."""
        self.graph.serialize(destination=str(path), format=format)


# =============================================================================
# MAIN CONVERTER CLASS
# =============================================================================


class RomanianHeritageConverter:
    """Main converter orchestrating the XML to TTL conversion process."""

    def __init__(
        self,
        input_path: Path,
        output_dir: Path,
        artwork_count: Optional[int] = None,
        enable_enrichment: bool = True,
    ):
        self.input_path = input_path
        self.output_dir = output_dir
        self.artwork_count = artwork_count
        self.enable_enrichment = enable_enrichment

        self.parser = LIDOParser(input_path)
        self.cache = ArtistCache()
        self.enricher = DataEnricher(self.cache) if enable_enrichment else None
        self.rdf_generator = RDFGenerator()

    def convert(self) -> Path:
        """
        Run the conversion process.

        Returns:
            Path to the generated TTL file
        """
        print(f"Parsing XML file: {self.input_path}")

        # Parse artworks
        artworks = self.parser.parse_artworks(limit=self.artwork_count)
        print(f"Parsed {len(artworks)} artworks")

        # Process each artwork
        for i, artwork in enumerate(artworks, 1):
            print(
                f"Processing artwork {i}/{len(artworks)}: {artwork.get('title', 'Unknown')[:50]}"
            )

            artist_enrichment = {}
            artwork_enrichment = {}
            getty_aat_uris = []

            if self.enable_enrichment:
                # Get Getty AAT URIs (always - works offline with mapping)
                getty_aat_uris = self.enricher.get_getty_aat_uris(artwork)
                if getty_aat_uris:
                    print(f"  Getty AAT: {len(getty_aat_uris)} concept(s) linked")

                # Enrich artist data from Wikidata AND DBpedia
                if artwork.get("creator"):
                    print(f"  Enriching artist: {artwork['creator']}")
                    artist_enrichment = self.enricher.enrich_artist(artwork["creator"])
                    if artist_enrichment.get("wikidata_uri"):
                        print(f"    Wikidata: {artist_enrichment['wikidata_uri']}")
                    if artist_enrichment.get("dbpedia_uri"):
                        print(f"    DBpedia: {artist_enrichment['dbpedia_uri']}")

                # Try to find artwork in Wikidata
                artwork_enrichment = self.enricher.enrich_artwork(
                    artwork.get("title", ""), artwork.get("creator")
                )
                if artwork_enrichment.get("wikidata_uri"):
                    print(f"  Artwork Wikidata: {artwork_enrichment['wikidata_uri']}")
            else:
                # Even without enrichment, we can still map to Getty AAT
                getty_aat_uris = self._get_getty_aat_offline(artwork)

            # Add to RDF graph with all enrichment data
            self.rdf_generator.add_artwork(
                artwork, artist_enrichment, artwork_enrichment, getty_aat_uris
            )

        # Generate output filename with timestamp
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_filename = f"romanian_data_{timestamp}.ttl"
        output_path = self.output_dir / output_filename

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Save TTL file
        print(f"Saving TTL file: {output_path}")
        self.rdf_generator.save(output_path)

        print(f"Conversion complete! Generated {len(artworks)} artwork records.")
        return output_path

    @staticmethod
    def _get_getty_aat_offline(artwork: Dict[str, Any]) -> List[str]:
        """Get Getty AAT URIs using local mapping (no network needed)."""
        aat_uris = []

        # Check object type
        if artwork.get("object_type"):
            obj_type = artwork["object_type"].lower()
            for key, uri in GETTY_AAT_MAPPINGS.items():
                if key in obj_type:
                    aat_uris.append(uri)
                    break

        # Check materials/technique
        materials = artwork.get("materials_technique", {})
        material_text = materials.get("material", "") or ""
        technique_text = materials.get("technique", "") or ""
        combined = f"{material_text} {technique_text}".lower()

        for key, uri in GETTY_AAT_MAPPINGS.items():
            if key in combined and uri not in aat_uris:
                aat_uris.append(uri)

        return aat_uris


# =============================================================================
# CLI ARGUMENT PARSING
# =============================================================================


def parse_arguments() -> argparse.Namespace:
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Convert Romanian heritage LIDO XML to ArP ontology TTL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --count 10                    # Convert first 10 artworks
  %(prog)s --all                         # Convert all artworks
  %(prog)s --count 50 --no-enrichment    # Convert 50 artworks without SPARQL enrichment
  %(prog)s --all --output-dir ./output   # Convert all and save to ./output directory
        """,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--count", "-c", type=int, metavar="N", help="Number of artworks to convert"
    )
    group.add_argument(
        "--all", "-a", action="store_true", help="Convert all artworks in the XML file"
    )

    parser.add_argument(
        "--input",
        "-i",
        type=Path,
        default=Path(__file__).parent.parent
        / "data"
        / "raw"
        / "inp-clasate-arp-2014-02-02.xml",
        help="Path to input LIDO XML file (default: data/raw/inp-clasate-arp-2014-02-02.xml)",
    )

    parser.add_argument(
        "--output-dir",
        "-o",
        type=Path,
        default=Path(__file__).parent.parent / "data" / "processed",
        help="Output directory for TTL file (default: data/processed/)",
    )

    parser.add_argument(
        "--no-enrichment",
        action="store_true",
        help="Disable Wikidata/DBpedia enrichment (faster, offline mode)",
    )

    return parser.parse_args()


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================


def main() -> int:
    """Main entry point."""
    args = parse_arguments()

    # Validate input file
    if not args.input.exists():
        print(f"Error: Input file not found: {args.input}", file=sys.stderr)
        return 1

    # Determine artwork count
    artwork_count = None if args.all else args.count

    try:
        converter = RomanianHeritageConverter(
            input_path=args.input,
            output_dir=args.output_dir,
            artwork_count=artwork_count,
            enable_enrichment=not args.no_enrichment,
        )

        output_path = converter.convert()
        print(f"\nOutput saved to: {output_path}")
        return 0

    except KeyboardInterrupt:
        print("\nConversion interrupted by user.")
        return 130
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
