# Graph Explorer Quick Reference

## Configuration Summary

### Current Configuration (Python API)

```yaml
# docker-compose.yml
environment:
  - ENDPOINT_URL=http://ontology-api:8000/query
  - USE_CREDS=no
  - LUCENE_SEARCH=no
```

### Access URLs

- **Graph Explorer**: http://localhost:3000
- **Python API**: http://localhost:8000
- **Fuseki**: http://localhost:3030

## Quick Start

### 1. Build Graph Explorer (First Time Only)

```bash
cd graph-explorer
npm install
BUNDLE_PEERS=true ./node_modules/.bin/webpack --config webpack.demo.config.js
cd ..
```

**Windows PowerShell**:
```powershell
cd graph-explorer
npm install
$env:BUNDLE_PEERS="true"; npm run build-examples
cd ..
```

### 2. Start Services

```bash
docker-compose up -d
```

### 3. Load Ontology Data

```bash
curl -X POST http://localhost:8000/load \
  -H "Content-Type: application/json" \
  -d '{"files": ["ontology/core.ttl", "ontology/extensions.ttl"]}'
```

**Windows PowerShell**:
```powershell
Invoke-RestMethod -Uri "http://localhost:8000/load" `
  -Method Post `
  -ContentType "application/json" `
  -Body '{"files": ["ontology/core.ttl", "ontology/extensions.ttl"]}'
```

### 4. Access Graph Explorer

Open browser to: http://localhost:3000

## Environment Variables

| Variable | Value | Purpose |
|----------|-------|---------|
| `ENDPOINT_URL` | `http://ontology-api:8000/query` | SPARQL endpoint URL |
| `USE_CREDS` | `no` | Send credentials with requests |
| `LUCENE_SEARCH` | `no` | Use regex-based search |

## Common Commands

### Check Service Status

```bash
docker-compose ps
```

### View Logs

```bash
# All services
docker-compose logs -f

# Graph explorer only
docker-compose logs -f graph-explorer

# Python API only
docker-compose logs -f ontology-api
```

### Restart Services

```bash
# Restart all
docker-compose restart

# Restart graph explorer
docker-compose restart graph-explorer

# Restart with rebuild
docker-compose up -d --build graph-explorer
```

### Verify Configuration

```bash
# Run verification script
python verify_graph_explorer_config.py

# Check API health
curl http://localhost:8000/health

# Check graph explorer
curl http://localhost:3000

# Test SPARQL query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10"}'
```

## Troubleshooting

### Graph Explorer Not Loading

```bash
# Check if container is running
docker-compose ps graph-explorer

# Check logs
docker-compose logs graph-explorer

# Verify build
ls graph-explorer/dist/examples/

# Rebuild
docker-compose up -d --build graph-explorer
```

### No Classes Appearing

```bash
# Check if data is loaded
curl http://localhost:8000/triples

# Load ontology files
curl -X POST http://localhost:8000/load \
  -H "Content-Type: application/json" \
  -d '{"files": ["ontology/core.ttl"]}'

# Test OWL class query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "PREFIX owl: <http://www.w3.org/2002/07/owl#> SELECT ?class WHERE { ?class a owl:Class } LIMIT 10"}'
```

### Connection Errors

```bash
# Check API is running
curl http://localhost:8000/health

# Check network connectivity
docker-compose exec graph-explorer wget -O- http://ontology-api:8000/health

# Verify ENDPOINT_URL
docker-compose exec graph-explorer env | grep ENDPOINT
```

## Configuration Changes

### Switch to Fuseki

Edit `docker-compose.yml`:
```yaml
environment:
  - ENDPOINT_URL=http://fuseki:3030/ontology/sparql
```

Then restart:
```bash
docker-compose restart graph-explorer
```

### Enable Authentication

Edit `docker-compose.yml`:
```yaml
environment:
  - ENDPOINT_URL=http://ontology-api:8000/query
  - USE_CREDS=yes
```

Then restart:
```bash
docker-compose restart graph-explorer
```

## SPARQL Queries

### Discover Classes

```sparql
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?class ?label WHERE {
  ?class a owl:Class .
  OPTIONAL { ?class rdfs:label ?label }
}
```

### Discover Properties

```sparql
PREFIX rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?property ?domain ?range WHERE {
  ?property a ?type .
  FILTER(?type IN (rdf:Property, owl:ObjectProperty, owl:DatatypeProperty))
  OPTIONAL { ?property rdfs:domain ?domain }
  OPTIONAL { ?property rdfs:range ?range }
}
```

### Class Hierarchy

```sparql
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?subClass ?superClass WHERE {
  ?subClass rdfs:subClassOf ?superClass .
}
```

## Files Reference

| File | Purpose |
|------|---------|
| `docker-compose.yml` | Service configuration |
| `graph-explorer/Dockerfile` | Graph explorer container |
| `graph-explorer/docker-start.sh` | Startup script with env var injection |
| `graph-explorer-config.json` | Configuration reference |
| `GRAPH_EXPLORER_API_INTEGRATION.md` | Detailed integration guide |
| `GRAPH_EXPLORER_SETUP.md` | Setup instructions |
| `verify_graph_explorer_config.py` | Configuration verification script |

## Requirements Satisfied

- ✅ Configure graph explorer to connect to Python API endpoint
- ✅ Set up environment variables for API URL and connection settings
- ✅ Ensure graph explorer can query RDF data through the API
- ✅ Configure visualization settings for ontology structure display

## Next Steps

1. ✅ Build graph explorer
2. ✅ Start services
3. ✅ Load ontology data
4. ✅ Access graph explorer
5. ✅ Explore ontology visually

## Support

For detailed information, see:
- `GRAPH_EXPLORER_API_INTEGRATION.md` - Complete integration guide
- `GRAPH_EXPLORER_SETUP.md` - Setup and usage guide
- `README_FUSEKI_INTEGRATION.md` - Fuseki integration details

For issues, check:
- Container logs: `docker-compose logs`
- API health: `curl http://localhost:8000/health`
- Verification script: `python verify_graph_explorer_config.py`
