# Graph Explorer Setup Guide

This guide explains how to set up and configure the Data Treehouse graph explorer for the W3C Ontology System.

## Quick Start

1. **Build the graph explorer** (first time only):
   ```bash
   cd graph-explorer
   npm install
   BUNDLE_PEERS=true ./node_modules/.bin/webpack --config webpack.demo.config.js
   cd ..
   ```

2. **Start all services**:
   ```bash
   docker-compose up --build
   ```

3. **Access the graph explorer**:
   Open your browser and navigate to: `http://localhost:3000`

## Configuration

The graph explorer is configured in `docker-compose.yml` under the `graph-explorer` service to connect to the Python API:

```yaml
graph-explorer:
  build:
    context: ./graph-explorer
    dockerfile: Dockerfile
  environment:
    # Connect to Python API (default configuration)
    - ENDPOINT_URL=http://ontology-api:8000/query
    - USE_CREDS=no
    - LUCENE_SEARCH=no
```

**Note**: The graph explorer is configured to use the Python API endpoint by default. To switch to Fuseki, change `ENDPOINT_URL` to `http://fuseki:3030/ontology/sparql`.

### Environment Variables

| Variable | Description | Default | Options |
|----------|-------------|---------|---------|
| `ENDPOINT_URL` | SPARQL endpoint URL | `http://ontology-api:8000/query` | Any valid URL |
| `USE_CREDS` | Use credentials for API access | `no` | `yes`, `no` |
| `LUCENE_SEARCH` | Use Lucene-based search | `no` | `yes`, `no` |

## How It Works

### Architecture

```
Browser (localhost:3000)
    ↓
Graph Explorer Container (Port 80)
    ↓ SPARQL Queries
Ontology API Container (Port 8000)
    ↓
RDF Data (maplib)
```

### SPARQL Endpoint

The graph explorer sends SPARQL queries to the `/query` endpoint of the Python API. The API supports:

- **GET requests**: `GET /query?query=SELECT+...`
- **POST requests with form data**: `POST /query` with `Content-Type: application/x-www-form-urlencoded`
- **POST requests with JSON**: `POST /query` with `Content-Type: application/json`

The API returns results in standard SPARQL JSON format:

```json
{
  "head": {
    "vars": ["s", "p", "o"]
  },
  "results": {
    "bindings": [
      {
        "s": {"type": "uri", "value": "http://example.org/Entity1"},
        "p": {"type": "uri", "value": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"},
        "o": {"type": "uri", "value": "http://www.w3.org/2002/07/owl#Class"}
      }
    ]
  }
}
```

## Building the Graph Explorer

The graph explorer needs to be built before it can be used in Docker. This is a one-time setup:

### Prerequisites

- Node.js v18.14.2 or compatible
- npm (comes with Node.js)

### Build Steps

1. Navigate to the graph-explorer directory:
   ```bash
   cd graph-explorer
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Build the bundles:
   ```bash
   BUNDLE_PEERS=true ./node_modules/.bin/webpack --config webpack.demo.config.js
   ```

   On Windows PowerShell:
   ```powershell
   $env:BUNDLE_PEERS="true"; npm run build
   ```

4. Verify the build:
   ```bash
   ls dist/examples/
   ```

   You should see files like:
   - `commons.bundle.js`
   - `fuseki-regexsearch.bundle.js`
   - `fuseki-lucene.bundle.js`

5. Return to the project root:
   ```bash
   cd ..
   ```

## Using the Graph Explorer

### Initial View

When you first open the graph explorer, you'll see:
- An empty canvas in the center
- A class tree on the left (once ontology is loaded)
- Connection and filter panels on the right

### Loading Data

1. **Automatic Discovery**: The graph explorer automatically queries for OWL classes and properties
2. **Manual Search**: Use the search box to find specific resources by URI or label
3. **Class Tree**: Click on classes in the left panel to add them to the canvas

### Navigation

- **Add to Canvas**: Click on a class in the left panel
- **Expand Relationships**: Click on a node and select "Connections" to see related nodes
- **Pan**: Click and drag the canvas
- **Zoom**: Use mouse wheel or zoom controls
- **Select**: Click on nodes or edges to see details

### SPARQL Queries

The graph explorer sends various SPARQL queries automatically:

1. **Class Hierarchy Query**: Discovers all OWL classes and their subclass relationships
2. **Property Query**: Finds all RDF properties
3. **Instance Query**: Retrieves instances of selected classes
4. **Link Query**: Discovers relationships between nodes

## Troubleshooting

### Graph Explorer Not Loading

**Problem**: Browser shows "Cannot connect" or blank page

**Solutions**:
1. Check if the container is running:
   ```bash
   docker-compose ps graph-explorer
   ```

2. Check container logs:
   ```bash
   docker-compose logs graph-explorer
   ```

3. Verify the build completed successfully:
   ```bash
   ls graph-explorer/dist/examples/
   ```

### No Classes Appearing

**Problem**: The class tree on the left is empty

**Solutions**:
1. Ensure ontology files are loaded in the API:
   ```bash
   curl http://localhost:8000/triples
   ```

2. Check if the API is responding to SPARQL queries:
   ```bash
   curl -X POST http://localhost:8000/query \
     -H "Content-Type: application/json" \
     -d '{"query": "SELECT ?s WHERE { ?s a <http://www.w3.org/2002/07/owl#Class> } LIMIT 10"}'
   ```

3. Verify the ontology contains OWL classes:
   ```bash
   grep "owl:Class" ontology/*.ttl
   ```

### Connection Errors

**Problem**: Graph explorer shows "Failed to connect to endpoint"

**Solutions**:
1. Verify both services are on the same network:
   ```bash
   docker network inspect ontology-network
   ```

2. Test connectivity from graph-explorer to API:
   ```bash
   docker-compose exec graph-explorer wget -O- http://ontology-api:8000/health
   ```

3. Check API health:
   ```bash
   curl http://localhost:8000/health
   ```

### Build Errors

**Problem**: `npm install` or webpack build fails

**Solutions**:
1. Ensure you're using Node.js v18.14.2:
   ```bash
   node --version
   ```

2. Clear npm cache and reinstall:
   ```bash
   cd graph-explorer
   rm -rf node_modules package-lock.json
   npm cache clean --force
   npm install
   ```

3. Check for build errors in the output and install missing dependencies

## Advanced Configuration

### Custom Endpoint

To connect to a different SPARQL endpoint:

```yaml
environment:
  - ENDPOINT_URL=http://your-sparql-endpoint:port/sparql
```

### Multiple Endpoints

You can configure multiple endpoints using the `ENDPOINT_MAP` variable:

```yaml
environment:
  - ENDPOINT_MAP=|
      /endpoint1|http://api1:8000/query|no|no
      /endpoint2|http://api2:8000/query|yes|no
```

Format: `path|endpoint_url|lucene_search|use_creds`

### Authentication

If your API requires authentication:

```yaml
environment:
  - ENDPOINT_URL=http://ontology-api:8000/query
  - USE_CREDS=yes
```

Then configure CORS in the API to accept credentials.

## Integration with Python API

The Python API has been configured to support the graph explorer:

### SPARQL Endpoint

The `/query` endpoint accepts:
- Standard SPARQL protocol (GET and POST)
- JSON format for custom applications
- Returns SPARQL JSON results format

### CORS

CORS is enabled to allow the graph explorer to make requests from the browser.

### Query Formats

The API automatically detects the query format:

1. **GET with query parameter**:
   ```
   GET /query?query=SELECT+...
   ```

2. **POST with form data**:
   ```
   POST /query
   Content-Type: application/x-www-form-urlencoded
   
   query=SELECT ...
   ```

3. **POST with JSON**:
   ```
   POST /query
   Content-Type: application/json
   
   {"query": "SELECT ..."}
   ```

## Requirements Satisfied

This implementation satisfies the following requirements from the spec:

- **8.1**: ✓ Integration with Data Treehouse graph explorer for visualization
- **8.2**: ✓ RDF data exposed in format compatible with graph explorer (SPARQL JSON)
- **8.3**: ✓ Complete ontology structure provided (classes, properties, instances)
- **8.4**: ✓ Graph explorer runs as Docker service accessible via web browser
- **8.5**: ✓ Graph explorer configured to connect to RDF Store endpoint

## Next Steps

1. Load your ontology files into the API
2. Access the graph explorer at http://localhost:3000
3. Explore the class hierarchy in the left panel
4. Add classes to the canvas and explore relationships
5. Use the search function to find specific resources
6. Save diagrams for later use (stored in browser local storage)

## Additional Resources

- [Graph Explorer GitHub Repository](https://github.com/DataTreehouse/graph-explorer)
- [Ontodia Documentation](https://github.com/metaphacts/ontodia)
- [SPARQL 1.1 Protocol](https://www.w3.org/TR/sparql11-protocol/)
- [SPARQL JSON Results Format](https://www.w3.org/TR/sparql11-results-json/)
