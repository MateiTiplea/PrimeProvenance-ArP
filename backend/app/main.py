from fastapi import FastAPI

from .routers.artworks import router as artworks_router
from .routers.sparql import router as sparql_router

app = FastAPI(
    title="ArP API",
    description="Artwork Provenance API",
    version="0.1.0",
)

app.include_router(artworks_router)
app.include_router(sparql_router)


@app.get("/")
async def root():
    return {"message": "ArP - Artwork Provenance API"}


@app.get("/health")
async def health():
    return {"status": "ok"}
