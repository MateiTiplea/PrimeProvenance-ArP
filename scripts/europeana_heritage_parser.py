#!/usr/bin/env python3
"""
Europeana Heritage API to TTL Converter.

Fetches artwork data from Europeana Search/Record APIs,
enriches with Wikidata/DBpedia, and generates RDF/TTL output
conforming to the ArP ontology.

Usage:
    python europeana_heritage_parser.py --count 10 --api-key YOUR_KEY
    python europeana_heritage_parser.py --count 50 --query "paintings"
    python europeana_heritage_parser.py --all --provider "Rijksmuseum"
    python europeana_heritage_parser.py --count 10 --no-enrichment
"""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests
from dotenv import load_dotenv
from rdflib import Graph, Literal, Namespace, URIRef
from rdflib.namespace import DC, DCTERMS, OWL, RDF, RDFS, XSD
from SPARQLWrapper import JSON, SPARQLWrapper
from SPARQLWrapper.SPARQLExceptions import SPARQLWrapperException

# =============================================================================
# NAMESPACE DEFINITIONS
# =============================================================================

# RDF namespaces for TTL output
ARP = Namespace("http://example.org/arp#")
SCHEMA = Namespace("http://schema.org/")
PROV = Namespace("http://www.w3.org/ns/prov#")
CRM = Namespace("http://www.cidoc-crm.org/cidoc-crm/")
AAT = Namespace("http://vocab.getty.edu/aat/")
DBR = Namespace("http://dbpedia.org/resource/")
WD = Namespace("http://www.wikidata.org/entity/")

# =============================================================================
# EUROPEANA API CONFIGURATION
# =============================================================================

EUROPEANA_SEARCH_URL = "https://api.europeana.eu/record/v2/search.json"
EUROPEANA_RECORD_URL = "https://api.europeana.eu/record/v2"

# =============================================================================
# SPARQL ENDPOINTS
# =============================================================================

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
DBPEDIA_ENDPOINT = "https://dbpedia.org/sparql"

# =============================================================================
# GETTY AAT VOCABULARY MAPPINGS
# =============================================================================

# Map artwork types and materials to Getty AAT concept URIs
GETTY_AAT_MAPPINGS = {
    # Artwork types
    "painting": "http://vocab.getty.edu/aat/300033618",
    "paintings": "http://vocab.getty.edu/aat/300033618",
    "oil painting": "http://vocab.getty.edu/aat/300033618",
    "watercolor": "http://vocab.getty.edu/aat/300078925",
    "watercolour": "http://vocab.getty.edu/aat/300078925",
    "drawing": "http://vocab.getty.edu/aat/300033973",
    "drawings": "http://vocab.getty.edu/aat/300033973",
    "sketch": "http://vocab.getty.edu/aat/300033973",
    "sculpture": "http://vocab.getty.edu/aat/300047090",
    "sculptures": "http://vocab.getty.edu/aat/300047090",
    "print": "http://vocab.getty.edu/aat/300041340",
    "prints": "http://vocab.getty.edu/aat/300041340",
    "engraving": "http://vocab.getty.edu/aat/300041340",
    "etching": "http://vocab.getty.edu/aat/300041365",
    "lithograph": "http://vocab.getty.edu/aat/300041379",
    "photograph": "http://vocab.getty.edu/aat/300046300",
    "photography": "http://vocab.getty.edu/aat/300046300",
    "icon": "http://vocab.getty.edu/aat/300074603",
    "mosaic": "http://vocab.getty.edu/aat/300015342",
    "fresco": "http://vocab.getty.edu/aat/300177433",
    "portrait": "http://vocab.getty.edu/aat/300015637",
    "landscape": "http://vocab.getty.edu/aat/300015636",
    "still life": "http://vocab.getty.edu/aat/300015638",
    "tapestry": "http://vocab.getty.edu/aat/300205002",
    "ceramic": "http://vocab.getty.edu/aat/300151343",
    "pottery": "http://vocab.getty.edu/aat/300151343",
    "textile": "http://vocab.getty.edu/aat/300014063",
    # Materials
    "oil": "http://vocab.getty.edu/aat/300015050",
    "oil on canvas": "http://vocab.getty.edu/aat/300015050",
    "tempera": "http://vocab.getty.edu/aat/300015062",
    "acrylic": "http://vocab.getty.edu/aat/300015058",
    "bronze": "http://vocab.getty.edu/aat/300010957",
    "marble": "http://vocab.getty.edu/aat/300011443",
    "wood": "http://vocab.getty.edu/aat/300011914",
    "paper": "http://vocab.getty.edu/aat/300014109",
    "canvas": "http://vocab.getty.edu/aat/300014078",
    "cardboard": "http://vocab.getty.edu/aat/300014224",
    "panel": "http://vocab.getty.edu/aat/300014657",
    "copper": "http://vocab.getty.edu/aat/300011020",
    "glass": "http://vocab.getty.edu/aat/300010797",
    "gold": "http://vocab.getty.edu/aat/300011021",
    "silver": "http://vocab.getty.edu/aat/300011029",
    "ivory": "http://vocab.getty.edu/aat/300011857",
    "stone": "http://vocab.getty.edu/aat/300011176",
    "terracotta": "http://vocab.getty.edu/aat/300010669",
    "plaster": "http://vocab.getty.edu/aat/300014922",
    "ink": "http://vocab.getty.edu/aat/300015012",
    "graphite": "http://vocab.getty.edu/aat/300011098",
    "charcoal": "http://vocab.getty.edu/aat/300022414",
    "pastel": "http://vocab.getty.edu/aat/300404632",
    "gouache": "http://vocab.getty.edu/aat/300070114",
    # Techniques
    "engraved": "http://vocab.getty.edu/aat/300053225",
    "casting": "http://vocab.getty.edu/aat/300053104",
    "carving": "http://vocab.getty.edu/aat/300053149",
    # Art periods/movements
    "impressionism": "http://vocab.getty.edu/aat/300021503",
    "impressionist": "http://vocab.getty.edu/aat/300021503",
    "post-impressionism": "http://vocab.getty.edu/aat/300021508",
    "romanticism": "http://vocab.getty.edu/aat/300172863",
    "romantic": "http://vocab.getty.edu/aat/300172863",
    "realism": "http://vocab.getty.edu/aat/300172861",
    "realist": "http://vocab.getty.edu/aat/300172861",
    "expressionism": "http://vocab.getty.edu/aat/300021505",
    "expressionist": "http://vocab.getty.edu/aat/300021505",
    "baroque": "http://vocab.getty.edu/aat/300021147",
    "renaissance": "http://vocab.getty.edu/aat/300021140",
    "gothic": "http://vocab.getty.edu/aat/300020775",
    "medieval": "http://vocab.getty.edu/aat/300020756",
    "modern": "http://vocab.getty.edu/aat/300264736",
    "contemporary": "http://vocab.getty.edu/aat/300264736",
    "abstract": "http://vocab.getty.edu/aat/300056508",
    "cubism": "http://vocab.getty.edu/aat/300021495",
    "cubist": "http://vocab.getty.edu/aat/300021495",
    "surrealism": "http://vocab.getty.edu/aat/300021515",
    "surrealist": "http://vocab.getty.edu/aat/300021515",
    # Romanian terms
    "portret": "http://vocab.getty.edu/aat/300015637",  # portrait
    "peisaj": "http://vocab.getty.edu/aat/300015636",  # landscape
    "natură moartă": "http://vocab.getty.edu/aat/300015638",  # still life
    "natura moarta": "http://vocab.getty.edu/aat/300015638",  # still life (no diacritics)
    "pictură": "http://vocab.getty.edu/aat/300177435",  # painting
    "pictura": "http://vocab.getty.edu/aat/300177435",  # painting (no diacritics)
    "tablou": "http://vocab.getty.edu/aat/300177435",  # painting/tableau
    "ulei": "http://vocab.getty.edu/aat/300015050",  # oil
    "ulei pe pânză": "http://vocab.getty.edu/aat/300015050",  # oil on canvas
    "ulei pe panza": "http://vocab.getty.edu/aat/300015050",  # oil on canvas (no diacritics)
    "sculptură": "http://vocab.getty.edu/aat/300047090",  # sculpture
    "sculptura": "http://vocab.getty.edu/aat/300047090",  # sculpture (no diacritics)
    "desen": "http://vocab.getty.edu/aat/300033973",  # drawing
    "gravură": "http://vocab.getty.edu/aat/300041340",  # engraving
    "gravura": "http://vocab.getty.edu/aat/300041340",  # engraving (no diacritics)
    "acuarelă": "http://vocab.getty.edu/aat/300078925",  # watercolor
    "acuarela": "http://vocab.getty.edu/aat/300078925",  # watercolor (no diacritics)
    "icoană": "http://vocab.getty.edu/aat/300074603",  # icon
    "icoana": "http://vocab.getty.edu/aat/300074603",  # icon (no diacritics)
    "frescă": "http://vocab.getty.edu/aat/300177433",  # fresco
    "fresca": "http://vocab.getty.edu/aat/300177433",  # fresco (no diacritics)
    "mozaic": "http://vocab.getty.edu/aat/300015342",  # mosaic
    "tapiserie": "http://vocab.getty.edu/aat/300205002",  # tapestry
    "ceramică": "http://vocab.getty.edu/aat/300151343",  # ceramic
    "ceramica": "http://vocab.getty.edu/aat/300151343",  # ceramic (no diacritics)
    "lemn": "http://vocab.getty.edu/aat/300011914",  # wood
    "bronz": "http://vocab.getty.edu/aat/300010957",  # bronze
    "marmură": "http://vocab.getty.edu/aat/300011443",  # marble
    "marmura": "http://vocab.getty.edu/aat/300011443",  # marble (no diacritics)
    "hârtie": "http://vocab.getty.edu/aat/300014109",  # paper
    "hartie": "http://vocab.getty.edu/aat/300014109",  # paper (no diacritics)
    "pânză": "http://vocab.getty.edu/aat/300014078",  # canvas
    "panza": "http://vocab.getty.edu/aat/300014078",  # canvas (no diacritics)
    "panou": "http://vocab.getty.edu/aat/300014657",  # panel
    "țăran": "http://vocab.getty.edu/aat/300025607",  # peasant (genre)
    "taran": "http://vocab.getty.edu/aat/300025607",  # peasant (no diacritics)
    "țărancă": "http://vocab.getty.edu/aat/300025607",  # peasant woman
    "taranca": "http://vocab.getty.edu/aat/300025607",  # peasant woman (no diacritics)
    "femeie": "http://vocab.getty.edu/aat/300189557",  # woman (subject)
    "bărbat": "http://vocab.getty.edu/aat/300189559",  # man (subject)
    "barbat": "http://vocab.getty.edu/aat/300189559",  # man (no diacritics)
    "copil": "http://vocab.getty.edu/aat/300247598",  # child (subject)
    "fetiță": "http://vocab.getty.edu/aat/300247589",  # girl
    "fetita": "http://vocab.getty.edu/aat/300247589",  # girl (no diacritics)
    "băiat": "http://vocab.getty.edu/aat/300247599",  # boy
    "baiat": "http://vocab.getty.edu/aat/300247599",  # boy (no diacritics)
    "călare": "http://vocab.getty.edu/aat/300264578",  # equestrian
    "calare": "http://vocab.getty.edu/aat/300264578",  # equestrian (no diacritics)
    "cal": "http://vocab.getty.edu/aat/300250125",  # horse
    # Dutch terms
    "schilderij": "http://vocab.getty.edu/aat/300177435",  # painting
    "portret": "http://vocab.getty.edu/aat/300015637",  # portrait
    "landschap": "http://vocab.getty.edu/aat/300015636",  # landscape
    "stilleven": "http://vocab.getty.edu/aat/300015638",  # still life
    "tekening": "http://vocab.getty.edu/aat/300033973",  # drawing
    "prent": "http://vocab.getty.edu/aat/300041273",  # print
    "paneel": "http://vocab.getty.edu/aat/300014657",  # panel
    "doek": "http://vocab.getty.edu/aat/300014078",  # canvas
    "olieverf": "http://vocab.getty.edu/aat/300015050",  # oil paint
    "hout": "http://vocab.getty.edu/aat/300011914",  # wood
    "papier": "http://vocab.getty.edu/aat/300014109",  # paper
    # French terms
    "peinture": "http://vocab.getty.edu/aat/300177435",  # painting
    "tableau": "http://vocab.getty.edu/aat/300177435",  # painting
    "dessin": "http://vocab.getty.edu/aat/300033973",  # drawing
    "huile": "http://vocab.getty.edu/aat/300015050",  # oil
    "huile sur toile": "http://vocab.getty.edu/aat/300015050",  # oil on canvas
    "toile": "http://vocab.getty.edu/aat/300014078",  # canvas
    "bois": "http://vocab.getty.edu/aat/300011914",  # wood
    "paysage": "http://vocab.getty.edu/aat/300015636",  # landscape
    "nature morte": "http://vocab.getty.edu/aat/300015638",  # still life
    # German terms
    "gemälde": "http://vocab.getty.edu/aat/300177435",  # painting
    "ölgemälde": "http://vocab.getty.edu/aat/300177435",  # oil painting
    "zeichnung": "http://vocab.getty.edu/aat/300033973",  # drawing
    "öl": "http://vocab.getty.edu/aat/300015050",  # oil
    "leinwand": "http://vocab.getty.edu/aat/300014078",  # canvas
    "holz": "http://vocab.getty.edu/aat/300011914",  # wood
    # Italian terms
    "dipinto": "http://vocab.getty.edu/aat/300177435",  # painting
    "pittura": "http://vocab.getty.edu/aat/300177435",  # painting
    "ritratto": "http://vocab.getty.edu/aat/300015637",  # portrait
    "paesaggio": "http://vocab.getty.edu/aat/300015636",  # landscape
    "olio su tela": "http://vocab.getty.edu/aat/300015050",  # oil on canvas
    "tela": "http://vocab.getty.edu/aat/300014078",  # canvas
    "legno": "http://vocab.getty.edu/aat/300011914",  # wood
}


# =============================================================================
# EUROPEANA API CLIENT
# =============================================================================


class EuropeanaClient:
    """HTTP client for Europeana Search and Record APIs."""

    def __init__(self, api_key: str, request_delay: float = 0.5):
        """
        Initialize the Europeana API client.

        Args:
            api_key: Europeana API key
            request_delay: Delay between API requests (rate limiting)
        """
        self.api_key = api_key
        self.request_delay = request_delay
        self.session = requests.Session()
        self.session.headers.update(
            {"User-Agent": "EuropeanaHeritageParser/1.0 (ArP Project)"}
        )

    def search(
        self,
        query: str = "*:*",
        qf: Optional[List[str]] = None,
        rows: int = 100,
        start: int = 1,
        profile: str = "rich",
        reusability: str = "open",
    ) -> Dict[str, Any]:
        """
        Search the Europeana collection.

        Args:
            query: Search query string
            qf: Query filters (e.g., ["TYPE:IMAGE", "what:painting"])
            rows: Number of results per page (max 100)
            start: Starting record number (1-based)
            profile: Response profile (minimal, standard, rich)
            reusability: License filter (open, restricted, permission)

        Returns:
            API response as dictionary
        """
        params = {
            "wskey": self.api_key,
            "query": query,
            "rows": min(rows, 100),
            "start": start,
            "profile": profile,
            "reusability": reusability,
        }

        if qf:
            params["qf"] = qf

        time.sleep(self.request_delay)

        try:
            response = self.session.get(EUROPEANA_SEARCH_URL, params=params, timeout=30)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            print(f"Error searching Europeana: {e}", file=sys.stderr)
            return {"success": False, "error": str(e), "items": [], "totalResults": 0}

    def get_record(self, record_id: str) -> Optional[Dict[str, Any]]:
        """
        Fetch a single record by ID.

        Args:
            record_id: Europeana record ID (e.g., "/2021672/resource_document_mauritshuis_670")

        Returns:
            Record data or None if not found
        """
        # Ensure record_id starts with /
        if not record_id.startswith("/"):
            record_id = "/" + record_id

        url = f"{EUROPEANA_RECORD_URL}{record_id}.json"
        params = {"wskey": self.api_key}

        time.sleep(self.request_delay)

        try:
            response = self.session.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            return data.get("object")
        except requests.RequestException as e:
            print(f"Error fetching record {record_id}: {e}", file=sys.stderr)
            return None

    def search_artworks(
        self,
        query: str = "painting",
        provider: Optional[str] = None,
        country: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Search for artworks with pagination.

        Args:
            query: Search query
            provider: Filter by data provider
            country: Filter by country (e.g., 'Romania', 'Netherlands')
            limit: Maximum number of results (None for all)

        Returns:
            List of artwork items from search results
        """
        artworks = []
        start = 1
        rows_per_page = 100

        # Build query filters for visual artworks with quality constraints
        qf = [
            "TYPE:IMAGE",
            "contentTier:(3 OR 4)",  # Higher quality content tiers
            "MEDIA:true",  # Must have media
        ]
        if provider:
            qf.append(f'DATA_PROVIDER:"{provider}"')
        if country:
            qf.append(f'COUNTRY:"{country}"')

        while True:
            print(f"  Fetching records {start} to {start + rows_per_page - 1}...")
            result = self.search(
                query=query, qf=qf, rows=rows_per_page, start=start, profile="rich"
            )

            if not result.get("success", True) or "items" not in result:
                print(f"  Search failed or no items found", file=sys.stderr)
                break

            items = result.get("items", [])
            if not items:
                break

            artworks.extend(items)

            if limit and len(artworks) >= limit:
                artworks = artworks[:limit]
                break

            total_results = result.get("totalResults", 0)
            if start + rows_per_page > total_results:
                break

            start += rows_per_page

        return artworks


# =============================================================================
# EUROPEANA DATA PARSER
# =============================================================================


class EuropeanaParser:
    """Parser for Europeana Data Model (EDM) JSON responses."""

    @staticmethod
    def parse_search_item(item: Dict[str, Any]) -> Dict[str, Any]:
        """
        Parse a search result item into artwork dictionary.

        Args:
            item: Europeana search result item

        Returns:
            Normalized artwork dictionary
        """
        # Extract ID
        record_id = item.get("id", "")
        artwork_id = EuropeanaParser._create_id_from_europeana(record_id)

        # Extract title (prefer English, fallback to any language)
        title = EuropeanaParser._get_lang_value(item.get("dcTitleLangAware", {}))
        if not title:
            titles = item.get("title", [])
            title = titles[0] if titles else None

        # Validate title - skip generic/repetitive titles
        if title:
            title = EuropeanaParser._clean_title(title)

        # Extract creator/artist - try multiple fields
        creator_concepts = []
        creator = EuropeanaParser._get_lang_value(
            item.get("dcCreatorLangAware", {}), ignore_urls=True
        )
        creator_concepts.extend(
            EuropeanaParser._get_concept_uris(item.get("dcCreatorLangAware", {}))
        )

        if not creator:
            creators = item.get("dcCreator", [])
            # Filter URLs from list
            creators = [
                c for c in creators if not (isinstance(c, str) and c.startswith("http"))
            ]
            creator = creators[0] if creators else None

        if not creator:
            # Try edmAgentLabelLangAware (Europeana agent labels)
            creator = EuropeanaParser._get_lang_value(
                item.get("edmAgentLabelLangAware", {}), ignore_urls=True
            )
        if not creator:
            # Try dcContributorLangAware
            creator = EuropeanaParser._get_lang_value(
                item.get("dcContributorLangAware", {}), ignore_urls=True
            )
            creator_concepts.extend(
                EuropeanaParser._get_concept_uris(
                    item.get("dcContributorLangAware", {})
                )
            )

        if not creator:
            creators = item.get("dcContributor", [])
            creators = [
                c for c in creators if not (isinstance(c, str) and c.startswith("http"))
            ]
            creator = creators[0] if creators else None

        # Extract date
        years = item.get("year", [])
        date_created = years[0] if years else None

        # Extract description - prefer English, fallback to original language with proper tag
        description, description_lang = EuropeanaParser._get_lang_value_with_lang(
            item.get("dcDescriptionLangAware", {}),
            strict_english=False,
            ignore_urls=True,
        )

        # Extract description concepts (often subject/style)
        description_concepts = EuropeanaParser._get_concept_uris(
            item.get("dcDescriptionLangAware", {})
        )

        # Extract dimensions from various fields
        dimensions = None
        # Try dctermsExtent (common for Rijksmuseum)
        extent_values = item.get("dctermsExtent", [])
        if extent_values:
            dimensions = (
                extent_values[0] if isinstance(extent_values, list) else extent_values
            )
        # Try dcFormat which sometimes contains dimensions
        if not dimensions:
            format_values = item.get("dcFormat", [])
            if format_values:
                for fmt in format_values:
                    # Look for dimension patterns like "100 x 80 cm" or "h 45cm × w 30cm"
                    if fmt and re.search(
                        r"\d+\s*[x×]\s*\d+|\d+\s*(cm|mm|in)", fmt, re.I
                    ):
                        dimensions = fmt
                        break

        # Extract image URL
        image_url = None
        previews = item.get("edmPreview", [])
        if previews:
            image_url = previews[0]
        if not image_url:
            shown_by = item.get("edmIsShownBy", [])
            if shown_by:
                image_url = shown_by[0]

        # Extract provider/location
        providers = item.get("dataProvider", [])
        repository = providers[0] if providers else None

        # Extract high-level type (e.g. IMAGE)
        types = item.get("type", [])
        obj_type = types[0] if isinstance(types, list) and types else types

        # Extract type/medium - ensure we get text, not URLs
        media_concepts = []  # URIs for medium/format

        dc_type = EuropeanaParser._get_lang_value(
            item.get("dcTypeLangAware", {}), ignore_urls=True
        )
        media_concepts.extend(
            EuropeanaParser._get_concept_uris(item.get("dcTypeLangAware", {}))
        )

        dc_format = EuropeanaParser._get_lang_value(
            item.get("dcFormatLangAware", {}), ignore_urls=True
        )
        media_concepts.extend(
            EuropeanaParser._get_concept_uris(item.get("dcFormatLangAware", {}))
        )

        medium = dc_format or dc_type

        # Also check simple lists for medium if LangAware failed (ignoring URLs)
        if not medium:
            types = item.get("type", [])
            types = [
                t for t in types if not (isinstance(t, str) and t.startswith("http"))
            ]
            if types:
                medium = types[0]

        # Extract edmConcept URIs
        edm_concepts = item.get("edmConcept", [])
        if edm_concepts:
            media_concepts.extend(edm_concepts)

        # Extract country
        countries = item.get("country", [])
        country = countries[0] if countries else None

        # Extract rights/license
        rights = item.get("rights", [])
        license_url = rights[0] if rights else None

        # Extract link to original record
        shown_at = item.get("edmIsShownAt", [])
        record_url = shown_at[0] if shown_at else None
        if not record_url:
            guid = item.get("guid")
            if guid:
                record_url = guid

        # Extract time span data for richer provenance
        time_spans = item.get("edmTimespan", [])
        time_span_labels = item.get("edmTimespanLabel", [])

        return {
            "id": artwork_id,
            "europeana_id": record_id,
            "title": title,
            "title_lang": "en",
            "object_type": obj_type,
            "description": description,
            "description_lang": description_lang,
            "materials_technique": {"material": medium, "technique": None},
            "creator": EuropeanaParser._clean_creator_name(creator),
            "creation_date": date_created,
            "repository": repository,
            "country": country,
            "image_url": image_url,
            "record_url": record_url,
            "license": license_url,
            "dimensions": dimensions,
            "time_spans": time_spans,
            "time_span_labels": time_span_labels,
            "description_concepts": description_concepts,
            "media_concepts": media_concepts,
            "creator_concepts": creator_concepts,
        }

    @staticmethod
    def parse_full_record(
        record: Dict[str, Any], existing_artwork: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Parse a full EDM record and merge with existing artwork data.

        This extracts additional metadata from the Record API that isn't
        available in the Search API, such as provenance and detailed dimensions.

        Args:
            record: Full EDM record from Record API
            existing_artwork: Artwork dict from parse_search_item

        Returns:
            Updated artwork dictionary with additional fields
        """
        artwork = existing_artwork.copy()

        if not record:
            return artwork

        # Get proxies (contains most metadata)
        proxies = record.get("proxies", [])
        provider_proxy = None
        europeana_proxy = None

        for proxy in proxies:
            if proxy.get("europeanaProxy"):
                europeana_proxy = proxy
            else:
                provider_proxy = proxy

        # Use provider proxy primarily (original metadata), fallback to europeana proxy
        main_proxy = provider_proxy or europeana_proxy or {}

        # Extract provenance (dcterms:provenance)
        provenance_data = main_proxy.get("dctermsProvenance", {})
        if provenance_data:
            provenance_text = EuropeanaParser._extract_edm_value(
                provenance_data, prefer_english=True
            )
            if provenance_text:
                artwork["provenance_text"] = provenance_text

        # Extract dimensions from dcterms:extent
        # Europeana often provides height and width as separate entries like:
        # "height 94.5 cm", "width 162 cm"
        extent_data = main_proxy.get("dctermsExtent", {})
        if extent_data and not artwork.get("dimensions"):
            # Get all extent values
            extent_values = EuropeanaParser._extract_edm_all_values(extent_data)

            height = None
            width = None

            for val in extent_values:
                if not val:
                    continue
                val_lower = val.lower()

                # Match patterns like "height 94.5 cm" or "h 94,5 cm" or "hoogte 94,5 cm"
                height_match = re.search(
                    r"(?:height|h|hoogte|drager hoogte)\s*[:\s]*(\d+[,.]?\d*)\s*(cm|mm|m\b|in)?",
                    val_lower,
                )
                if height_match:
                    h = height_match.group(1).replace(",", ".")
                    height = float(h)
                    continue

                # Match patterns like "width 162 cm" or "w 162 cm" or "breedte 162 cm"
                width_match = re.search(
                    r"(?:width|w|breedte|drager breedte)\s*[:\s]*(\d+[,.]?\d*)\s*(cm|mm|m\b|in)?",
                    val_lower,
                )
                if width_match:
                    w = width_match.group(1).replace(",", ".")
                    width = float(w)
                    continue

                # Also try generic dimension pattern like "94.5 x 162 cm"
                combined_match = re.search(
                    r"(\d+[,.]?\d*)\s*[x×]\s*(\d+[,.]?\d*)\s*(cm|mm|m\b|in)?", val_lower
                )
                if combined_match:
                    height = float(combined_match.group(1).replace(",", "."))
                    width = float(combined_match.group(2).replace(",", "."))
                    break

            if height is not None and width is not None:
                # Format: height × width cm
                h_str = f"{height:.1f}" if height != int(height) else str(int(height))
                w_str = f"{width:.1f}" if width != int(width) else str(int(width))
                artwork["dimensions"] = f"{h_str} × {w_str} cm"
            elif height is not None:
                h_str = f"{height:.1f}" if height != int(height) else str(int(height))
                artwork["dimensions"] = f"h: {h_str} cm"
            elif width is not None:
                w_str = f"{width:.1f}" if width != int(width) else str(int(width))
                artwork["dimensions"] = f"w: {w_str} cm"

        # Also try dcFormat for dimensions/materials
        format_data = main_proxy.get("dcFormat", {})
        if format_data:
            format_values = EuropeanaParser._extract_edm_all_values(format_data)
            for fmt in format_values:
                # Check if it looks like dimension info
                if fmt and re.search(
                    r"\d+\s*[x×]\s*\d+|\d+\s*(cm|mm|m\b|in)", fmt, re.I
                ):
                    if not artwork.get("dimensions"):
                        artwork["dimensions"] = fmt
                # Check if it's material/technique info
                elif fmt and not artwork.get("materials_technique", {}).get(
                    "technique"
                ):
                    if any(
                        kw in fmt.lower()
                        for kw in [
                            "oil",
                            "canvas",
                            "panel",
                            "paper",
                            "wood",
                            "tempera",
                            "watercolor",
                            "gouache",
                        ]
                    ):
                        if artwork.get("materials_technique"):
                            artwork["materials_technique"]["technique"] = fmt
                        else:
                            artwork["materials_technique"] = {
                                "material": fmt,
                                "technique": None,
                            }

        # Extract better description if available (prefer English)
        desc_data = main_proxy.get("dcDescription", {})
        if desc_data:
            desc, desc_lang = EuropeanaParser._extract_edm_value_with_lang(
                desc_data, prefer_english=True
            )
            # Only replace if we found an English description and current isn't English
            if desc and desc_lang == "en" and artwork.get("description_lang") != "en":
                artwork["description"] = desc
                artwork["description_lang"] = "en"
            # Or if we have no description at all
            elif desc and not artwork.get("description"):
                artwork["description"] = desc
                artwork["description_lang"] = desc_lang

        # Extract dcterms:medium for materials
        medium_data = main_proxy.get("dctermsMedium", {})
        if medium_data:
            medium = EuropeanaParser._extract_edm_value(
                medium_data, prefer_english=True
            )
            if medium and artwork.get("materials_technique"):
                if not artwork["materials_technique"].get("material"):
                    artwork["materials_technique"]["material"] = medium

        # Extract dc:subject for style/genre hints
        subject_data = main_proxy.get("dcSubject", {})
        if subject_data:
            subjects = EuropeanaParser._extract_edm_all_values(subject_data)
            if subjects:
                artwork["subjects"] = subjects

        # Extract dcterms:created for more precise dates
        created_data = main_proxy.get("dctermsCreated", {})
        if created_data and not artwork.get("creation_date"):
            created = EuropeanaParser._extract_edm_value(created_data)
            if created:
                artwork["creation_date"] = created

        # Extract acquisition/collection info from dcterms:isPartOf
        part_of_data = main_proxy.get("dctermsIsPartOf", {})
        if part_of_data:
            collection = EuropeanaParser._extract_edm_value(
                part_of_data, prefer_english=True
            )
            if collection:
                artwork["collection"] = collection

        # Get aggregations for additional links
        aggregations = record.get("aggregations", [])
        if aggregations:
            agg = aggregations[0]
            # Higher quality image
            if not artwork.get("image_url"):
                artwork["image_url"] = agg.get("edmIsShownBy") or agg.get("edmObject")
            # Original record URL
            if not artwork.get("record_url"):
                artwork["record_url"] = agg.get("edmIsShownAt")

        # Extract Getty AAT URIs from concepts
        getty_aat_uris = set()
        concepts = record.get("concepts", [])
        for concept in concepts:
            # Check the concept's about URI
            about = concept.get("about", "")
            if "vocab.getty.edu/aat" in about:
                getty_aat_uris.add(about)

            # Also check exactMatch for Getty AAT links
            exact_matches = concept.get("exactMatch", [])
            for match in exact_matches:
                if isinstance(match, str) and "vocab.getty.edu/aat" in match:
                    getty_aat_uris.add(match)

        if getty_aat_uris:
            artwork["getty_aat_from_europeana"] = list(getty_aat_uris)

        # Extract artist Wikidata and DBpedia links from agents
        agents = record.get("agents", [])
        for agent in agents:
            owl_same_as = agent.get("owlSameAs", [])
            artist_wikidata = None
            artist_dbpedia = None

            for link in owl_same_as:
                if isinstance(link, str):
                    if "wikidata.org" in link:
                        artist_wikidata = link
                    elif "dbpedia.org" in link:
                        artist_dbpedia = link

            # Store if found - first agent is typically the creator
            if artist_wikidata or artist_dbpedia:
                if not artwork.get("artist_wikidata_from_europeana"):
                    artwork["artist_wikidata_from_europeana"] = artist_wikidata
                if not artwork.get("artist_dbpedia_from_europeana"):
                    artwork["artist_dbpedia_from_europeana"] = artist_dbpedia

                # Also get artist name from agent
                pref_label = agent.get("prefLabel", {})
                artist_name = EuropeanaParser._extract_edm_value(
                    pref_label, prefer_english=True
                )
                if artist_name and not artwork.get("artist_name_resolved"):
                    artwork["artist_name_resolved"] = artist_name

        return artwork

    @staticmethod
    def _extract_edm_value(data: Any, prefer_english: bool = False) -> Optional[str]:
        """Extract a single value from EDM field (handles various formats)."""
        if not data:
            return None

        # If it's a simple string
        if isinstance(data, str):
            return data

        # If it's a list
        if isinstance(data, list):
            if not data:
                return None
            # Try to find English value first
            if prefer_english:
                for item in data:
                    if isinstance(item, dict) and item.get("@language") == "en":
                        return item.get("@value")
            # Return first value
            first = data[0]
            if isinstance(first, dict):
                return first.get("@value") or first.get("def", [None])[0]
            return str(first) if first else None

        # If it's a dict with language keys
        if isinstance(data, dict):
            # Try English first
            if prefer_english and "en" in data:
                vals = data["en"]
                return vals[0] if isinstance(vals, list) else vals
            # Try def (default)
            if "def" in data:
                vals = data["def"]
                return vals[0] if isinstance(vals, list) else vals
            # Return any value
            for vals in data.values():
                if vals:
                    return vals[0] if isinstance(vals, list) else vals

        return None

    @staticmethod
    def _extract_edm_value_with_lang(data: Any, prefer_english: bool = False) -> tuple:
        """Extract value and language from EDM field."""
        if not data:
            return None, None

        if isinstance(data, str):
            return data, "en"  # Assume English for plain strings

        if isinstance(data, list):
            if not data:
                return None, None
            if prefer_english:
                for item in data:
                    if isinstance(item, dict) and item.get("@language") == "en":
                        return item.get("@value"), "en"
            first = data[0]
            if isinstance(first, dict):
                return first.get("@value"), first.get("@language", "en")
            return str(first) if first else None, "en"

        if isinstance(data, dict):
            if prefer_english and "en" in data:
                vals = data["en"]
                val = vals[0] if isinstance(vals, list) else vals
                return val, "en"
            for lang, vals in data.items():
                if vals:
                    val = vals[0] if isinstance(vals, list) else vals
                    return val, lang

        return None, None

    @staticmethod
    def _extract_edm_all_values(data: Any) -> List[str]:
        """Extract all values from EDM field."""
        values = []

        if not data:
            return values

        if isinstance(data, str):
            return [data]

        if isinstance(data, list):
            for item in data:
                if isinstance(item, dict):
                    val = item.get("@value")
                    if val:
                        values.append(val)
                elif item:
                    values.append(str(item))
            return values

        if isinstance(data, dict):
            for lang_vals in data.values():
                if isinstance(lang_vals, list):
                    values.extend([v for v in lang_vals if v])
                elif lang_vals:
                    values.append(lang_vals)

        return values

    @staticmethod
    def _get_lang_value(
        lang_dict: Dict[str, List[str]],
        preferred_langs: List[str] = None,
        ignore_urls: bool = False,
    ) -> Optional[str]:
        """
        Extract value from language-aware field, preferring certain languages.

        Args:
            lang_dict: Dictionary with language codes as keys
            preferred_langs: List of preferred language codes
            ignore_urls: If True, skip values that look like URLs

        Returns:
            Best matching value or None
        """
        value, _ = EuropeanaParser._get_lang_value_with_lang(
            lang_dict, preferred_langs, ignore_urls=ignore_urls
        )
        return value

    @staticmethod
    def _get_lang_value_with_lang(
        lang_dict: Dict[str, List[str]],
        preferred_langs: List[str] = None,
        strict_english: bool = False,
        ignore_urls: bool = False,
    ) -> tuple:
        """
        Extract value from language-aware field with language tracking.

        Args:
            lang_dict: Dictionary with language codes as keys
            preferred_langs: List of preferred language codes
            strict_english: If True, only return English content, else None
            ignore_urls: If True, skip values that look like URLs

        Returns:
            Tuple of (value, language) or (None, None)
        """
        if not lang_dict:
            return None, None

        if preferred_langs is None:
            preferred_langs = ["en", "def", ""]

        def is_url(v):
            return isinstance(v, str) and (
                v.startswith("http://") or v.startswith("https://")
            )

        # Try preferred languages first
        for lang in preferred_langs:
            if lang in lang_dict:
                values = lang_dict[lang]
                if values:
                    # Iterate values to find one that satisfies ignore_urls
                    candidates = values if isinstance(values, list) else [values]
                    for val in candidates:
                        if ignore_urls and is_url(val):
                            continue
                        return val, lang if lang else "en"

        # If strict English mode, don't fall back to other languages
        if strict_english:
            return None, None

        # Fallback to any available language
        for lang, values in lang_dict.items():
            if values:
                candidates = values if isinstance(values, list) else [values]
                for val in candidates:
                    if ignore_urls and is_url(val):
                        continue
                    return val, lang

        return None, None

    @staticmethod
    def _get_concept_uris(lang_dict: Dict[str, List[str]]) -> List[str]:
        """Extract concept URIs (starting with http) from language-aware field."""
        uris = set()
        if not lang_dict:
            return []

        for values in lang_dict.values():
            if not values:
                continue
            candidates = values if isinstance(values, list) else [values]
            for val in candidates:
                if isinstance(val, str) and (
                    val.startswith("http://") or val.startswith("https://")
                ):
                    uris.add(val)
        return list(uris)

    @staticmethod
    def _create_id_from_europeana(europeana_id: str) -> str:
        """Create a safe ID from Europeana record ID."""
        # Remove leading slash and replace special chars
        safe_id = europeana_id.lstrip("/")
        safe_id = re.sub(r"[^a-zA-Z0-9]+", "_", safe_id)
        safe_id = re.sub(r"_+", "_", safe_id)
        safe_id = safe_id.strip("_").lower()
        return f"europeana_{safe_id}"

    @staticmethod
    def _clean_title(title: str) -> Optional[str]:
        """Clean and validate title, return None if it's a generic/bad title."""
        if not title:
            return None

        # Remove excessive whitespace
        title = re.sub(r"\s+", " ", title).strip()

        # Skip titles that are just repeated words (e.g., "painting, painting, painting")
        words = [w.strip().lower() for w in title.split(",")]
        unique_words = set(words)
        if len(words) > 2 and len(unique_words) <= 2:
            return None

        # Skip very short or generic titles
        generic_titles = {
            "painting",
            "drawing",
            "sculpture",
            "print",
            "photograph",
            "untitled",
            "without title",
            "no title",
            "unknown",
            "image",
            "picture",
            "artwork",
            "art",
            "work",
        }
        if title.lower().strip() in generic_titles:
            return None

        # Skip titles that are just numbers or codes
        if re.match(r"^[\d\s\-_\.]+$", title):
            return None

        return title

    @staticmethod
    def _clean_creator_name(name: Optional[str]) -> Optional[str]:
        """Clean and normalize creator name."""
        if not name:
            return None

        # Remove common annotations
        name = re.sub(r"\s*\([^)]*\)\s*", " ", name)  # Remove parenthetical
        name = re.sub(r"\s*\[[^\]]*\]\s*", " ", name)  # Remove brackets
        name = re.sub(r"\s+", " ", name).strip()

        # Skip generic names
        if name.lower() in [
            "anonymous",
            "unknown",
            "unidentified",
            "anon",
            "n/a",
            "-",
        ]:
            return None

        return name


# =============================================================================
# ARTIST ENRICHMENT CACHE
# =============================================================================


class ArtistCache:
    """Cache for artist enrichment data to avoid duplicate SPARQL queries."""

    def __init__(self):
        self._cache: Dict[str, Dict[str, Any]] = {}

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
# DATA ENRICHER
# =============================================================================


class DataEnricher:
    """Enriches data using Wikidata, DBpedia, and Getty AAT vocabularies."""

    def __init__(self, cache: ArtistCache, verbose: bool = True):
        self.cache = cache
        self.verbose = verbose
        self._artwork_cache: Dict[str, Dict[str, Any]] = {}
        self._query_delay = 1.0

    def _log_warning(self, message: str) -> None:
        """Log a warning message if verbose mode is enabled."""
        if self.verbose:
            print(f"    ⚠ {message}", file=sys.stderr)

    def enrich_artist(self, artist_name: str) -> Dict[str, Any]:
        """
        Enrich artist information from Wikidata and DBpedia.

        Args:
            artist_name: Artist name

        Returns:
            Dictionary with enriched artist data
        """
        if not artist_name:
            return {}

        # Skip generic names
        if artist_name.lower() in ["anonymous", "unknown", "unidentified"]:
            return {}

        # Check cache first
        if self.cache.has(artist_name):
            return self.cache.get(artist_name)

        # Normalize name
        normalized_name = self._normalize_artist_name(artist_name)

        # Query Wikidata
        result = self._query_wikidata_artist(normalized_name)

        # Also query DBpedia
        dbpedia_result = self._query_dbpedia_artist(normalized_name)

        # Merge results
        if dbpedia_result.get("dbpedia_uri"):
            result["dbpedia_uri"] = dbpedia_result["dbpedia_uri"]
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
        Try to find artwork in Wikidata/DBpedia.

        Args:
            title: Artwork title
            artist_name: Optional artist name

        Returns:
            Dictionary with Wikidata/DBpedia URIs if found
        """
        cache_key = f"{title}|{artist_name or ''}"
        if cache_key in self._artwork_cache:
            return self._artwork_cache[cache_key]

        result = {"wikidata_uri": None, "dbpedia_uri": None, "dimensions": None}

        normalized_artist = (
            self._normalize_artist_name(artist_name) if artist_name else None
        )

        # Query Wikidata
        wikidata_result = self._query_wikidata_artwork(title, normalized_artist)
        result.update(wikidata_result)

        # Query DBpedia
        dbpedia_result = self._query_dbpedia_artwork(title, normalized_artist)
        if dbpedia_result.get("dbpedia_uri"):
            result["dbpedia_uri"] = dbpedia_result["dbpedia_uri"]

        self._artwork_cache[cache_key] = result
        return result

    def get_getty_aat_uris(self, artwork: Dict[str, Any]) -> List[str]:
        """
        Get Getty AAT URIs for an artwork based on its type and materials.

        Args:
            artwork: Parsed artwork data

        Returns:
            List of Getty AAT URIs
        """
        aat_uris = []
        artwork_title = artwork.get("title", "Unknown")[:40]

        # Check object type
        obj_type = artwork.get("object_type", "")
        obj_type_matched = False
        if obj_type:
            obj_type_lower = obj_type.lower()
            for key, uri in GETTY_AAT_MAPPINGS.items():
                if key in obj_type_lower:
                    aat_uris.append(uri)
                    obj_type_matched = True
                    break

        # Check materials/technique
        materials = artwork.get("materials_technique", {})
        material_text = materials.get("material", "") or ""
        technique_text = materials.get("technique", "") or ""
        combined = f"{material_text} {technique_text}".lower()

        for key, uri in GETTY_AAT_MAPPINGS.items():
            if key in combined and uri not in aat_uris:
                aat_uris.append(uri)

        # Check description for style/period hints
        description = artwork.get("description", "") or ""
        description_lower = description.lower()
        for key, uri in GETTY_AAT_MAPPINGS.items():
            if key in description_lower and uri not in aat_uris:
                aat_uris.append(uri)
                if len(aat_uris) >= 5:  # Limit to avoid too many matches
                    break

        if not aat_uris:
            self._log_warning(f"Getty AAT: No vocabulary matches for '{artwork_title}'")

        return aat_uris

    @staticmethod
    def _normalize_artist_name(name: str) -> str:
        """Normalize artist name for SPARQL queries."""
        # Remove special characters
        name = name.replace("~", "").strip()

        # Remove parenthetical annotations
        name = re.sub(r"\s*\([^)]*\)\s*", " ", name)

        # Handle "Surname, FirstName" format
        if "," in name:
            parts = name.split(",", 1)
            if len(parts) == 2:
                return f"{parts[1].strip()} {parts[0].strip()}"

        return re.sub(r"\s+", " ", name).strip()

    def _query_wikidata_artist(self, artist_name: str) -> Dict[str, Any]:
        """Query Wikidata for artist using MediaWiki search API (faster than SPARQL)."""
        result = {
            "wikidata_uri": None,
            "birth_date": None,
            "death_date": None,
            "nationality": None,
            "description": None,
        }

        try:
            # Step 1: Use Wikidata's fast search API to find the entity
            search_url = "https://www.wikidata.org/w/api.php"
            params = {
                "action": "wbsearchentities",
                "search": artist_name,
                "language": "en",
                "type": "item",
                "limit": 5,
                "format": "json",
            }

            time.sleep(self._query_delay)
            headers = {
                "User-Agent": "EuropeanaHeritageParser/1.0 (ArP Project; https://github.com/example/arp)"
            }
            response = requests.get(
                search_url, params=params, headers=headers, timeout=5
            )
            response.raise_for_status()
            data = response.json()

            search_results = data.get("search", [])
            if not search_results:
                self._log_warning(f"Wikidata: No artist found for '{artist_name}'")
                return result

            # Step 2: Get details for the first result using simple SPARQL
            for item in search_results:
                entity_id = item.get("id")
                if not entity_id:
                    continue

                entity_uri = f"http://www.wikidata.org/entity/{entity_id}"

                # Simple query to verify it's a human and get details
                query = f"""
                SELECT ?birthDate ?deathDate ?nationalityLabel ?description WHERE {{
                  wd:{entity_id} wdt:P31 wd:Q5 .
                  OPTIONAL {{ wd:{entity_id} wdt:P569 ?birthDate . }}
                  OPTIONAL {{ wd:{entity_id} wdt:P570 ?deathDate . }}
                  OPTIONAL {{ wd:{entity_id} wdt:P27 ?nationality . }}
                  OPTIONAL {{ wd:{entity_id} schema:description ?description . FILTER(LANG(?description) = "en") }}
                  SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
                }}
                LIMIT 1
                """

                sparql = SPARQLWrapper(WIKIDATA_ENDPOINT)
                sparql.setQuery(query)
                sparql.setReturnFormat(JSON)
                sparql.setTimeout(5)
                sparql.addCustomHttpHeader(
                    "User-Agent", "EuropeanaHeritageParser/1.0 (ArP Project)"
                )

                time.sleep(0.3)
                results = sparql.query().convert()
                bindings = results.get("results", {}).get("bindings", [])

                if bindings:
                    binding = bindings[0]
                    result["wikidata_uri"] = entity_uri
                    result["birth_date"] = self._extract_date(
                        binding.get("birthDate", {}).get("value")
                    )
                    result["death_date"] = self._extract_date(
                        binding.get("deathDate", {}).get("value")
                    )
                    result["nationality"] = binding.get("nationalityLabel", {}).get(
                        "value"
                    )
                    result["description"] = binding.get("description", {}).get("value")
                    return result

            self._log_warning(f"Wikidata: No artist found for '{artist_name}'")

        except Exception as e:
            self._log_warning(f"Wikidata artist query failed for '{artist_name}': {e}")

        return result

    def _query_wikidata_artwork(
        self, title: str, artist_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Query Wikidata for artwork using MediaWiki search API (faster than SPARQL)."""
        result = {"wikidata_uri": None}

        try:
            # Use Wikidata's fast search API
            search_url = "https://www.wikidata.org/w/api.php"
            params = {
                "action": "wbsearchentities",
                "search": title,
                "language": "en",
                "type": "item",
                "limit": 10,
                "format": "json",
            }

            time.sleep(self._query_delay)
            headers = {
                "User-Agent": "EuropeanaHeritageParser/1.0 (ArP Project; https://github.com/example/arp)"
            }
            response = requests.get(
                search_url, params=params, headers=headers, timeout=5
            )
            response.raise_for_status()
            data = response.json()

            search_results = data.get("search", [])
            if not search_results:
                # Try Dutch language search for Rijksmuseum artworks
                params["language"] = "nl"
                response = requests.get(
                    search_url, params=params, headers=headers, timeout=5
                )
                response.raise_for_status()
                data = response.json()
                search_results = data.get("search", [])

            if not search_results:
                self._log_warning(f"Wikidata: No artwork found for '{title[:40]}...'")
                return result

            # Verify each result is actually an artwork
            artwork_types = {"Q3305213", "Q4502142", "Q838948", "Q18573970", "Q93184"}
            for item in search_results:
                entity_id = item.get("id")
                if not entity_id:
                    continue

                # Verify it's an artwork type AND has matching creator
                # P31 = instance of, P170 = creator
                # artwork types: Q3305213 (painting), Q4502142 (visual artwork),
                #                Q838948 (work of art), Q18573970 (pictorial artwork), Q93184 (drawing)
                if artist_name:
                    # Query with artist verification
                    normalized_artist = self._normalize_artist_name(artist_name).lower()
                    query = f"""
                    SELECT ?type ?creatorLabel WHERE {{
                      wd:{entity_id} wdt:P31 ?type .
                      VALUES ?type {{ wd:Q3305213 wd:Q4502142 wd:Q838948 wd:Q18573970 wd:Q93184 }}
                      OPTIONAL {{ wd:{entity_id} wdt:P170 ?creator . }}
                      SERVICE wikibase:label {{ bd:serviceParam wikibase:language "en". }}
                    }}
                    LIMIT 5
                    """
                else:
                    # No artist to verify, just check artwork type
                    query = f"""
                    SELECT ?type WHERE {{
                      wd:{entity_id} wdt:P31 ?type .
                      VALUES ?type {{ wd:Q3305213 wd:Q4502142 wd:Q838948 wd:Q18573970 wd:Q93184 }}
                    }}
                    LIMIT 1
                    """

                sparql = SPARQLWrapper(WIKIDATA_ENDPOINT)
                sparql.setQuery(query)
                sparql.setReturnFormat(JSON)
                sparql.setTimeout(5)
                sparql.addCustomHttpHeader(
                    "User-Agent", "EuropeanaHeritageParser/1.0 (ArP Project)"
                )

                time.sleep(0.3)
                results = sparql.query().convert()
                bindings = results.get("results", {}).get("bindings", [])

                if bindings:
                    # If we have an artist to verify, check if creator matches
                    if artist_name:
                        creator_found = False
                        for binding in bindings:
                            creator_label = (
                                binding.get("creatorLabel", {}).get("value", "").lower()
                            )
                            if creator_label and (
                                normalized_artist in creator_label
                                or creator_label in normalized_artist
                                or
                                # Handle last name match for "Surname, FirstName" format
                                any(
                                    part in creator_label
                                    for part in normalized_artist.split()
                                    if len(part) > 3
                                )
                            ):
                                creator_found = True
                                break

                        if creator_found:
                            result["wikidata_uri"] = (
                                f"http://www.wikidata.org/entity/{entity_id}"
                            )
                            # Fetch dimensions for this artwork
                            result["dimensions"] = self._fetch_wikidata_dimensions(
                                entity_id
                            )
                            return result
                        else:
                            # Artist doesn't match, continue searching
                            continue
                    else:
                        # No artist to verify, accept the match
                        result["wikidata_uri"] = (
                            f"http://www.wikidata.org/entity/{entity_id}"
                        )
                        # Fetch dimensions for this artwork
                        result["dimensions"] = self._fetch_wikidata_dimensions(
                            entity_id
                        )
                        return result

            self._log_warning(
                f"Wikidata: No artwork found for '{title[:40]}...' by '{artist_name or 'unknown'}'"
            )

        except Exception as e:
            self._log_warning(f"Wikidata artwork query failed for '{title[:40]}': {e}")

        return result

    def _fetch_wikidata_dimensions(self, entity_id: str) -> Optional[str]:
        """Fetch dimensions for an artwork from Wikidata.

        Uses P2048 (height) and P2049 (width) properties.

        Args:
            entity_id: Wikidata entity ID (e.g., "Q12345")

        Returns:
            Formatted dimensions string like "123 × 456 cm" or None
        """
        try:
            # P2048 = height, P2049 = width - use simple direct property access
            query = f"""
            SELECT ?height ?width WHERE {{
              OPTIONAL {{ wd:{entity_id} wdt:P2048 ?height . }}
              OPTIONAL {{ wd:{entity_id} wdt:P2049 ?width . }}
            }}
            LIMIT 1
            """

            sparql = SPARQLWrapper(WIKIDATA_ENDPOINT)
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            sparql.setTimeout(5)
            sparql.addCustomHttpHeader(
                "User-Agent", "EuropeanaHeritageParser/1.0 (ArP Project)"
            )

            time.sleep(0.2)
            results = sparql.query().convert()
            bindings = results.get("results", {}).get("bindings", [])

            if bindings:
                binding = bindings[0]
                height = binding.get("height", {}).get("value")
                width = binding.get("width", {}).get("value")

                if height or width:
                    # Format dimensions - height x width
                    height_str = None
                    width_str = None

                    if height:
                        try:
                            h = float(height)
                            height_str = f"{h:.1f}" if h != int(h) else str(int(h))
                        except ValueError:
                            height_str = height

                    if width:
                        try:
                            w = float(width)
                            width_str = f"{w:.1f}" if w != int(w) else str(int(w))
                        except ValueError:
                            width_str = width

                    if height_str and width_str:
                        return f"{height_str} × {width_str} cm"
                    elif height_str:
                        return f"h: {height_str} cm"
                    elif width_str:
                        return f"w: {width_str} cm"

        except Exception as e:
            self._log_warning(
                f"Failed to fetch Wikidata dimensions for {entity_id}: {e}"
            )

        return None

    def _query_dbpedia_artist(self, artist_name: str) -> Dict[str, Any]:
        """Query DBpedia for artist information."""
        result = {
            "dbpedia_uri": None,
            "birth_date": None,
            "death_date": None,
            "nationality": None,
        }

        # Sanitize for DBpedia URI
        sanitized_name = re.sub(r"\s*\([^)]*\)\s*", " ", artist_name)
        sanitized_name = re.sub(r"[^\w\s-]", "", sanitized_name)
        sanitized_name = re.sub(r"\s+", " ", sanitized_name).strip()

        if not sanitized_name:
            return result

        dbpedia_name = sanitized_name.replace(" ", "_")

        query = f"""
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX dbr: <http://dbpedia.org/resource/>
        
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
            sparql.addCustomHttpHeader("User-Agent", "EuropeanaHeritageParser/1.0")

            time.sleep(self._query_delay)

            results = sparql.query().convert()
            bindings = results.get("results", {}).get("bindings", [])

            if bindings:
                binding = bindings[0]
                result["dbpedia_uri"] = binding.get("artist", {}).get("value")
                result["birth_date"] = self._extract_date(
                    binding.get("birthDate", {}).get("value")
                )
                result["death_date"] = self._extract_date(
                    binding.get("deathDate", {}).get("value")
                )
                nat = binding.get("nationality", {}).get("value")
                if nat:
                    result["nationality"] = nat.split("/")[-1].replace("_", " ")
            else:
                self._log_warning(f"DBpedia: No artist found for '{artist_name}'")

        except (SPARQLWrapperException, urllib.error.URLError) as e:
            self._log_warning(f"DBpedia artist query failed for '{artist_name}': {e}")

        return result

    def _query_dbpedia_artwork(
        self, title: str, artist_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """Query DBpedia for artwork information with artist verification."""
        result = {"dbpedia_uri": None}

        safe_title = title.replace('"', '\\"').replace("'", "\\'")

        # Build artist constraint - REQUIRE match if artist name provided
        artist_clause = ""
        if artist_name:
            normalized_artist = self._normalize_artist_name(artist_name)
            safe_artist = normalized_artist.replace('"', '\\"').replace("'", "\\'")

            artist_clause = f"""
          ?artwork dbo:author ?author .
          ?author rdfs:label ?authorLabel .
          FILTER(LANG(?authorLabel) = "en")
          FILTER(CONTAINS(LCASE(?authorLabel), LCASE("{safe_artist}")) || 
                 CONTAINS(LCASE("{safe_artist}"), LCASE(?authorLabel)))
            """

        query = f"""
        PREFIX dbo: <http://dbpedia.org/ontology/>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
        
        SELECT ?artwork ?authorLabel WHERE {{
          ?artwork a dbo:Artwork .
          ?artwork rdfs:label ?label .
          FILTER(LANG(?label) = "en")
          FILTER(CONTAINS(LCASE(?label), LCASE("{safe_title}")))
          {artist_clause}
        }}
        LIMIT 5
        """

        try:
            sparql = SPARQLWrapper(DBPEDIA_ENDPOINT)
            sparql.setQuery(query)
            sparql.setReturnFormat(JSON)
            sparql.addCustomHttpHeader("User-Agent", "EuropeanaHeritageParser/1.0")

            time.sleep(self._query_delay)

            results = sparql.query().convert()
            bindings = results.get("results", {}).get("bindings", [])

            if bindings:
                # If we have artist name, verify match
                if artist_name:
                    normalized_artist = self._normalize_artist_name(artist_name).lower()
                    for binding in bindings:
                        author_label = (
                            binding.get("authorLabel", {}).get("value", "").lower()
                        )
                        if author_label and (
                            normalized_artist in author_label
                            or author_label in normalized_artist
                            or any(
                                part in author_label
                                for part in normalized_artist.split()
                                if len(part) > 3
                            )
                        ):
                            result["dbpedia_uri"] = binding.get("artwork", {}).get(
                                "value"
                            )
                            return result
                    self._log_warning(
                        f"DBpedia: No artwork found for '{title[:40]}...' by '{artist_name}'"
                    )
                else:
                    result["dbpedia_uri"] = bindings[0].get("artwork", {}).get("value")
            else:
                self._log_warning(f"DBpedia: No artwork found for '{title[:40]}...'")

        except (SPARQLWrapperException, urllib.error.URLError) as e:
            self._log_warning(f"DBpedia artwork query failed for '{title[:40]}': {e}")

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
            artist_enrichment: Enriched artist data
            artwork_enrichment: Enriched artwork data
            getty_aat_uris: Getty AAT concept URIs

        Returns:
            URIRef of the artwork
        """
        artwork_uri = self._create_artwork_uri(artwork["id"])

        # Type declarations
        self.graph.add((artwork_uri, RDF.type, ARP.Artwork))
        self.graph.add((artwork_uri, RDF.type, SCHEMA.VisualArtwork))

        # Add painting type if applicable
        obj_type = artwork.get("object_type", "")
        if obj_type:
            obj_type_lower = obj_type.lower() if isinstance(obj_type, str) else ""
            if "paint" in obj_type_lower or "image" in obj_type_lower:
                self.graph.add((artwork_uri, RDF.type, SCHEMA.Painting))

        # Title
        if artwork.get("title"):
            self.graph.add(
                (
                    artwork_uri,
                    DC.title,
                    Literal(artwork["title"], lang=artwork.get("title_lang", "en")),
                )
            )

        # Description - use tracked language
        if artwork.get("description"):
            desc_lang = artwork.get("description_lang", "en") or "en"
            self.graph.add(
                (
                    artwork_uri,
                    DC.description,
                    Literal(artwork["description"], lang=desc_lang),
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

        # Object type as style
        if artwork.get("object_type"):
            obj_type_str = artwork["object_type"]
            if isinstance(obj_type_str, str):
                self.graph.add((artwork_uri, ARP.artworkStyle, Literal(obj_type_str)))

        # Getty AAT links and other medium/type concepts
        # Combine mapped Getty URIs with extracted concepts
        all_media_uris = set(getty_aat_uris)
        if artwork.get("media_concepts"):
            all_media_uris.update(artwork["media_concepts"])

        for uri in all_media_uris:
            self.graph.add((artwork_uri, SCHEMA.artMedium, URIRef(uri)))
            self.graph.add((artwork_uri, DCTERMS.type, URIRef(uri)))
            self.graph.add((artwork_uri, DCTERMS.medium, URIRef(uri)))

        # Description concepts (often Subject/Topic)
        if artwork.get("description_concepts"):
            for uri in artwork["description_concepts"]:
                self.graph.add((artwork_uri, DC.subject, URIRef(uri)))
                self.graph.add((artwork_uri, DCTERMS.subject, URIRef(uri)))

        # Creator concepts (as contributors)
        if artwork.get("creator_concepts"):
            for uri in artwork["creator_concepts"]:
                self.graph.add((artwork_uri, DCTERMS.contributor, URIRef(uri)))

        # Artwork external links
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
            location_uri = self._add_location(
                artwork["repository"], artwork.get("country")
            )
            owner_uri = self._add_owner(artwork["repository"], location_uri)

            self.graph.add((artwork_uri, ARP.currentLocation, location_uri))
            self.graph.add((artwork_uri, ARP.currentOwner, owner_uri))

        # Build provenance chain
        self._add_provenance_chain(artwork, artwork_uri)

        return artwork_uri

    def _create_artwork_uri(self, artwork_id: str) -> URIRef:
        """Create a URI for an artwork."""
        safe_id = self._slugify(artwork_id)
        return ARP[f"artwork_{safe_id}"]

    def _add_artist(self, artist_name: str, enrichment: Dict[str, Any]) -> URIRef:
        """Add an artist to the graph."""
        cache_key = artist_name.lower().strip()

        if cache_key in self._artists:
            return self._artists[cache_key]

        normalized_name = DataEnricher._normalize_artist_name(artist_name)
        artist_uri = ARP[f"artist_{self._slugify(normalized_name)}"]
        self._artists[cache_key] = artist_uri

        self.graph.add((artist_uri, RDF.type, ARP.Artist))
        self.graph.add((artist_uri, SCHEMA.name, Literal(normalized_name, lang="en")))

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

        if enrichment.get("wikidata_uri"):
            self.graph.add((artist_uri, OWL.sameAs, URIRef(enrichment["wikidata_uri"])))

        if enrichment.get("dbpedia_uri"):
            self.graph.add((artist_uri, OWL.sameAs, URIRef(enrichment["dbpedia_uri"])))

        return artist_uri

    def _add_location(
        self, repository_name: str, country: Optional[str] = None
    ) -> URIRef:
        """Add a location (museum) to the graph."""
        cache_key = repository_name.lower().strip()

        if cache_key in self._locations:
            return self._locations[cache_key]

        location_uri = ARP[f"location_{self._slugify(repository_name)}"]
        self._locations[cache_key] = location_uri

        self.graph.add((location_uri, RDF.type, ARP.Location))
        self.graph.add((location_uri, RDF.type, SCHEMA.Museum))
        self.graph.add((location_uri, SCHEMA.name, Literal(repository_name, lang="en")))

        if country:
            self.graph.add((location_uri, SCHEMA.address, Literal(country)))

        return location_uri

    def _add_owner(self, repository_name: str, location_uri: URIRef) -> URIRef:
        """Add an owner (organization) to the graph."""
        cache_key = repository_name.lower().strip()

        if cache_key in self._owners:
            return self._owners[cache_key]

        owner_uri = ARP[f"owner_{self._slugify(repository_name)}"]
        self._owners[cache_key] = owner_uri

        self.graph.add((owner_uri, RDF.type, ARP.OrganizationOwner))
        self.graph.add((owner_uri, SCHEMA.name, Literal(repository_name, lang="en")))
        self.graph.add((owner_uri, ARP.ownerLocation, location_uri))

        return owner_uri

    def _add_provenance_chain(
        self, artwork: Dict[str, Any], artwork_uri: URIRef
    ) -> List[URIRef]:
        """Build a provenance chain for the artwork with richer data."""
        events = []
        event_order = 1

        # Creation event
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

        # Add creation date with better parsing
        creation_date_str = None
        if artwork.get("creation_date"):
            date_str = str(artwork["creation_date"])
            # Try to extract full date or year
            year_match = re.match(r"(\d{4})", date_str)
            if year_match:
                creation_date_str = year_match.group(1)
                self.graph.add(
                    (
                        creation_uri,
                        PROV.startedAtTime,
                        Literal(f"{year_match.group(1)}-01-01", datatype=XSD.date),
                    )
                )

        # Try to get more specific dates from time spans
        time_spans = artwork.get("time_spans", [])
        time_span_labels = artwork.get("time_span_labels", [])

        period_desc = None
        if time_spans and not creation_date_str:
            # Try to extract date from time span URIs (often contain years)
            for ts in time_spans:
                if isinstance(ts, str):
                    year_match = re.search(r"/(\d{4})$", ts)
                    if year_match:
                        creation_date_str = year_match.group(1)
                        self.graph.add(
                            (
                                creation_uri,
                                PROV.startedAtTime,
                                Literal(
                                    f"{year_match.group(1)}-01-01", datatype=XSD.date
                                ),
                            )
                        )
                        break

        # Get time period description from time span labels (don't add separately)
        if time_span_labels:
            for label in time_span_labels:
                if isinstance(label, dict):
                    period_desc = (
                        label.get("def") or label.get("en") or list(label.values())[0]
                        if label
                        else None
                    )
                elif isinstance(label, str):
                    period_desc = label
                else:
                    period_desc = None

                if period_desc:
                    break

        # Link artist if available
        if artwork.get("creator"):
            normalized_name = DataEnricher._normalize_artist_name(artwork["creator"])
            artist_uri = ARP[f"artist_{self._slugify(normalized_name)}"]
            self.graph.add((creation_uri, ARP.toOwner, artist_uri))

        # Build a SINGLE comprehensive creation description
        desc_parts = []
        if artwork.get("creator"):
            desc_parts.append(f"Created by {artwork['creator']}")
        if creation_date_str:
            desc_parts.append(f"in {creation_date_str}")
        if period_desc and period_desc not in [
            "Second millenium AD",
            "Second millennium AD",
        ]:
            # Only add period if it's specific (not generic like "Second millennium")
            desc_parts.append(f"({period_desc})")

        if desc_parts:
            self.graph.add(
                (
                    creation_uri,
                    DC.description,
                    Literal(" ".join(desc_parts), lang="en"),
                )
            )

        events.append(creation_uri)
        event_order += 1

        # Acquisition by current repository
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

            owner_uri = ARP[f"owner_{self._slugify(artwork['repository'])}"]
            self.graph.add((acquisition_uri, ARP.toOwner, owner_uri))

            location_uri = ARP[f"location_{self._slugify(artwork['repository'])}"]
            self.graph.add((acquisition_uri, ARP.eventLocation, location_uri))

            # Build a more detailed acquisition description
            country = artwork.get("country", "")
            if country:
                self.graph.add(
                    (
                        acquisition_uri,
                        DC.description,
                        Literal(
                            f"Acquired by {artwork['repository']}, {country}", lang="en"
                        ),
                    )
                )
            else:
                self.graph.add(
                    (
                        acquisition_uri,
                        DC.description,
                        Literal(f"Acquired by {artwork['repository']}", lang="en"),
                    )
                )

            events.append(acquisition_uri)
            event_order += 1

        # Add provenance history from Europeana if available
        if artwork.get("provenance_text"):
            history_uri = ARP[f"prov_{artwork['id']}_history"]
            self.graph.add((history_uri, RDF.type, ARP.ProvenanceEvent))
            self.graph.add((history_uri, ARP.eventType, Literal("Provenance History")))
            self.graph.add(
                (
                    history_uri,
                    ARP.provenanceOrder,
                    Literal(event_order, datatype=XSD.integer),
                )
            )
            self.graph.add((artwork_uri, ARP.hasProvenanceEvent, history_uri))
            self.graph.add(
                (
                    history_uri,
                    DC.description,
                    Literal(artwork["provenance_text"], lang="en"),
                )
            )
            # Mark source as Europeana/museum record
            self.graph.add(
                (
                    history_uri,
                    ARP.sourceUri,
                    Literal(artwork.get("record_url", "")),
                )
            )
            events.append(history_uri)

        return events

    def _parse_creation_date(self, date_str: str) -> Optional[Literal]:
        """Parse creation date string into appropriate RDF literal."""
        if not date_str:
            return None

        date_str = str(date_str)

        # Handle date ranges
        range_match = re.match(r"(\d{4})\s*[-–]\s*(\d{4})", date_str)
        if range_match:
            return Literal(range_match.group(1), datatype=XSD.gYear)

        # Handle single year
        year_match = re.match(r"(\d{4})", date_str)
        if year_match:
            return Literal(year_match.group(1), datatype=XSD.gYear)

        return Literal(date_str)

    @staticmethod
    def _slugify(text: str) -> str:
        """Convert text to URL-safe slug."""
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
            "ä": "a",
            "ö": "o",
            "ü": "u",
            "ß": "ss",
            "é": "e",
            "è": "e",
            "ê": "e",
            "ë": "e",
            "à": "a",
            "á": "a",
            "ñ": "n",
            "ø": "o",
        }
        for old, new in replacements.items():
            text = text.replace(old, new)

        text = re.sub(r"[^a-zA-Z0-9]+", "_", text.lower())
        text = re.sub(r"_+", "_", text)
        text = text.strip("_")

        return text

    def serialize(self, output_format: str = "turtle") -> str:
        """Serialize the graph to string."""
        return self.graph.serialize(format=output_format)

    def save(self, path: Path, output_format: str = "turtle") -> None:
        """Save the graph to file."""
        self.graph.serialize(destination=str(path), format=output_format)


# =============================================================================
# MAIN CONVERTER CLASS
# =============================================================================


class EuropeanaHeritageConverter:
    """Main converter orchestrating the API fetch to TTL conversion."""

    BATCH_SIZE = 5

    def __init__(
        self,
        api_key: str,
        output_dir: Path,
        query: str = "painting",
        provider: Optional[str] = None,
        country: Optional[str] = None,
        artwork_count: Optional[int] = None,
        enable_enrichment: bool = True,
        verbose: bool = True,
        debug: bool = False,
    ):
        self.api_key = api_key
        self.output_dir = output_dir
        self.query = query
        self.provider = provider
        self.country = country
        self.artwork_count = artwork_count
        self.enable_enrichment = enable_enrichment
        self.verbose = verbose
        self.debug = debug

        self.client = EuropeanaClient(api_key)
        self.cache = ArtistCache()
        self.enricher = (
            DataEnricher(self.cache, verbose=verbose) if enable_enrichment else None
        )
        self.rdf_generator = RDFGenerator()
        self.output_path: Optional[Path] = None

        self._stats = {
            "artworks_processed": 0,
            "artists_enriched_wikidata": 0,
            "artists_enriched_dbpedia": 0,
            "artists_not_found": 0,
            "artworks_enriched_wikidata": 0,
            "artworks_enriched_dbpedia": 0,
            "artworks_not_found": 0,
            "getty_aat_linked": 0,
            "getty_aat_not_found": 0,
        }

    def convert(self) -> Path:
        """
        Run the conversion process.

        Returns:
            Path to the generated TTL file
        """
        print(f"Searching Europeana for: {self.query}")
        if self.provider:
            print(f"Filtering by provider: {self.provider}")
        if self.country:
            print(f"Filtering by country: {self.country}")

        # Fetch artworks from Europeana
        items = self.client.search_artworks(
            query=self.query,
            provider=self.provider,
            country=self.country,
            limit=self.artwork_count,
        )
        print(f"Found {len(items)} artworks")

        if not items:
            print("No artworks found. Exiting.")
            sys.exit(1)

        # Generate output filename
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        output_filename = f"europeana_data_{timestamp}.ttl"
        self.output_path = self.output_dir / output_filename

        # Ensure output directory exists
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Write TTL prefixes
        self._write_prefixes()

        processed_count = 0
        parsed_artworks_debug = []  # For debug JSON output

        try:
            # Debug: save all raw items to JSON file
            if self.debug:
                debug_dir = self.output_dir / "debug"
                debug_dir.mkdir(parents=True, exist_ok=True)
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")

                # Save raw Europeana API responses
                raw_json_path = debug_dir / f"europeana_raw_{timestamp}.json"
                with open(raw_json_path, "w", encoding="utf-8") as f:
                    json.dump(items, f, indent=2, ensure_ascii=False)
                print(f"\n✓ Debug: Raw Europeana items saved to: {raw_json_path}\n")

            for i, item in enumerate(items, 1):
                # Debug: show raw Europeana fields for first item
                if self.debug and i == 1:
                    print("\n=== DEBUG: Raw Europeana item fields ===")
                    debug_fields = [
                        "dcCreator",
                        "dcCreatorLangAware",
                        "dcContributor",
                        "dcContributorLangAware",
                        "edmAgentLabelLangAware",
                        "dcDescriptionLangAware",
                        "dctermsExtent",
                        "dcFormat",
                        "edmTimespan",
                        "edmTimespanLabel",
                    ]
                    for field in debug_fields:
                        if field in item:
                            print(f"  {field}: {item[field]}")
                    print("  All keys:", sorted(item.keys()))
                    print("=== END DEBUG ===\n")

                # Parse the search result
                artwork = EuropeanaParser.parse_search_item(item)

                if not artwork.get("title"):
                    print(f"  Skipping item {i} - no title")
                    continue

                title = artwork.get("title", "Unknown")[:50]
                print(f"Processing artwork {i}/{len(items)}: {title}")

                # Fetch full record from Record API for richer metadata
                europeana_id = artwork.get("europeana_id")
                if europeana_id:
                    print("  Fetching full record...")
                    full_record = self.client.get_record(europeana_id)
                    if full_record:
                        artwork = EuropeanaParser.parse_full_record(
                            full_record, artwork
                        )
                        print("    ✓ Full record retrieved")
                        if artwork.get("provenance_text"):
                            print(
                                f"    ✓ Provenance found: {artwork['provenance_text'][:60]}..."
                            )
                        if artwork.get("dimensions"):
                            print(
                                f"    ✓ Dimensions from Europeana: {artwork['dimensions']}"
                            )
                        if self.debug and full_record:
                            # Save full record to debug
                            debug_dir = self.output_dir / "debug"
                            record_file = (
                                debug_dir / f"record_{i}_{artwork['id'][:30]}.json"
                            )
                            with open(record_file, "w", encoding="utf-8") as f:
                                json.dump(full_record, f, indent=2, ensure_ascii=False)
                    else:
                        print("    ⚠ Could not fetch full record")

                # Debug: show parsed fields
                if self.debug:
                    print(f"  Dimensions: {artwork.get('dimensions')}")
                    print(
                        f"  Description ({artwork.get('description_lang', 'unknown')}): {(artwork.get('description') or '')[:80]}..."
                    )

                artist_enrichment = {}
                artwork_enrichment = {}
                getty_aat_uris = []

                if self.enable_enrichment and self.enricher:
                    # Getty AAT mapping (name-based)
                    getty_aat_uris = self.enricher.get_getty_aat_uris(artwork)

                    # Merge with Getty AAT URIs extracted directly from Europeana
                    extracted_aat = artwork.get("getty_aat_from_europeana", [])
                    if extracted_aat:
                        # Convert to list if it's not already
                        if isinstance(extracted_aat, set):
                            extracted_aat = list(extracted_aat)

                        # Add unique URIs
                        for uri in extracted_aat:
                            if uri not in getty_aat_uris:
                                getty_aat_uris.append(uri)

                    if getty_aat_uris:
                        print(f"  ✓ Getty AAT: {len(getty_aat_uris)} concept(s) linked")
                        self._stats["getty_aat_linked"] += 1
                    else:
                        self._stats["getty_aat_not_found"] += 1

                    # Artist enrichment
                    creator_name = artwork.get("creator")
                    resolved_name = artwork.get("artist_name_resolved")

                    # Use resolved name if available (often better formatted)
                    artist_name_to_use = resolved_name or creator_name

                    if artist_name_to_use:
                        print(f"  Enriching artist: {artist_name_to_use}")

                        # Pre-fill enrichment with data found in Europeana
                        artist_enrichment = {}
                        if artwork.get("artist_wikidata_from_europeana"):
                            artist_enrichment["wikidata_uri"] = artwork[
                                "artist_wikidata_from_europeana"
                            ]
                        if artwork.get("artist_dbpedia_from_europeana"):
                            artist_enrichment["dbpedia_uri"] = artwork[
                                "artist_dbpedia_from_europeana"
                            ]

                        # If we already have links, we might still want to fetch details (birth/death),
                        # or we can trust the enrichment service to handle it if we pass the known URIs.
                        # For now, let's call enrich_artist. simpler logic: if we have links, verify/fetch details.
                        # But enricher.enrich_artist mainly searches by name.

                        # Let's run standard enrichment first
                        enriched_data = self.enricher.enrich_artist(artist_name_to_use)

                        # Merge/Prioritize Europeana found links (they are likely more accurate for the specific record)
                        if artwork.get("artist_wikidata_from_europeana"):
                            enriched_data["wikidata_uri"] = artwork[
                                "artist_wikidata_from_europeana"
                            ]
                        if artwork.get("artist_dbpedia_from_europeana"):
                            enriched_data["dbpedia_uri"] = artwork[
                                "artist_dbpedia_from_europeana"
                            ]

                        artist_enrichment = enriched_data

                        has_artist_link = False
                        if artist_enrichment.get("wikidata_uri"):
                            print(
                                f"    ✓ Wikidata: {artist_enrichment['wikidata_uri']}"
                            )
                            self._stats["artists_enriched_wikidata"] += 1
                            has_artist_link = True
                        if artist_enrichment.get("dbpedia_uri"):
                            print(f"    ✓ DBpedia: {artist_enrichment['dbpedia_uri']}")
                            self._stats["artists_enriched_dbpedia"] += 1
                            has_artist_link = True
                        if not has_artist_link:
                            self._stats["artists_not_found"] += 1
                    else:
                        print("  ⚠ No creator/artist found in Europeana record")

                    # Artwork enrichment
                    artwork_enrichment = self.enricher.enrich_artwork(
                        artwork.get("title", ""), artwork.get("creator")
                    )
                    has_artwork_link = False
                    if artwork_enrichment.get("wikidata_uri"):
                        print(
                            f"  ✓ Artwork Wikidata: {artwork_enrichment['wikidata_uri']}"
                        )
                        self._stats["artworks_enriched_wikidata"] += 1
                        has_artwork_link = True

                        # Use Wikidata dimensions if not already set from Europeana
                        if artwork_enrichment.get("dimensions") and not artwork.get(
                            "dimensions"
                        ):
                            artwork["dimensions"] = artwork_enrichment["dimensions"]
                            print(
                                f"    ✓ Dimensions from Wikidata: {artwork['dimensions']}"
                            )
                    if artwork_enrichment.get("dbpedia_uri"):
                        print(
                            f"  ✓ Artwork DBpedia: {artwork_enrichment['dbpedia_uri']}"
                        )
                        self._stats["artworks_enriched_dbpedia"] += 1
                        has_artwork_link = True
                    if not has_artwork_link:
                        self._stats["artworks_not_found"] += 1
                else:
                    # Offline Getty AAT mapping
                    getty_aat_uris = self._get_getty_aat_offline(artwork)

                # Add to RDF graph
                self.rdf_generator.add_artwork(
                    artwork, artist_enrichment, artwork_enrichment, getty_aat_uris
                )
                processed_count += 1
                self._stats["artworks_processed"] = processed_count

                # Collect for debug output
                if self.debug:
                    parsed_artworks_debug.append(artwork)

                # Incremental save
                if processed_count % self.BATCH_SIZE == 0:
                    self._append_graph_to_file()
                    print(f"  [Saved batch - {processed_count} artworks to disk]")

        finally:
            # Final save
            if len(self.rdf_generator.graph) > 0:
                self._append_graph_to_file()
                print("  [Final save - ensuring all data is written to disk]")

            # Debug: save parsed artworks to JSON
            if self.debug and parsed_artworks_debug:
                debug_dir = self.output_dir / "debug"
                timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
                parsed_json_path = debug_dir / f"europeana_parsed_{timestamp}.json"
                with open(parsed_json_path, "w", encoding="utf-8") as f:
                    json.dump(parsed_artworks_debug, f, indent=2, ensure_ascii=False)
                print(f"✓ Debug: Parsed artworks saved to: {parsed_json_path}")

        self._print_enrichment_summary()

        print(f"\nOutput saved to: {self.output_path}")
        return self.output_path

    def _print_enrichment_summary(self) -> None:
        """Print enrichment results summary."""
        stats = self._stats
        total = stats["artworks_processed"]

        print("\n" + "=" * 60)
        print("ENRICHMENT SUMMARY")
        print("=" * 60)
        print(f"Total artworks processed: {total}")

        if self.enable_enrichment:
            print("\n📊 Artist Enrichment:")
            wd_artists = stats["artists_enriched_wikidata"]
            db_artists = stats["artists_enriched_dbpedia"]
            no_artists = stats["artists_not_found"]
            print(f"  ✓ Wikidata links found: {wd_artists}")
            print(f"  ✓ DBpedia links found:  {db_artists}")
            if no_artists > 0:
                print(f"  ✗ Artists not found:    {no_artists}")

            print("\n📊 Artwork Enrichment:")
            wd_artworks = stats["artworks_enriched_wikidata"]
            db_artworks = stats["artworks_enriched_dbpedia"]
            no_artworks = stats["artworks_not_found"]
            print(f"  ✓ Wikidata links found: {wd_artworks}")
            print(f"  ✓ DBpedia links found:  {db_artworks}")
            if no_artworks > 0:
                print(f"  ✗ Artworks not found:   {no_artworks}")

            print("\n📊 Getty AAT Vocabulary:")
            aat_linked = stats["getty_aat_linked"]
            aat_not_found = stats["getty_aat_not_found"]
            print(f"  ✓ Artworks with AAT links: {aat_linked}")
            if aat_not_found > 0:
                print(f"  ✗ No AAT mappings found:   {aat_not_found}")

            if total > 0:
                print("\n📈 Success Rates:")
                artist_total = wd_artists + db_artists + no_artists
                artwork_total = wd_artworks + db_artworks + no_artworks
                aat_total = aat_linked + aat_not_found

                if artist_total > 0:
                    artist_rate = (wd_artists + db_artists) / artist_total * 100
                    print(f"  Artist enrichment:  {artist_rate:.1f}%")
                if artwork_total > 0:
                    artwork_rate = (wd_artworks + db_artworks) / artwork_total * 100
                    print(f"  Artwork enrichment: {artwork_rate:.1f}%")
                if aat_total > 0:
                    aat_rate = aat_linked / aat_total * 100
                    print(f"  Getty AAT mapping:  {aat_rate:.1f}%")

        print("=" * 60)

    def _write_prefixes(self) -> None:
        """Write TTL prefixes to the output file."""
        prefixes = f"""@prefix arp: <http://example.org/arp#> .
@prefix aat: <http://vocab.getty.edu/aat/> .
@prefix crm: <http://www.cidoc-crm.org/cidoc-crm/> .
@prefix dbr: <http://dbpedia.org/resource/> .
@prefix dc: <http://purl.org/dc/elements/1.1/> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix prov: <http://www.w3.org/ns/prov#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix schema: <http://schema.org/> .
@prefix wd: <http://www.wikidata.org/entity/> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

# Europeana Heritage Data - Generated by europeana_heritage_parser.py
# Source: Europeana API (https://api.europeana.eu)
# Timestamp: {datetime.now().isoformat()}

"""
        with open(self.output_path, "w", encoding="utf-8") as f:
            f.write(prefixes)

    def _append_graph_to_file(self) -> None:
        """Append current graph triples to file and clear the graph."""
        if not self.output_path or len(self.rdf_generator.graph) == 0:
            return

        ttl_content = self.rdf_generator.graph.serialize(format="turtle")

        # Fix namespace prefix renaming
        ttl_content = ttl_content.replace("schema1:", "schema:")

        # Remove prefix declarations
        lines = ttl_content.split("\n")
        content_lines = []
        in_prefix_section = True
        for line in lines:
            if in_prefix_section and (line.startswith("@prefix") or line.strip() == ""):
                continue
            in_prefix_section = False
            content_lines.append(line)

        content = "\n".join(content_lines)

        with open(self.output_path, "a", encoding="utf-8") as f:
            f.write(content)
            f.write("\n\n")

        # Clear graph for next batch
        self.rdf_generator = RDFGenerator()

    @staticmethod
    def _get_getty_aat_offline(artwork: Dict[str, Any]) -> List[str]:
        """Get Getty AAT URIs using local mapping."""
        aat_uris = []

        if artwork.get("object_type"):
            obj_type = str(artwork["object_type"]).lower()
            for key, uri in GETTY_AAT_MAPPINGS.items():
                if key in obj_type:
                    aat_uris.append(uri)
                    break

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
        description="Convert Europeana artworks to ArP ontology TTL",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --count 10 --api-key YOUR_KEY
  %(prog)s --count 50 --query "paintings"
  %(prog)s --all --provider "Rijksmuseum"
  %(prog)s --count 100 --query "portrait" --output-dir ./output
  %(prog)s --count 10 --no-enrichment

Environment Variables:
  EUROPEANA_API_KEY    API key for Europeana (alternative to --api-key)
                       Can be set in .env file in scripts/ or project root

Get your API key at: https://apis.europeana.eu/
        """,
    )

    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument(
        "--count", "-c", type=int, metavar="N", help="Number of artworks to fetch"
    )
    group.add_argument(
        "--all",
        "-a",
        action="store_true",
        help="Fetch all matching artworks (use with caution)",
    )

    parser.add_argument(
        "--api-key",
        "-k",
        type=str,
        default=os.environ.get("EUROPEANA_API_KEY"),
        help="Europeana API key (or set EUROPEANA_API_KEY env var)",
    )

    parser.add_argument(
        "--query",
        "-q",
        type=str,
        default="what:(painting OR portrait OR landscape)",
        help="Search query (default: 'what:(painting OR portrait OR landscape)'). "
        "Examples: 'Rembrandt', 'what:sculpture', 'where:Paris'",
    )

    parser.add_argument(
        "--provider",
        "-p",
        type=str,
        default=None,
        help="Filter by data provider (e.g., 'Rijksmuseum', 'Louvre')",
    )

    parser.add_argument(
        "--country",
        type=str,
        default=None,
        help="Filter by country (e.g., 'Romania', 'Netherlands', 'France')",
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

    parser.add_argument(
        "--debug",
        action="store_true",
        help="Show debug info (raw Europeana fields for first item)",
    )

    return parser.parse_args()


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================


def main() -> int:
    """Main entry point."""
    # Load environment variables from .env file
    # Look for .env in script directory, then project root
    script_dir = Path(__file__).parent
    project_root = script_dir.parent

    # Try loading from multiple locations
    for env_path in [script_dir / ".env", project_root / ".env"]:
        if env_path.exists():
            load_dotenv(env_path)
            break
    else:
        # Fallback: load from current directory or default locations
        load_dotenv()

    args = parse_arguments()

    # Validate API key (now includes .env loaded values)
    if not args.api_key:
        print(
            "Error: Europeana API key required. Use --api-key or set EUROPEANA_API_KEY.",
            file=sys.stderr,
        )
        print("Get your API key at: https://apis.europeana.eu/", file=sys.stderr)
        return 1

    # Determine artwork count
    artwork_count = None if args.all else args.count

    try:
        converter = EuropeanaHeritageConverter(
            api_key=args.api_key,
            output_dir=args.output_dir,
            query=args.query,
            provider=args.provider,
            country=args.country,
            artwork_count=artwork_count,
            enable_enrichment=not args.no_enrichment,
            debug=args.debug,
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
