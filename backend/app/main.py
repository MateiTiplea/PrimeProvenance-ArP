from fastapi import FastAPI

app = FastAPI(
    title="ArP API",
    description="Artwork Provenance API",
    version="0.1.0",
)


@app.get("/")
async def root():
    return {"message": "ArP - Artwork Provenance API"}


@app.get("/health")
async def health():
    return {"status": "ok"}
