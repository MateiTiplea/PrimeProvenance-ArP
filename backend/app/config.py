"""Application configuration."""

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    fuseki_host: str = "fuseki"
    fuseki_port: int = 3030
    fuseki_dataset: str = "arp"
    fuseki_username: str = "admin"
    fuseki_password: str = "admin"
    
    @property
    def fuseki_query_endpoint(self) -> str:
        return f"http://{self.fuseki_host}:{self.fuseki_port}/{self.fuseki_dataset}/query"
    
    @property
    def fuseki_update_endpoint(self) -> str:
        return f"http://{self.fuseki_host}:{self.fuseki_port}/{self.fuseki_dataset}/update"

    class Config:
        env_prefix = "ARP_"


settings = Settings()
