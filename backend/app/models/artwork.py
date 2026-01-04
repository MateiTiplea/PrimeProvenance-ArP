"""Artwork data model."""

from pydantic import BaseModel
from typing import Optional


class Artwork(BaseModel):
    """Basic artwork model."""
    
    uri: str
    title: str
    artist: Optional[str] = None
    description: Optional[str] = None
