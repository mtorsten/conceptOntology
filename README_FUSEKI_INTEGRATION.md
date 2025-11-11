# Apache Jena Fuseki and Graph Explorer Integration

This document describes the integration of Apache Jena Fuseki SPARQL server and the Graph Explorer visualization tool with the W3C Ontology System.

## Overview

The system uses two complementary services for RDF data management and visualization:

1. **Apache Jena Fuseki**: A robust SPARQL server that provides a persistent RDF triple store using TDB2 format, with full SPARQL 1.1 query and update support.

2. **Graph Explorer**: An interactive web-based interface for visualizing and exploring RDF ontology data through an intuitive graph-based UI.

Together, these services provide both powerful querying capabilities and visual exploration of the ontology structure, including classes, properties, instances, and their relationships.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Browser                          │
│         Graph Explorer UI (http://localhost:3000)        │
│         Fuseki Web UI (http://localhost:3030)            │
└────────────────────────┬────────────────────────────────┘
                         │
                         │ HTTP
                         │
┌────────────────────────▼────────────────────────────────┐
│              Graph Explorer Container                    │
│                    (Port 3000)                           │
│                                                          │
│  - Web UI for visualization                             │
│  - Interactive graph display                            │
│  - Node/edge filtering and search                       │
└────────────────────────┬────────────────────────────────┘
                         │
                         │ SPARQL Protocol
                         │
┌────────────────────────▼────────────────────────────────┐
│           Apache Jena Fuseki Container                   │
│                    (Port 3030)                           │
│                                                          │
│  - SPARQL 1.1 Query & Update                            │
│  - TDB2 persistent triple store                         │
│  - Graph Store Protocol                                 │
│  - Built-in web UI                                      │
│  - Dataset: /ontology                                   │
└────────────────────────┬────────────────────────────────┘
                         │
                         │ Shared Volumes
                         │
┌────────────────────────▼────────────────────────────────┐
│              Ontology API Container                      │
│                    (Port 8000)                           │
│                                                          │
│  - Python maplib integration                            │
│  - SHACL validation                                     │
│  - Custom query operations                              │
└─────────────────────────────────────────────────────────┘
```

## Apache Jena Fuseki

### What is Fuseki?

Apache Jena Fuseki is a SPARQL server that provides:
- **SPARQL 1.1 Protocol**: Full support for SPARQL queries and updates
- **TDB2 Storage**: High-performance, persistent RDF triple store
- **Graph Store Protocol**: RESTful API for graph management
- **Web UI**: Built-in interface for query execution and dataset management
- **Scalability**: Handles large RDF datasets efficiently

### TDB2 Format

TDB2 is Apache Jena's native RDF database format:
- **Persistent Storage**: Data survives container restarts
- **Indexed**: Optimized for fast SPARQL query execution
- **Transactional**: ACID properties for data integrity
- **Compressed**: Efficient storage of large datasets
- **File-based**: Stored in `/fuseki/databases/ontology` directory

### Configuration

#### Environment Variables
- `ADMIN_PASSWORD`: Admin password for Fuseki web UI (default: `admin123`)
- `JVM_ARGS`: Java Virtual Machine arguments (default: `-Xmx2g -Xms1g`)
  - `-Xmx2g`: Maximum heap size of 2GB
  - `-Xms1g`: Initial heap size of 1GB
- `FUSEKI_CORS_ENABLED`: Enable CORS for cross-origin requests (default: `true`)

#### Configuration File

The Fuseki configuration is defined in `fuseki-config/config.ttl`:

```turtle
<#service_ontology> rdf:type fuseki:Service ;
    fuseki:name "ontology" ;
    fuseki:serviceQuery "sparql" ;
    fuseki:serviceQuery "query" ;
    fuseki:serviceUpdate "update" ;
    fuseki:serviceUpload "upload" ;
    fuseki:serviceReadWriteGraphStore "data" ;
    fuseki:dataset <#dataset_ontology> ;
    .

<#dataset_ontology> rdf:type tdb2:DatasetTDB2 ;
    tdb2:location "/fuseki/databases/ontology" ;
    tdb2:unionDefaultGraph true ;
    .
```

#### Endpoints

Once Fuseki is running, the following endpoints are available:

- **Query Endpoint**: `http://localhost:3030/ontology/sparql`
- **Update Endpoint**: `http://localhost:3030/ontology/update`
- **Upload Endpoint**: `http://localhost:3030/ontology/upload`
- **Graph Store**: `http://localhost:3030/ontology/data`
- **Web UI**: `http://localhost:3030`
- **Health Check**: `http://localhost:3030/$/ping`

### Usage

#### Accessing Fuseki Web UI

1. Open browser to `http://localhost:3030`
2. Login with credentials:
   - Username: `admin`
   - Password: `admin123` (or your configured password)
3. Select the `ontology` dataset
4. Use the query editor to execute SPARQL queries

#### Loading Data into Fuseki

**Option 1: Using Fuseki Web UI**
1. Navigate to `http://localhost:3030`
2. Select the `ontology` dataset
3. Click "upload files"
4. Select your Turtle (.ttl) files
5. Click "upload"

**Option 2: Using HTTP POST**
```bash
curl -X POST \
  -H "Content-Type: text/turtle" \
  --data-binary @ontology/core.ttl \
  http://localhost:3030/ontology/data?default
```

**Option 3: Using s-put command**
```bash
docker-compose exec fuseki \
  /jena-fuseki/bin/s-put \
  http://localhost:3030/ontology/data \
  default \
  /ontology/core.ttl
```

#### Querying Data

**Using Fuseki Web UI:**
1. Navigate to `http://localhost:3030`
2. Select the `ontology` dataset
3. Enter your SPARQL query
4. Click "Execute"

**Using curl:**
```bash
curl -X POST \
  -H "Content-Type: application/sparql-query" \
  -H "Accept: application/sparql-results+json" \
  --data "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10" \
  http://localhost:3030/ontology/sparql
```

**Using Python:**
```python
import requests

query = """
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?class ?label WHERE {
  ?class a owl:Class .
  OPTIONAL { ?class rdfs:label ?label }
} LIMIT 100
"""

response = requests.post(
    'http://localhost:3030/ontology/sparql',
    data={'query': query},
    headers={'Accept': 'application/sparql-results+json'}
)

results = response.json()
print(results)
```

## Graph Explorer

### What is Graph Explorer?

Graph Explorer is a web-based visualization tool that:
- **Visualizes RDF Graphs**: Displays triples as interactive node-link diagrams
- **Explores Relationships**: Navigate through connected resources
- **Filters Data**: Focus on specific node types or properties
- **Searches**: Find resources by URI or label
- **Exports**: Save visualizations and data

### Configuration

The graph explorer is configured through environment variables in `docker-compose.yml`:

#### SPARQL Connection
- `ENDPOINT_URL`: SPARQL endpoint URL
  - Default: `http://fuseki:3030/ontology/sparql` (connects to Fuseki)
  - Alternative: `http://ontology-api:8000/query` (connects to Python API)
- `USE_CREDS`: Whether to use credentials for authentication (default: `no`)
- `LUCENE_SEARCH`: Enable Lucene full-text search (default: `no`)

### Usage

#### Accessing Graph Explorer

1. Ensure Fuseki is running and has data loaded
2. Open browser to `http://localhost:3000`
3. The graph explorer will automatically connect to Fuseki
4. Start exploring the ontology visually

#### Exploring the Ontology

1. **Initial View**: The graph loads with a default query showing classes and properties
2. **Click Nodes**: Select nodes to see their properties and relationships
3. **Expand Nodes**: Double-click to load connected resources
4. **Filter**: Use the filter panel to show/hide specific node types
5. **Search**: Use the search box to find specific resources
6. **Zoom/Pan**: Mouse wheel to zoom, drag to pan the canvas

#### Customizing Queries

The graph explorer allows you to customize the SPARQL query used to populate the graph:

1. Click the "Query" button
2. Enter a custom SPARQL query
3. Click "Execute"
4. The graph updates with the new results

Example queries:

**Show all OWL Classes:**
```sparql
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?class ?label WHERE {
  ?class a owl:Class .
  OPTIONAL { ?class rdfs:label ?label }
}
```

**Show Class Hierarchy:**
```sparql
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?subClass ?superClass WHERE {
  ?subClass rdfs:subClassOf ?superClass .
}
```

**Show Properties with Domains and Ranges:**
```sparql
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?property ?domain ?range WHERE {
  ?property rdfs:domain ?domain .
  ?property rdfs:range ?range .
}
```

## Integration with Python API

The system provides three ways to query RDF data:

### 1. Direct Fuseki Access
- **Use Case**: Standard SPARQL queries, data loading, graph management
- **Endpoint**: `http://localhost:3030/ontology/sparql`
- **Advantages**: Full SPARQL 1.1 support, persistent storage, high performance

### 2. Python API
- **Use Case**: Custom operations, SHACL validation, maplib integration
- **Endpoint**: `http://localhost:8000/query`
- **Advantages**: Python-based processing, validation, custom logic

### 3. Graph Explorer
- **Use Case**: Visual exploration, interactive navigation
- **Endpoint**: Configurable (Fuseki or Python API)
- **Advantages**: User-friendly, visual feedback, exploration tools

## Starting the Services

### Start All Services
```bash
docker-compose up -d
```

### Start Individual Services
```bash
# Start Fuseki only
docker-compose up -d fuseki

# Start Graph Explorer only
docker-compose up -d graph-explorer

# Start Python API only
docker-compose up -d ontology-api
```

### Check Service Status
```bash
docker-compose ps
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f fuseki
docker-compose logs -f graph-explorer
```

## Data Workflow

### Typical Workflow

1. **Load Ontology Files**
   - Use Fuseki web UI or API to load Turtle files
   - Data is persisted in TDB2 format

2. **Query via Fuseki**
   - Execute SPARQL queries through Fuseki endpoints
   - Use Fuseki web UI for ad-hoc queries

3. **Visualize with Graph Explorer**
   - Open Graph Explorer to see visual representation
   - Navigate relationships interactively

4. **Validate with Python API**
   - Use Python API for SHACL validation
   - Run custom validation rules

5. **Export Results**
   - Export data from Fuseki in various formats
   - Save visualizations from Graph Explorer

## Troubleshooting

### Fuseki Not Starting

**Check logs:**
```bash
docker-compose logs fuseki
```

**Common issues:**
- Insufficient memory: Increase JVM_ARGS in docker-compose.yml
- Port conflict: Ensure port 3030 is available
- Volume permissions: Check fuseki-data volume permissions

**Solution:**
```bash
# Restart Fuseki
docker-compose restart fuseki

# Rebuild if needed
docker-compose up -d --build fuseki
```

### Graph Explorer Not Connecting

**Check endpoint configuration:**
```bash
docker-compose exec graph-explorer env | grep ENDPOINT
```

**Verify Fuseki is accessible:**
```bash
curl http://localhost:3030/$/ping
```

**Solution:**
```bash
# Restart graph-explorer
docker-compose restart graph-explorer

# Check if Fuseki has data
curl -X POST \
  -H "Content-Type: application/sparql-query" \
  --data "SELECT (COUNT(*) as ?count) WHERE { ?s ?p ?o }" \
  http://localhost:3030/ontology/sparql
```

### No Data Displayed

**Check if data is loaded in Fuseki:**
```bash
curl -X POST \
  -H "Content-Type: application/sparql-query" \
  -H "Accept: application/sparql-results+json" \
  --data "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10" \
  http://localhost:3030/ontology/sparql
```

**Load data if empty:**
```bash
# Using Fuseki web UI at http://localhost:3030
# Or using curl:
curl -X POST \
  -H "Content-Type: text/turtle" \
  --data-binary @ontology/core.ttl \
  http://localhost:3030/ontology/data?default
```

### Performance Issues

**Increase Fuseki memory:**
Edit `docker-compose.yml`:
```yaml
environment:
  - JVM_ARGS=-Xmx4g -Xms2g  # Increase to 4GB max, 2GB initial
```

**Optimize queries:**
- Use LIMIT clauses
- Add specific graph patterns
- Use indexes effectively

**Monitor resource usage:**
```bash
docker stats fuseki
```

## Data Persistence

### TDB2 Database Location

The TDB2 database is stored in a Docker volume:
- Volume name: `fuseki-data`
- Container path: `/fuseki/databases/ontology`
- Persists across container restarts

### Backup and Restore

**Backup TDB2 database:**
```bash
# Create backup directory
mkdir -p backups

# Backup using tdbdump
docker-compose exec fuseki \
  /jena-fuseki/bin/tdbdump \
  --loc=/fuseki/databases/ontology \
  > backups/ontology-backup.nq
```

**Restore TDB2 database:**
```bash
# Stop Fuseki
docker-compose stop fuseki

# Clear existing data
docker volume rm fuseki-data

# Recreate volume
docker volume create fuseki-data

# Start Fuseki
docker-compose up -d fuseki

# Load backup
docker-compose exec -T fuseki \
  /jena-fuseki/bin/tdbloader \
  --loc=/fuseki/databases/ontology \
  < backups/ontology-backup.nq
```

## Security Considerations

### Authentication

**Fuseki Admin Access:**
- Default username: `admin`
- Default password: `admin123`
- **Change in production!**

**Update password:**
Edit `docker-compose.yml`:
```yaml
environment:
  - ADMIN_PASSWORD=your_secure_password
```

### Network Isolation

Services communicate over an internal Docker network (`ontology-network`):
- Fuseki is accessible from graph-explorer via internal network
- Only exposed ports are accessible from host
- Use firewall rules to restrict external access in production

### CORS Configuration

CORS is enabled by default for development:
```yaml
environment:
  - FUSEKI_CORS_ENABLED=true
```

In production, configure CORS to only allow specific origins.

## Requirements Mapping

This implementation satisfies the following requirements:

- **8.1**: Integration with graph explorer for visualization ✓
- **8.2**: RDF data exposed in compatible format (SPARQL endpoint) ✓
- **8.3**: Complete ontology structure provided (classes, properties, instances) ✓
- **8.4**: Graph explorer runs as Docker service accessible via browser ✓
- **8.5**: Graph explorer configured to connect to SPARQL endpoint ✓

## Additional Resources

- [Apache Jena Fuseki Documentation](https://jena.apache.org/documentation/fuseki2/)
- [TDB2 Documentation](https://jena.apache.org/documentation/tdb2/)
- [SPARQL 1.1 Query Language](https://www.w3.org/TR/sparql11-query/)
- [SPARQL 1.1 Protocol](https://www.w3.org/TR/sparql11-protocol/)
- [Graph Store Protocol](https://www.w3.org/TR/sparql11-http-rdf-update/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
