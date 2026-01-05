# Fuseki Configuration

This directory contains Apache Jena Fuseki configuration and data files for the ArP (Artwork Provenance) application.

## Directory Structure

```
fuseki/
├── Dockerfile               # Custom Fuseki image with configuration
├── config/
│   └── config.ttl           # TDB2 dataset configuration
├── data/
│   ├── arp-ontology.ttl     # ArP namespace and ontology definitions
│   └── sample-data.ttl      # Sample artwork data with provenance chains
└── README.md                # This file
```

## Configuration

### Dockerfile

Extends the official `stain/jena-fuseki` image to include custom configuration with proper permissions:

```dockerfile
FROM stain/jena-fuseki:latest

USER root
RUN mkdir -p /fuseki/configuration /fuseki/databases/arp

COPY config/config.ttl /fuseki/configuration/arp.ttl

RUN chown -R 1000:1000 /fuseki
```

The Dockerfile:
- Switches to root to create required directories
- Creates the TDB2 database directory at `/fuseki/databases/arp`
- Copies the dataset configuration
- Sets correct ownership for the fuseki user (uid 1000)

### config.ttl

Defines a persistent TDB2 dataset named `arp` with the following endpoints:

| Endpoint | URL | Description |
|----------|-----|-------------|
| SPARQL Query | `/arp/sparql` or `/arp/query` | Execute SPARQL SELECT/CONSTRUCT queries |
| SPARQL Update | `/arp/update` | Execute SPARQL INSERT/DELETE operations |
| Graph Store (RW) | `/arp/data` | HTTP access to named graphs (read/write) |
| Graph Store (RO) | `/arp/get` | HTTP access to named graphs (read-only) |

## Starting Fuseki

### Using Docker Compose (Recommended)

From the project root, build and start the containers:

```bash
docker compose build --no-cache && docker compose up -d
```

Fuseki will be available at: http://localhost:3030

To start only the Fuseki service:

```bash
docker compose build --no-cache fuseki && docker compose up -d fuseki
```

### Stopping and Cleaning Up

```bash
# Stop containers
docker compose down

# Stop and remove volumes (fresh start)
docker compose down -v
```

## Authentication

Fuseki uses Apache Shiro for authentication. The default configuration:

| Operation | Authentication Required |
|-----------|------------------------|
| Web UI (browsing) | No |
| SPARQL Query (`/arp/sparql`) | No |
| SPARQL Update (`/arp/update`) | Yes |
| Data Upload (`/arp/data`) | Yes |
| Admin API (`/$/**`) | Yes |

Default credentials: **admin / admin**

Note: The web UI will prompt for credentials when you attempt write operations (upload, update). If authentication doesn't appear to work, try using an incognito browser window to clear any cached credentials.

## Loading Data

### Option 1: Via Fuseki UI

1. Open http://localhost:3030 in your browser
2. Navigate to the `arp` dataset
3. Click "Upload data"
4. Upload `arp-ontology.ttl` and `sample-data.ttl`
5. Log in with `admin` / `admin` when prompted

### Option 2: Via HTTP API

```bash
# Load ontology
curl -X POST http://localhost:3030/arp/data \
  -H "Content-Type: text/turtle" \
  --data-binary @fuseki/data/arp-ontology.ttl \
  -u admin:admin

# Load sample data
curl -X POST http://localhost:3030/arp/data \
  -H "Content-Type: text/turtle" \
  --data-binary @fuseki/data/sample-data.ttl \
  -u admin:admin
```

### Option 3: Via SPARQL Update

```bash
curl -X POST http://localhost:3030/arp/update \
  -H "Content-Type: application/sparql-update" \
  -d "LOAD <file:///staging/arp-ontology.ttl>" \
  -u admin:admin
```

## Sample Queries

### List All Artworks

```sparql
PREFIX arp: <http://example.org/arp#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX schema: <http://schema.org/>

SELECT ?artwork ?title ?artistName WHERE {
  ?artwork a arp:Artwork ;
           dc:title ?title ;
           dc:creator ?artist .
  ?artist schema:name ?artistName .
}
```

### Get Provenance Chain for an Artwork

```sparql
PREFIX arp: <http://example.org/arp#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX prov: <http://www.w3.org/ns/prov#>
PREFIX schema: <http://schema.org/>

SELECT ?order ?eventType ?date ?description WHERE {
  arp:artwork_mona_lisa arp:hasProvenanceEvent ?event .
  ?event arp:eventType ?eventType ;
         arp:provenanceOrder ?order .
  OPTIONAL { ?event prov:startedAtTime ?date }
  OPTIONAL { ?event dc:description ?description }
}
ORDER BY ?order
```

### Find Romanian Artworks

```sparql
PREFIX arp: <http://example.org/arp#>
PREFIX dc: <http://purl.org/dc/elements/1.1/>
PREFIX schema: <http://schema.org/>

SELECT ?artwork ?title ?artistName WHERE {
  ?artwork a arp:Artwork ;
           dc:title ?title ;
           dc:creator ?artist .
  ?artist schema:name ?artistName ;
          schema:nationality "Romanian" .
}
```

## Namespaces Used

| Prefix | URI |
|--------|-----|
| `arp` | `http://example.org/arp#` |
| `crm` | `http://www.cidoc-crm.org/cidoc-crm/` |
| `dc` | `http://purl.org/dc/elements/1.1/` |
| `dcterms` | `http://purl.org/dc/terms/` |
| `prov` | `http://www.w3.org/ns/prov#` |
| `schema` | `http://schema.org/` |
| `aat` | `http://vocab.getty.edu/aat/` |
| `dbr` | `http://dbpedia.org/resource/` |
| `wd` | `http://www.wikidata.org/entity/` |

## Troubleshooting

### Dataset Not Found

If the `arp` dataset doesn't appear:

1. Rebuild the image without cache: `docker compose build --no-cache fuseki`
2. Remove existing volumes: `docker compose down -v`
3. Start fresh: `docker compose up -d`
4. Check Fuseki logs: `docker logs arp-fuseki`

### Permission Errors

If you see "FUSEKI_BASE is not writable" or similar:

```bash
docker compose down -v
docker compose build --no-cache
docker compose up -d
```

### Configuration Syntax Errors

If logs show "Undefined prefix" or TTL parsing errors:

1. Validate `config.ttl` syntax
2. Ensure all prefixes are declared (including `@prefix : <#> .`)
3. Rebuild: `docker compose build --no-cache && docker compose up -d`

### Query Errors

Verify data is loaded:

```sparql
SELECT (COUNT(*) as ?count) WHERE { ?s ?p ?o }
```

Should return the total number of triples in the dataset.
