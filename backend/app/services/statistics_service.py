"""Statistics service for Getty-based artwork analytics."""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..models.statistics import (
    GettyMaterialStat,
    MaterialDistribution,
    HierarchyStat,
    MaterialHierarchyResponse,
    PeriodMaterialStat,
    TemporalTrend,
    TemporalTrendsResponse,
    CrossAnalysisCell,
    CrossAnalysisResponse,
    StatisticsQueryResponse,
)
from .sparql_service import sparql_service
from .external_sparql_service import external_sparql_service

logger = logging.getLogger(__name__)

# Namespace constants
ARP_NS = "http://example.org/arp#"
SCHEMA_NS = "http://schema.org/"
AAT_NS = "http://vocab.getty.edu/aat/"
SKOS_NS = "http://www.w3.org/2004/02/skos/core#"
GVP_NS = "http://vocab.getty.edu/ontology#"


class StatisticsService:
    """Service for generating Getty-based artwork statistics."""

    # Getty-related SPARQL prefixes to auto-inject
    GETTY_PREFIXES = """
        PREFIX aat: <http://vocab.getty.edu/aat/>
        PREFIX gvp: <http://vocab.getty.edu/ontology#>
        PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
        PREFIX schema: <http://schema.org/>
        PREFIX arp: <http://example.org/arp#>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        PREFIX dcterms: <http://purl.org/dc/terms/>
        PREFIX owl: <http://www.w3.org/2002/07/owl#>
        PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    """

    def get_material_distribution(self) -> MaterialDistribution:
        """
        Get artwork counts grouped by Getty AAT material types.
        
        Returns distribution of artworks by their schema:artMedium values
        that link to Getty AAT URIs.
        """
        # Query local Fuseki for material counts
        query = f"""
        PREFIX schema: <{SCHEMA_NS}>
        PREFIX arp: <{ARP_NS}>
        
        SELECT ?material (COUNT(DISTINCT ?artwork) AS ?count) WHERE {{
            ?artwork a arp:Artwork .
            ?artwork schema:artMedium ?material .
            FILTER(STRSTARTS(STR(?material), "{AAT_NS}"))
        }}
        GROUP BY ?material
        ORDER BY DESC(?count)
        """
        
        try:
            result = sparql_service.execute_query(query)
            bindings = result.get("results", {}).get("bindings", [])
            
            materials: List[GettyMaterialStat] = []
            total_artworks = 0
            
            for binding in bindings:
                material_uri = binding.get("material", {}).get("value", "")
                count = int(binding.get("count", {}).get("value", 0))
                total_artworks += count
                
                # Fetch Getty label for this material
                getty_info = external_sparql_service.get_getty_term(material_uri)
                
                materials.append(GettyMaterialStat(
                    getty_uri=material_uri,
                    pref_label=getty_info.get("prefLabel") if "error" not in getty_info else None,
                    scope_note=getty_info.get("scopeNote") if "error" not in getty_info else None,
                    artwork_count=count,
                    broader_category=getty_info.get("broader", {}).get("label") if getty_info.get("broader") else None,
                    broader_uri=getty_info.get("broader", {}).get("uri") if getty_info.get("broader") else None,
                ))
            
            return MaterialDistribution(
                total_artworks=total_artworks,
                materials=materials,
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error fetching material distribution: {e}")
            return MaterialDistribution(
                total_artworks=0,
                materials=[],
                generated_at=datetime.utcnow()
            )

    def get_material_hierarchy(self) -> MaterialHierarchyResponse:
        """
        Get material distribution organized by Getty AAT broader categories.
        
        Groups materials by their parent categories in the Getty hierarchy.
        """
        # First get the basic material distribution
        distribution = self.get_material_distribution()
        
        # Group materials by broader category
        category_map: Dict[str, HierarchyStat] = {}
        
        for material in distribution.materials:
            # Use broader category or "Uncategorized" if none
            category_uri = material.broader_uri or "uncategorized"
            category_label = material.broader_category or "Uncategorized"
            
            if category_uri not in category_map:
                category_map[category_uri] = HierarchyStat(
                    category_uri=category_uri,
                    category_label=category_label,
                    subcategories=[],
                    total_count=0
                )
            
            category_map[category_uri].subcategories.append(material)
            category_map[category_uri].total_count += material.artwork_count
        
        # Sort categories by total count
        categories = sorted(
            category_map.values(),
            key=lambda x: x.total_count,
            reverse=True
        )
        
        return MaterialHierarchyResponse(
            total_artworks=distribution.total_artworks,
            categories=categories,
            generated_at=datetime.utcnow()
        )

    def get_temporal_trends(self) -> TemporalTrendsResponse:
        """
        Get material usage trends across art historical periods.
        
        Cross-references artwork periods with Getty AAT materials.
        """
        query = f"""
        PREFIX schema: <{SCHEMA_NS}>
        PREFIX arp: <{ARP_NS}>
        
        SELECT ?period ?material (COUNT(DISTINCT ?artwork) AS ?count) WHERE {{
            ?artwork a arp:Artwork .
            ?artwork arp:artworkPeriod ?period .
            ?artwork schema:artMedium ?material .
            FILTER(STRSTARTS(STR(?material), "{AAT_NS}"))
        }}
        GROUP BY ?period ?material
        ORDER BY ?period DESC(?count)
        """
        
        try:
            result = sparql_service.execute_query(query)
            bindings = result.get("results", {}).get("bindings", [])
            
            # Group by period
            period_map: Dict[str, TemporalTrend] = {}
            material_labels: Dict[str, str] = {}  # Cache material labels
            
            for binding in bindings:
                period = binding.get("period", {}).get("value", "Unknown")
                material_uri = binding.get("material", {}).get("value", "")
                count = int(binding.get("count", {}).get("value", 0))
                
                # Get material label (cached)
                if material_uri not in material_labels:
                    getty_info = external_sparql_service.get_getty_term(material_uri)
                    material_labels[material_uri] = getty_info.get("prefLabel") if "error" not in getty_info else None
                
                if period not in period_map:
                    period_map[period] = TemporalTrend(
                        period=period,
                        total_artworks=0,
                        materials=[]
                    )
                
                period_map[period].materials.append(PeriodMaterialStat(
                    getty_uri=material_uri,
                    pref_label=material_labels.get(material_uri),
                    count=count
                ))
                period_map[period].total_artworks += count
            
            trends = list(period_map.values())
            
            return TemporalTrendsResponse(
                total_periods=len(trends),
                trends=trends,
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error fetching temporal trends: {e}")
            return TemporalTrendsResponse(
                total_periods=0,
                trends=[],
                generated_at=datetime.utcnow()
            )

    def get_cross_analysis(
        self,
        dimension_x: str = "period",
        dimension_y: str = "material"
    ) -> CrossAnalysisResponse:
        """
        Get cross-category analysis (e.g., period x material matrix).
        
        Args:
            dimension_x: X-axis dimension ("period", "location", "artist")
            dimension_y: Y-axis dimension ("material")
        
        Returns:
            Cross-analysis matrix with counts for each combination.
        """
        # Map dimension names to SPARQL predicates
        dimension_predicates = {
            "period": ("arp:artworkPeriod", "?period"),
            "location": ("arp:currentLocation/schema:name", "?location"),
            "artist": ("dc:creator/schema:name", "?artist"),
            "material": ("schema:artMedium", "?material"),
        }
        
        if dimension_x not in dimension_predicates or dimension_y not in dimension_predicates:
            return CrossAnalysisResponse(
                dimension_x=dimension_x,
                dimension_y=dimension_y,
                x_values=[],
                y_values=[],
                matrix=[],
                total_artworks=0,
                generated_at=datetime.utcnow()
            )
        
        x_pred, x_var = dimension_predicates[dimension_x]
        y_pred, y_var = dimension_predicates[dimension_y]
        
        # Build query for cross-analysis
        material_filter = ""
        if dimension_y == "material":
            material_filter = f'FILTER(STRSTARTS(STR({y_var}), "{AAT_NS}"))'
        elif dimension_x == "material":
            material_filter = f'FILTER(STRSTARTS(STR({x_var}), "{AAT_NS}"))'
        
        query = f"""
        PREFIX schema: <{SCHEMA_NS}>
        PREFIX arp: <{ARP_NS}>
        PREFIX dc: <http://purl.org/dc/elements/1.1/>
        
        SELECT {x_var} {y_var} (COUNT(DISTINCT ?artwork) AS ?count) WHERE {{
            ?artwork a arp:Artwork .
            ?artwork {x_pred} {x_var} .
            ?artwork {y_pred} {y_var} .
            {material_filter}
        }}
        GROUP BY {x_var} {y_var}
        ORDER BY {x_var} DESC(?count)
        """
        
        try:
            result = sparql_service.execute_query(query)
            bindings = result.get("results", {}).get("bindings", [])
            
            x_values_set: set = set()
            y_values_set: set = set()
            matrix: List[CrossAnalysisCell] = []
            material_labels: Dict[str, str] = {}
            total_artworks = 0
            
            for binding in bindings:
                x_val = binding.get(x_var.replace("?", ""), {}).get("value", "")
                y_val = binding.get(y_var.replace("?", ""), {}).get("value", "")
                count = int(binding.get("count", {}).get("value", 0))
                total_artworks += count
                
                x_values_set.add(x_val)
                
                # Get material label if y dimension is material
                y_label = y_val
                y_uri = None
                if dimension_y == "material" and y_val.startswith(AAT_NS):
                    y_uri = y_val
                    if y_val not in material_labels:
                        getty_info = external_sparql_service.get_getty_term(y_val)
                        material_labels[y_val] = getty_info.get("prefLabel", y_val) if "error" not in getty_info else y_val
                    y_label = material_labels.get(y_val, y_val)
                
                y_values_set.add(y_label)
                
                matrix.append(CrossAnalysisCell(
                    row_value=x_val,
                    column_value=y_label,
                    column_uri=y_uri,
                    count=count
                ))
            
            return CrossAnalysisResponse(
                dimension_x=dimension_x,
                dimension_y=dimension_y,
                x_values=sorted(list(x_values_set)),
                y_values=sorted(list(y_values_set)),
                matrix=matrix,
                total_artworks=total_artworks,
                generated_at=datetime.utcnow()
            )
            
        except Exception as e:
            logger.error(f"Error fetching cross analysis: {e}")
            return CrossAnalysisResponse(
                dimension_x=dimension_x,
                dimension_y=dimension_y,
                x_values=[],
                y_values=[],
                matrix=[],
                total_artworks=0,
                generated_at=datetime.utcnow()
            )

    def execute_statistics_query(
        self,
        query: str,
        include_getty_prefixes: bool = True
    ) -> StatisticsQueryResponse:
        """
        Execute a custom SPARQL statistics query with optional Getty prefixes.
        
        Args:
            query: The SPARQL query to execute
            include_getty_prefixes: Whether to auto-inject Getty namespace prefixes
        
        Returns:
            Query results or error message.
        """
        start_time = time.time()
        
        try:
            # Inject Getty prefixes if requested
            if include_getty_prefixes:
                # Only add prefixes that aren't already in the query
                prefixes_to_add = []
                for line in self.GETTY_PREFIXES.strip().split("\n"):
                    prefix_name = line.strip().split(":")[0].replace("PREFIX ", "")
                    if f"PREFIX {prefix_name}:" not in query:
                        prefixes_to_add.append(line.strip())
                
                if prefixes_to_add:
                    query = "\n".join(prefixes_to_add) + "\n" + query
            
            result = sparql_service.execute_query(query)
            execution_time = int((time.time() - start_time) * 1000)
            
            return StatisticsQueryResponse(
                success=True,
                results=result,
                error=None,
                execution_time_ms=execution_time
            )
            
        except Exception as e:
            execution_time = int((time.time() - start_time) * 1000)
            logger.error(f"Error executing statistics query: {e}")
            return StatisticsQueryResponse(
                success=False,
                results=None,
                error=str(e),
                execution_time_ms=execution_time
            )


# Singleton instance
statistics_service = StatisticsService()
