"""External SPARQL service for DBpedia, Wikidata, and Getty AAT integration."""

import logging
import time
from typing import Any, Dict, List, Optional

from SPARQLWrapper import JSON, SPARQLWrapper

from ..config import settings

logger = logging.getLogger(__name__)


class SimpleCache:
    """Simple TTL-based in-memory cache for external query results."""

    def __init__(self, ttl: int = 3600):
        """Initialize cache with TTL in seconds."""
        self._cache: Dict[str, tuple] = {}  # key -> (value, expiry_time)
        self._ttl = ttl

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if not expired."""
        if key in self._cache:
            value, expiry = self._cache[key]
            if time.time() < expiry:
                logger.debug("Cache hit for key: %s...", key[:50])
                return value
            else:
                # Expired, remove from cache
                del self._cache[key]
                logger.debug("Cache expired for key: %s...", key[:50])
        return None

    def set(self, key: str, value: Any) -> None:
        """Set value in cache with TTL."""
        expiry = time.time() + self._ttl
        self._cache[key] = (value, expiry)
        logger.debug("Cache set for key: %s...", key[:50])

    def clear(self) -> None:
        """Clear all cached values."""
        self._cache.clear()

    def cleanup(self) -> int:
        """Remove expired entries and return count of removed items."""
        now = time.time()
        expired_keys = [k for k, (_, expiry) in self._cache.items() if now >= expiry]
        for key in expired_keys:
            del self._cache[key]
        return len(expired_keys)


class ExternalSPARQLService:
    """Service for querying external SPARQL endpoints (DBpedia, Wikidata, Getty)."""

    # RDF Namespace prefixes
    PREFIXES = {
        "dbo": "http://dbpedia.org/ontology/",
        "dbr": "http://dbpedia.org/resource/",
        "dbp": "http://dbpedia.org/property/",
        "wd": "http://www.wikidata.org/entity/",
        "wdt": "http://www.wikidata.org/prop/direct/",
        "wikibase": "http://wikiba.se/ontology#",
        "bd": "http://www.bigdata.com/rdf#",
        "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
        "skos": "http://www.w3.org/2004/02/skos/core#",
        "gvp": "http://vocab.getty.edu/ontology#",
        "schema": "http://schema.org/",
        "owl": "http://www.w3.org/2002/07/owl#",
    }

    def __init__(self):
        """Initialize external SPARQL service with endpoints and cache."""
        self.cache = SimpleCache(ttl=settings.external_cache_ttl)

        # External query timeout (shorter to prevent blocking the API)
        external_timeout = 10

        # Initialize DBpedia client
        self.dbpedia = SPARQLWrapper(settings.dbpedia_endpoint)
        self.dbpedia.setReturnFormat(JSON)
        self.dbpedia.setTimeout(external_timeout)
        self.dbpedia.addCustomHttpHeader("User-Agent", "ArP-Artwork-Provenance/1.0")

        # Initialize Wikidata client
        self.wikidata = SPARQLWrapper(settings.wikidata_endpoint)
        self.wikidata.setReturnFormat(JSON)
        self.wikidata.setTimeout(external_timeout)
        self.wikidata.addCustomHttpHeader("User-Agent", "ArP-Artwork-Provenance/1.0")

        # Initialize Getty client
        self.getty = SPARQLWrapper(settings.getty_endpoint)
        self.getty.setReturnFormat(JSON)
        self.getty.setTimeout(external_timeout)
        self.getty.addCustomHttpHeader("User-Agent", "ArP-Artwork-Provenance/1.0")

    def _execute_query(
        self, client: SPARQLWrapper, query: str, cache_key: str
    ) -> Optional[Dict]:
        """Execute a SPARQL query with caching and error handling."""
        # Check cache first
        cached = self.cache.get(cache_key)
        if cached is not None:
            return cached

        try:
            client.setQuery(query)
            results = client.query().convert()

            # Cache the results
            self.cache.set(cache_key, results)
            return results

        except Exception as e:
            logger.error("SPARQL query failed: %s", e)
            logger.debug("Query was: %s...", query[:200])
            return None

    def _extract_value(self, binding: Dict, key: str) -> Optional[str]:
        """Safely extract a value from a SPARQL binding."""
        if key in binding and "value" in binding[key]:
            return binding[key]["value"]
        return None

    # =========================================================================
    # DBpedia Methods
    # =========================================================================

    def get_dbpedia_artwork_info(self, dbpedia_uri: str) -> Dict[str, Any]:
        """
        Fetch artwork information from DBpedia.

        Args:
            dbpedia_uri: Full DBpedia URI (e.g., http://dbpedia.org/resource/Mona_Lisa)

        Returns:
            Dictionary with abstract, thumbnail, artist, and other metadata
        """
        cache_key = f"dbpedia:artwork:{dbpedia_uri}"

        query = f"""
        PREFIX dbo: <{self.PREFIXES['dbo']}>
        PREFIX dbp: <{self.PREFIXES['dbp']}>
        PREFIX rdfs: <{self.PREFIXES['rdfs']}>
        PREFIX owl: <{self.PREFIXES['owl']}>
        
        SELECT ?abstract ?thumbnail ?artist ?artistName ?museum ?museumName 
               ?year ?width ?height ?wikidata WHERE {{
            <{dbpedia_uri}> dbo:abstract ?abstract .
            FILTER(LANG(?abstract) = "en")
            
            OPTIONAL {{ <{dbpedia_uri}> dbo:thumbnail ?thumbnail }}
            OPTIONAL {{ 
                <{dbpedia_uri}> dbo:author ?artist .
                ?artist rdfs:label ?artistName .
                FILTER(LANG(?artistName) = "en")
            }}
            OPTIONAL {{ 
                <{dbpedia_uri}> dbo:museum ?museum .
                ?museum rdfs:label ?museumName .
                FILTER(LANG(?museumName) = "en")
            }}
            OPTIONAL {{ <{dbpedia_uri}> dbp:year ?year }}
            OPTIONAL {{ <{dbpedia_uri}> dbp:widthMetric ?width }}
            OPTIONAL {{ <{dbpedia_uri}> dbp:heightMetric ?height }}
            OPTIONAL {{ <{dbpedia_uri}> owl:sameAs ?wikidata . FILTER(CONTAINS(STR(?wikidata), "wikidata")) }}
        }}
        LIMIT 1
        """

        results = self._execute_query(self.dbpedia, query, cache_key)

        if not results or not results.get("results", {}).get("bindings"):
            return {"error": "No data found", "source": "dbpedia", "uri": dbpedia_uri}

        binding = results["results"]["bindings"][0]

        return {
            "source": "dbpedia",
            "uri": dbpedia_uri,
            "abstract": self._extract_value(binding, "abstract"),
            "thumbnail": self._extract_value(binding, "thumbnail"),
            "artist": (
                {
                    "uri": self._extract_value(binding, "artist"),
                    "name": self._extract_value(binding, "artistName"),
                }
                if self._extract_value(binding, "artist")
                else None
            ),
            "museum": (
                {
                    "uri": self._extract_value(binding, "museum"),
                    "name": self._extract_value(binding, "museumName"),
                }
                if self._extract_value(binding, "museum")
                else None
            ),
            "year": self._extract_value(binding, "year"),
            "dimensions": (
                {
                    "width": self._extract_value(binding, "width"),
                    "height": self._extract_value(binding, "height"),
                }
                if self._extract_value(binding, "width")
                else None
            ),
            "wikidata_uri": self._extract_value(binding, "wikidata"),
        }

    def get_dbpedia_artist_info(self, dbpedia_uri: str) -> Dict[str, Any]:
        """
        Fetch artist biographical information from DBpedia.

        Args:
            dbpedia_uri: Full DBpedia URI (e.g., http://dbpedia.org/resource/Leonardo_da_Vinci)

        Returns:
            Dictionary with biography, birth/death dates, nationality, and notable works
        """
        cache_key = f"dbpedia:artist:{dbpedia_uri}"

        query = f"""
        PREFIX dbo: <{self.PREFIXES['dbo']}>
        PREFIX dbp: <{self.PREFIXES['dbp']}>
        PREFIX rdfs: <{self.PREFIXES['rdfs']}>
        PREFIX owl: <{self.PREFIXES['owl']}>
        
        SELECT ?abstract ?thumbnail ?birthDate ?deathDate ?birthPlace ?birthPlaceName
               ?nationality ?movement ?movementName ?wikidata WHERE {{
            <{dbpedia_uri}> dbo:abstract ?abstract .
            FILTER(LANG(?abstract) = "en")
            
            OPTIONAL {{ <{dbpedia_uri}> dbo:thumbnail ?thumbnail }}
            OPTIONAL {{ <{dbpedia_uri}> dbo:birthDate ?birthDate }}
            OPTIONAL {{ <{dbpedia_uri}> dbo:deathDate ?deathDate }}
            OPTIONAL {{ 
                <{dbpedia_uri}> dbo:birthPlace ?birthPlace .
                ?birthPlace rdfs:label ?birthPlaceName .
                FILTER(LANG(?birthPlaceName) = "en")
            }}
            OPTIONAL {{ <{dbpedia_uri}> dbo:nationality ?nationality }}
            OPTIONAL {{ 
                <{dbpedia_uri}> dbo:movement ?movement .
                ?movement rdfs:label ?movementName .
                FILTER(LANG(?movementName) = "en")
            }}
            OPTIONAL {{ <{dbpedia_uri}> owl:sameAs ?wikidata . FILTER(CONTAINS(STR(?wikidata), "wikidata")) }}
        }}
        LIMIT 1
        """

        results = self._execute_query(self.dbpedia, query, cache_key)

        if not results or not results.get("results", {}).get("bindings"):
            return {"error": "No data found", "source": "dbpedia", "uri": dbpedia_uri}

        binding = results["results"]["bindings"][0]

        return {
            "source": "dbpedia",
            "uri": dbpedia_uri,
            "abstract": self._extract_value(binding, "abstract"),
            "thumbnail": self._extract_value(binding, "thumbnail"),
            "birthDate": self._extract_value(binding, "birthDate"),
            "deathDate": self._extract_value(binding, "deathDate"),
            "birthPlace": (
                {
                    "uri": self._extract_value(binding, "birthPlace"),
                    "name": self._extract_value(binding, "birthPlaceName"),
                }
                if self._extract_value(binding, "birthPlace")
                else None
            ),
            "nationality": self._extract_value(binding, "nationality"),
            "movement": (
                {
                    "uri": self._extract_value(binding, "movement"),
                    "name": self._extract_value(binding, "movementName"),
                }
                if self._extract_value(binding, "movement")
                else None
            ),
            "wikidata_uri": self._extract_value(binding, "wikidata"),
        }

    # =========================================================================
    # Wikidata Methods
    # =========================================================================

    def get_wikidata_artwork_info(self, wikidata_uri: str) -> Dict[str, Any]:
        """
        Fetch artwork metadata from Wikidata.

        Args:
            wikidata_uri: Full Wikidata URI (e.g., http://www.wikidata.org/entity/Q12418)
                          or just the Q-ID (e.g., Q12418)

        Returns:
            Dictionary with image, inception date, materials, creator, and location
        """
        # Extract Q-ID from URI if needed
        if "/" in wikidata_uri:
            qid = wikidata_uri.split("/")[-1]
        else:
            qid = wikidata_uri

        cache_key = f"wikidata:artwork:{qid}"

        query = f"""
        PREFIX wd: <{self.PREFIXES['wd']}>
        PREFIX wdt: <{self.PREFIXES['wdt']}>
        PREFIX wikibase: <{self.PREFIXES['wikibase']}>
        PREFIX bd: <{self.PREFIXES['bd']}>
        
        SELECT ?image ?inception ?creator ?creatorLabel ?location ?locationLabel
               ?material ?materialLabel ?genre ?genreLabel ?movement ?movementLabel WHERE {{
            OPTIONAL {{ wd:{qid} wdt:P18 ?image }}
            OPTIONAL {{ wd:{qid} wdt:P571 ?inception }}
            OPTIONAL {{ 
                wd:{qid} wdt:P170 ?creator .
            }}
            OPTIONAL {{ 
                wd:{qid} wdt:P276 ?location .
            }}
            OPTIONAL {{ 
                wd:{qid} wdt:P186 ?material .
            }}
            OPTIONAL {{ 
                wd:{qid} wdt:P136 ?genre .
            }}
            OPTIONAL {{ 
                wd:{qid} wdt:P135 ?movement .
            }}
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,fr,de,es,it" }}
        }}
        LIMIT 1
        """

        results = self._execute_query(self.wikidata, query, cache_key)

        if not results or not results.get("results", {}).get("bindings"):
            return {"error": "No data found", "source": "wikidata", "uri": wikidata_uri}

        binding = results["results"]["bindings"][0]

        return {
            "source": "wikidata",
            "uri": f"http://www.wikidata.org/entity/{qid}",
            "qid": qid,
            "image": self._extract_value(binding, "image"),
            "inception": self._extract_value(binding, "inception"),
            "creator": (
                {
                    "uri": self._extract_value(binding, "creator"),
                    "label": self._extract_value(binding, "creatorLabel"),
                }
                if self._extract_value(binding, "creator")
                else None
            ),
            "location": (
                {
                    "uri": self._extract_value(binding, "location"),
                    "label": self._extract_value(binding, "locationLabel"),
                }
                if self._extract_value(binding, "location")
                else None
            ),
            "material": (
                {
                    "uri": self._extract_value(binding, "material"),
                    "label": self._extract_value(binding, "materialLabel"),
                }
                if self._extract_value(binding, "material")
                else None
            ),
            "genre": (
                {
                    "uri": self._extract_value(binding, "genre"),
                    "label": self._extract_value(binding, "genreLabel"),
                }
                if self._extract_value(binding, "genre")
                else None
            ),
            "movement": (
                {
                    "uri": self._extract_value(binding, "movement"),
                    "label": self._extract_value(binding, "movementLabel"),
                }
                if self._extract_value(binding, "movement")
                else None
            ),
        }

    def get_wikidata_artist_info(self, wikidata_uri: str) -> Dict[str, Any]:
        """
        Fetch artist information from Wikidata.

        Args:
            wikidata_uri: Full Wikidata URI or Q-ID

        Returns:
            Dictionary with biographical data and notable works
        """
        # Extract Q-ID from URI if needed
        if "/" in wikidata_uri:
            qid = wikidata_uri.split("/")[-1]
        else:
            qid = wikidata_uri

        cache_key = f"wikidata:artist:{qid}"

        query = f"""
        PREFIX wd: <{self.PREFIXES['wd']}>
        PREFIX wdt: <{self.PREFIXES['wdt']}>
        PREFIX wikibase: <{self.PREFIXES['wikibase']}>
        PREFIX bd: <{self.PREFIXES['bd']}>
        
        SELECT ?image ?birthDate ?deathDate ?birthPlace ?birthPlaceLabel
               ?nationality ?nationalityLabel ?occupation ?occupationLabel
               ?movement ?movementLabel WHERE {{
            OPTIONAL {{ wd:{qid} wdt:P18 ?image }}
            OPTIONAL {{ wd:{qid} wdt:P569 ?birthDate }}
            OPTIONAL {{ wd:{qid} wdt:P570 ?deathDate }}
            OPTIONAL {{ 
                wd:{qid} wdt:P19 ?birthPlace .
            }}
            OPTIONAL {{ 
                wd:{qid} wdt:P27 ?nationality .
            }}
            OPTIONAL {{ 
                wd:{qid} wdt:P106 ?occupation .
            }}
            OPTIONAL {{ 
                wd:{qid} wdt:P135 ?movement .
            }}
            SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en,fr,de,es,it" }}
        }}
        LIMIT 1
        """

        results = self._execute_query(self.wikidata, query, cache_key)

        if not results or not results.get("results", {}).get("bindings"):
            return {"error": "No data found", "source": "wikidata", "uri": wikidata_uri}

        binding = results["results"]["bindings"][0]

        return {
            "source": "wikidata",
            "uri": f"http://www.wikidata.org/entity/{qid}",
            "qid": qid,
            "image": self._extract_value(binding, "image"),
            "birthDate": self._extract_value(binding, "birthDate"),
            "deathDate": self._extract_value(binding, "deathDate"),
            "birthPlace": (
                {
                    "uri": self._extract_value(binding, "birthPlace"),
                    "label": self._extract_value(binding, "birthPlaceLabel"),
                }
                if self._extract_value(binding, "birthPlace")
                else None
            ),
            "nationality": (
                {
                    "uri": self._extract_value(binding, "nationality"),
                    "label": self._extract_value(binding, "nationalityLabel"),
                }
                if self._extract_value(binding, "nationality")
                else None
            ),
            "occupation": (
                {
                    "uri": self._extract_value(binding, "occupation"),
                    "label": self._extract_value(binding, "occupationLabel"),
                }
                if self._extract_value(binding, "occupation")
                else None
            ),
            "movement": (
                {
                    "uri": self._extract_value(binding, "movement"),
                    "label": self._extract_value(binding, "movementLabel"),
                }
                if self._extract_value(binding, "movement")
                else None
            ),
        }

    # =========================================================================
    # Getty AAT Methods
    # =========================================================================

    def get_getty_term(self, aat_uri: str) -> Dict[str, Any]:
        """
        Fetch term information from Getty Art & Architecture Thesaurus.

        Args:
            aat_uri: Full Getty AAT URI (e.g., http://vocab.getty.edu/aat/300015050)
                     or just the AAT ID (e.g., 300015050)

        Returns:
            Dictionary with preferred label, scope note, and hierarchy
        """
        # Normalize URI
        if not aat_uri.startswith("http"):
            aat_uri = f"http://vocab.getty.edu/aat/{aat_uri}"

        cache_key = f"getty:aat:{aat_uri}"

        query = f"""
        PREFIX skos: <{self.PREFIXES['skos']}>
        PREFIX gvp: <{self.PREFIXES['gvp']}>
        PREFIX rdfs: <{self.PREFIXES['rdfs']}>
        PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
        
        SELECT ?prefLabel ?scopeNote ?broader ?broaderLabel WHERE {{
            <{aat_uri}> skos:prefLabel ?prefLabel .
            FILTER(LANG(?prefLabel) = "en" || LANG(?prefLabel) = "")
            
            OPTIONAL {{ 
                <{aat_uri}> skos:scopeNote [rdf:value ?scopeNote] .
                FILTER(LANG(?scopeNote) = "en" || LANG(?scopeNote) = "")
            }}
            OPTIONAL {{
                <{aat_uri}> gvp:broaderGeneric ?broader .
                ?broader skos:prefLabel ?broaderLabel .
                FILTER(LANG(?broaderLabel) = "en" || LANG(?broaderLabel) = "")
            }}
        }}
        LIMIT 1
        """

        results = self._execute_query(self.getty, query, cache_key)

        if not results or not results.get("results", {}).get("bindings"):
            return {"error": "No data found", "source": "getty", "uri": aat_uri}

        binding = results["results"]["bindings"][0]

        return {
            "source": "getty",
            "uri": aat_uri,
            "prefLabel": self._extract_value(binding, "prefLabel"),
            "scopeNote": self._extract_value(binding, "scopeNote"),
            "broader": (
                {
                    "uri": self._extract_value(binding, "broader"),
                    "label": self._extract_value(binding, "broaderLabel"),
                }
                if self._extract_value(binding, "broader")
                else None
            ),
        }

    def lookup_getty_materials(self, material_uris: List[str]) -> List[Dict[str, Any]]:
        """
        Lookup multiple Getty AAT material terms.

        Args:
            material_uris: List of Getty AAT URIs

        Returns:
            List of term dictionaries
        """
        return [self.get_getty_term(uri) for uri in material_uris]

    # =========================================================================
    # Combined Enrichment
    # =========================================================================

    def enrich_from_local_uris(
        self,
        dbpedia_uri: Optional[str] = None,
        wikidata_uri: Optional[str] = None,
        getty_uris: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Enrich data from external sources based on provided URIs.

        Args:
            dbpedia_uri: DBpedia resource URI
            wikidata_uri: Wikidata entity URI
            getty_uris: List of Getty AAT URIs

        Returns:
            Combined enrichment data from all sources
        """
        enrichment = {
            "dbpedia": None,
            "wikidata": None,
            "getty": [],
        }

        if dbpedia_uri:
            enrichment["dbpedia"] = self.get_dbpedia_artwork_info(dbpedia_uri)

        if wikidata_uri:
            enrichment["wikidata"] = self.get_wikidata_artwork_info(wikidata_uri)

        if getty_uris:
            enrichment["getty"] = self.lookup_getty_materials(getty_uris)

        return enrichment


# Singleton instance
external_sparql_service = ExternalSPARQLService()
