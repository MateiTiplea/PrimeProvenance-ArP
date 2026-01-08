"""Statistics data models for Getty-based analytics."""

from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any


class GettyMaterialStat(BaseModel):
    """Statistics for a single Getty AAT material type."""
    
    getty_uri: str = Field(..., description="Getty AAT URI (e.g., http://vocab.getty.edu/aat/300015050)")
    pref_label: Optional[str] = Field(None, description="Preferred label from Getty AAT")
    scope_note: Optional[str] = Field(None, description="Scope note/definition from Getty AAT")
    artwork_count: int = Field(..., description="Number of artworks using this material")
    broader_category: Optional[str] = Field(None, description="Broader category label from Getty hierarchy")
    broader_uri: Optional[str] = Field(None, description="Broader category URI from Getty hierarchy")


class MaterialDistribution(BaseModel):
    """Distribution of artworks by Getty AAT material types."""
    
    total_artworks: int = Field(..., description="Total number of artworks with Getty material links")
    materials: List[GettyMaterialStat] = Field(default_factory=list, description="List of material statistics")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when statistics were generated")


class HierarchyStat(BaseModel):
    """Statistics for a Getty AAT broader category with subcategories."""
    
    category_uri: str = Field(..., description="Getty AAT category URI")
    category_label: str = Field(..., description="Category label from Getty AAT")
    subcategories: List[GettyMaterialStat] = Field(default_factory=list, description="Material types within this category")
    total_count: int = Field(..., description="Total artworks in this category")


class MaterialHierarchyResponse(BaseModel):
    """Response containing material hierarchy statistics."""
    
    total_artworks: int = Field(..., description="Total number of artworks with Getty material links")
    categories: List[HierarchyStat] = Field(default_factory=list, description="List of broader category statistics")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when statistics were generated")


class PeriodMaterialStat(BaseModel):
    """Material statistics for a specific time period."""
    
    getty_uri: str = Field(..., description="Getty AAT material URI")
    pref_label: Optional[str] = Field(None, description="Material label")
    count: int = Field(..., description="Number of artworks")


class TemporalTrend(BaseModel):
    """Material distribution for a specific time period."""
    
    period: str = Field(..., description="Time period (e.g., 'Renaissance', '1800-1850')")
    total_artworks: int = Field(..., description="Total artworks in this period")
    materials: List[PeriodMaterialStat] = Field(default_factory=list, description="Materials used in this period")


class TemporalTrendsResponse(BaseModel):
    """Response containing temporal trends of material usage."""
    
    total_periods: int = Field(..., description="Number of distinct periods")
    trends: List[TemporalTrend] = Field(default_factory=list, description="Trends by period")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when statistics were generated")


class CrossAnalysisCell(BaseModel):
    """A single cell in the cross-analysis matrix."""
    
    row_value: str = Field(..., description="Row dimension value (e.g., period name)")
    column_value: str = Field(..., description="Column dimension value (e.g., material label)")
    column_uri: Optional[str] = Field(None, description="Column dimension URI (for Getty materials)")
    count: int = Field(..., description="Number of artworks matching both dimensions")


class CrossAnalysisResponse(BaseModel):
    """Response for cross-category analysis (e.g., period x material)."""
    
    dimension_x: str = Field(..., description="X-axis dimension name (e.g., 'period')")
    dimension_y: str = Field(..., description="Y-axis dimension name (e.g., 'material')")
    x_values: List[str] = Field(default_factory=list, description="Unique values for X dimension")
    y_values: List[str] = Field(default_factory=list, description="Unique values for Y dimension")
    matrix: List[CrossAnalysisCell] = Field(default_factory=list, description="Cross-analysis data cells")
    total_artworks: int = Field(..., description="Total artworks in analysis")
    generated_at: datetime = Field(default_factory=datetime.utcnow, description="Timestamp when statistics were generated")


class StatisticsQueryRequest(BaseModel):
    """Request for custom statistics SPARQL query."""
    
    query: str = Field(..., description="SPARQL query (Getty prefixes will be auto-injected)")
    include_getty_prefixes: bool = Field(True, description="Whether to auto-inject Getty namespace prefixes")


class StatisticsQueryResponse(BaseModel):
    """Response for custom statistics query."""
    
    success: bool = Field(..., description="Whether the query executed successfully")
    results: Optional[Dict[str, Any]] = Field(None, description="SPARQL query results")
    error: Optional[str] = Field(None, description="Error message if query failed")
    execution_time_ms: Optional[int] = Field(None, description="Query execution time in milliseconds")
