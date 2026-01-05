"""Provenance data models."""

from pydantic import BaseModel, Field
from typing import Optional, List
from enum import Enum


class ProvenanceEventType(str, Enum):
    """Types of provenance events."""
    
    CREATION = "Creation"
    SALE = "Sale"
    GIFT = "Gift"
    BEQUEST = "Bequest"
    THEFT = "Theft"
    RECOVERY = "Recovery"
    LOAN = "Loan"
    RETURN = "Return"
    ACQUISITION = "Acquisition"


class ProvenanceRecord(BaseModel):
    """A single provenance event in an artwork's history."""
    
    id: str
    date: str
    event: ProvenanceEventType
    owner: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    sourceUri: Optional[str] = None
    order: Optional[int] = None


class ProvenanceEventCreate(BaseModel):
    """Schema for creating a new provenance event."""
    
    event: ProvenanceEventType
    date: str
    owner: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    sourceUri: Optional[str] = None


class ProvenanceEventUpdate(BaseModel):
    """Schema for updating a provenance event."""
    
    event: Optional[ProvenanceEventType] = None
    date: Optional[str] = None
    owner: Optional[str] = None
    location: Optional[str] = None
    description: Optional[str] = None
    sourceUri: Optional[str] = None


class ProvenanceChainResponse(BaseModel):
    """Complete provenance history for an artwork."""
    
    artworkId: str
    events: List[ProvenanceRecord]
