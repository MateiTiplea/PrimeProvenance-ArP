from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers.artworks import router as artworks_router
from .routers.external import router as external_router
from .routers.search import router as search_router
from .routers.sparql import router as sparql_router
from .routers.statistics import router as statistics_router

app = FastAPI(
    title="ArP API",
    description="Artwork Provenance API with external SPARQL integration for DBpedia, Wikidata, and Getty AAT",
    version="0.1.0",
)

# CORS middleware for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(artworks_router, prefix="/api")
app.include_router(sparql_router, prefix="/api")
app.include_router(search_router, prefix="/api")
app.include_router(external_router, prefix="/api")
app.include_router(statistics_router, prefix="/api")


@app.get("/")
async def root():
    return {"message": "ArP - Artwork Provenance API"}


@app.get("/health")
async def health():
    return {"status": "ok"}
