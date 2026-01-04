"""Artworks router."""

from fastapi import APIRouter

router = APIRouter(prefix="/artworks", tags=["artworks"])


@router.get("/")
async def list_artworks():
    """List artworks endpoint placeholder."""
    return {"artworks": []}
