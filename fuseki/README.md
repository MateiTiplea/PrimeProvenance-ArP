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

Extends the official `stain/jena-fuseki` image to include custom configuration:

```dockerfile
FROM stain/jena-fuseki:latest
COPY config/config.ttl /fuseki/configuration/arp.ttl
```

This approach is necessary because Fuseki requires the `/fuseki/configuration` directory to be writable at runtime, making direct volume mounts problematic.

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

From the project root:

```bash
docker compose up fuseki
```

Fuseki will be available at: http://localhost:3030

### Using Docker Directly

```bash
docker run -p 3030:3030 \
  -v $(pwd)/fuseki/config:/fuseki/configuration \
  -v fuseki-data:/fuseki \
  -e ADMIN_PASSWORD=admin \
  stain/jena-fuseki:latest
```

## Loading Data

### Option 1: Via Fuseki UI

1. Open http://localhost:3030 in your browser
2. Log in with username `admin` and password `admin`
3. Navigate to the `arp` dataset
4. Click "Upload data"
5. Upload `arp-ontology.ttl` and `sample-data.ttl`

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

1. Check that `config.ttl` is mounted to `/fuseki/configuration/`
2. Restart the Fuseki container
3. Check Fuseki logs: `docker logs arp-fuseki`

### Permission Errors

Ensure the Docker volumes have correct permissions:

```bash
docker-compose down -v
docker-compose up fuseki
```

### Query Errors

Verify data is loaded:

```sparql
SELECT (COUNT(*) as ?count) WHERE { ?s ?p ?o }
```

Should return the total number of triples in the dataset.

