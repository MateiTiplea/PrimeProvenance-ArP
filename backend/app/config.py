"""Application configuration."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""

    # Fuseki configuration
    fuseki_host: str
    fuseki_port: int
    fuseki_dataset: str
    fuseki_username: str
    fuseki_password: str

    # External SPARQL endpoints (with defaults)
    dbpedia_endpoint: str = "https://dbpedia.org/sparql"
    wikidata_endpoint: str = "https://query.wikidata.org/sparql"
    getty_endpoint: str = "http://vocab.getty.edu/sparql"

    # Cache settings
    external_cache_ttl: int = 3600  # seconds (1 hour)

    @property
    def fuseki_query_endpoint(self) -> str:
        return (
            f"http://{self.fuseki_host}:{self.fuseki_port}/{self.fuseki_dataset}/query"
        )

    @property
    def fuseki_update_endpoint(self) -> str:
        return (
            f"http://{self.fuseki_host}:{self.fuseki_port}/{self.fuseki_dataset}/update"
        )

    model_config = SettingsConfigDict(
        env_prefix="ARP_", env_file=".env", env_file_encoding="utf-8", extra="ignore"
    )


settings = Settings()
