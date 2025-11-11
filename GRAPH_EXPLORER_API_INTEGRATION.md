# Graph Explorer Integration with Python API

This document describes the configuration and integration of the Data Treehouse Graph Explorer with the Python API endpoint for the W3C Ontology System.

## Overview

The Graph Explorer is configured to connect to the Python API (`http://ontology-api:8000/query`) to query and visualize RDF data. This integration enables interactive exploration of the ontology structure, including classes, properties, instances, and their relationships.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    User Browser                          │
│         http://localhost:3000                            │
└────────────────────────┬────────────────────────────────┘
                         │
                         │ HTTP Requests
                         │
┌────────────────────────▼────────────────────────────────┐
│           Graph Explorer Container                       │
│                  (Port 3000 → 80)                        │
│                                                          │
│  - Serves static web UI                                 │
│  - Processes environment variables at startup           │
│  - Injects ENDPOINT_URL into JavaScript bundles        │
└────────────────────────┬────────────────────────────────┘
                         │
                         │ SPARQL Queries (from browser)
                         │
┌────────────────────────▼────────────────────────────────┐
│            Python API Container                          │
│                  (Port 8000)                             │
│                                                          │
│  Endpoint: /query                                       │
│  - Accepts GET and POST requests                        │
│  - Supports multiple content types                      │
│  - Returns SPARQL JSON results format                   │
│  - CORS enabled for browser access                      │
└────────────────────────┬────────────────────────────────┘
                         │
                         │ maplib operations
                         │
┌────────────────────────▼────────────────────────────────┐
│                  RDF Data Store                          │
│                    (maplib)                              │
│                                                          │
│  - In-memory RDF triples                                │
│  - SPARQL query execution                               │
│  - Namespace management                                 │
└─────────────────────────────────────────────────────────┘
```

## Configuration

### Environment Variables

The Graph Explorer is configured through environment variables in `docker-compose.yml`:

```yaml
environment:
  # Primary configuration: Connect to Python API
  - ENDPOINT_URL=http://ontology-api:8000/query
  
  # Authentication: No credentials required
  - USE_CREDS=no
  
  # Search method: Use regex-based search
  - LUCENE_SEARCH=no
```

#### ENDPOINT_URL

**Purpose**: Specifies the SPARQL endpoint URL that the graph explorer will query.

**Value**: `http://ontology-api:8000/query`

**Details**:
- Uses internal Docker network hostname `ontology-api`
- Port 8000 is the Python API service port
- `/query` is the SPARQL endpoint path
- This URL is injected into the JavaScript bundles at container startup

**Alternative**: To connect to Fuseki instead, change to:
```yaml
- ENDPOINT_URL=http://fuseki:3030/ontology/sparql
```

#### USE_CREDS

**Purpose**: Controls whether the graph explorer sends credentials with requests.

**Value**: `no`

**Options**:
- `yes`: Send credentials (cookies, authorization headers) with requests
- `no`: Do not send credentials (default for open access)

**Details**:
- Set to `no` because the Python API does not require authentication
- If authentication is added to the API, change to `yes`
- Maps to JavaScript `fetch()` credentials option:
  - `yes` → `credentials: 'include'`
  - `no` → `credentials: 'same-origin'`

#### LUCENE_SEARCH

**Purpose**: Determines the search method used by the graph explorer.

**Value**: `no`

**Options**:
- `yes`: Use Lucene-based full-text search (requires Fuseki with Lucene index)
- `no`: Use regex-based search (works with any SPARQL endpoint)

**Details**:
- Set to `no` because the Python API uses standard SPARQL regex search
- Lucene search requires specific Fuseki configuration
- Regex search uses SPARQL `FILTER regex()` expressions

### How Configuration Works

The graph explorer uses a startup script (`docker-start.sh`) that:

1. Reads environment variables (`ENDPOINT_URL`, `USE_CREDS`, `LUCENE_SEARCH`)
2. Selects the appropriate JavaScript bundle:
   - `fuseki-lucene.bundle.js` if `LUCENE_SEARCH=yes`
   - `fuseki-regexsearch.bundle.js` if `LUCENE_SEARCH=no`
3. Injects environment variables into the bundle using Perl substitution
4. Creates the HTML index file with the configured bundle
5. Starts the Apache HTTP server to serve the files

This means configuration changes require a container restart to take effect.

## Python API Integration

### API Endpoint: /query

The Python API provides a SPARQL endpoint at `/query` that supports multiple request formats.

#### Request Methods

**GET Request**:
```http
GET /query?query=SELECT+%3Fs+%3Fp+%3Fo+WHERE+%7B+%3Fs+%3Fp+%3Fo+%7D+LIMIT+10
```

**POST Request (Form Data)**:
```http
POST /query
Content-Type: application/x-www-form-urlencoded

query=SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10
```

**POST Request (JSON)**:
```http
POST /query
Content-Type: application/json

{
  "query": "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10",
  "timeout": 30.0,
  "output_format": "sparql_json"
}
```

**POST Request (SPARQL Query)**:
```http
POST /query
Content-Type: application/sparql-query

SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10
```

#### Response Format

The API returns results in standard SPARQL JSON format:

```json
{
  "head": {
    "vars": ["s", "p", "o"]
  },
  "results": {
    "bindings": [
      {
        "s": {
          "type": "uri",
          "value": "http://example.org/Entity1"
        },
        "p": {
          "type": "uri",
          "value": "http://www.w3.org/1999/02/22-rdf-syntax-ns#type"
        },
        "o": {
          "type": "uri",
          "value": "http://www.w3.org/2002/07/owl#Class"
        }
      }
    ]
  }
}
```

#### CORS Configuration

The Python API has CORS (Cross-Origin Resource Sharing) enabled:

```python
from flask_cors import CORS
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes
```

This allows the graph explorer (running in the browser) to make requests to the API from a different origin.

### Query Processing Flow

1. **User Action**: User interacts with graph explorer (clicks node, searches, etc.)
2. **SPARQL Generation**: Graph explorer generates appropriate SPARQL query
3. **HTTP Request**: Browser sends query to `http://ontology-api:8000/query`
4. **API Processing**: Python API receives and validates the query
5. **Query Execution**: API executes query using maplib
6. **Result Formatting**: API formats results as SPARQL JSON
7. **Response**: API returns results to browser
8. **Visualization**: Graph explorer renders results as interactive graph

## Visualization Settings

### Automatic Discovery

The graph explorer automatically discovers ontology structure by executing SPARQL queries:

**Discover OWL Classes**:
```sparql
PREFIX owl: <http://www.w3.org/2002/07/owl#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?class ?label WHERE {
  ?class a owl:Class .
  OPTIONAL { ?class rdfs:label ?label }
}
```

**Discover Properties**:
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

**Discover Class Hierarchy**:
```sparql
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?subClass ?superClass WHERE {
  ?subClass rdfs:subClassOf ?superClass .
}
```

### Display Settings

The graph explorer provides various display options:

- **Node Types**: Different colors and shapes for classes, properties, and instances
- **Labels**: Display rdfs:label or local name
- **Connections**: Show relationships between nodes
- **Filtering**: Hide/show specific node types
- **Layout**: Force-directed, hierarchical, or circular layouts
- **Zoom/Pan**: Navigate large graphs
- **Search**: Find nodes by URI or label

## Usage

### Starting the Services

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

3. **Wait for services to be healthy**:
   ```bash
   docker-compose ps
   ```

4. **Access the graph explorer**:
   Open browser to `http://localhost:3000`

### Exploring the Ontology

1. **Initial Load**: The graph explorer loads and displays the class tree on the left
2. **Browse Classes**: Click on classes in the tree to add them to the canvas
3. **Expand Nodes**: Double-click nodes to load connected resources
4. **View Properties**: Click on nodes to see their properties in the right panel
5. **Navigate Relationships**: Click on edges to see relationship details
6. **Search**: Use the search box to find specific resources
7. **Filter**: Use the filter panel to show/hide node types
8. **Custom Queries**: Click "Query" to execute custom SPARQL queries

### Example Workflow

1. **Load Ontology Data**:
   ```bash
   curl -X POST http://localhost:8000/load \
     -H "Content-Type: application/json" \
     -d '{"files": ["ontology/core.ttl", "ontology/extensions.ttl"]}'
   ```

2. **Verify Data Loaded**:
   ```bash
   curl http://localhost:8000/triples
   ```

3. **Open Graph Explorer**:
   Navigate to `http://localhost:3000`

4. **Explore Visually**:
   - The class tree populates automatically
   - Click on classes to visualize them
   - Explore relationships interactively

## Troubleshooting

### Graph Explorer Not Loading

**Symptom**: Browser shows blank page or "Cannot connect"

**Solutions**:

1. **Check if graph explorer container is running**:
   ```bash
   docker-compose ps graph-explorer
   ```

2. **Check container logs**:
   ```bash
   docker-compose logs graph-explorer
   ```

3. **Verify build completed**:
   ```bash
   ls graph-explorer/dist/examples/
   ```
   Should show: `commons.bundle.js`, `fuseki-regexsearch.bundle.js`, etc.

4. **Rebuild if needed**:
   ```bash
   cd graph-explorer
   npm install
   BUNDLE_PEERS=true ./node_modules/.bin/webpack --config webpack.demo.config.js
   cd ..
   docker-compose up -d --build graph-explorer
   ```

### No Classes Appearing

**Symptom**: Graph explorer loads but class tree is empty

**Solutions**:

1. **Check if ontology data is loaded**:
   ```bash
   curl http://localhost:8000/triples
   ```

2. **Test SPARQL query directly**:
   ```bash
   curl -X POST http://localhost:8000/query \
     -H "Content-Type: application/json" \
     -d '{"query": "SELECT ?s WHERE { ?s a <http://www.w3.org/2002/07/owl#Class> } LIMIT 10"}'
   ```

3. **Load ontology files**:
   ```bash
   curl -X POST http://localhost:8000/load \
     -H "Content-Type: application/json" \
     -d '{"files": ["ontology/core.ttl"]}'
   ```

4. **Verify ontology contains OWL classes**:
   ```bash
   grep "owl:Class" ontology/*.ttl
   ```

### Connection Errors

**Symptom**: Graph explorer shows "Failed to connect to endpoint"

**Solutions**:

1. **Verify Python API is running**:
   ```bash
   curl http://localhost:8000/health
   ```

2. **Check network connectivity**:
   ```bash
   docker-compose exec graph-explorer wget -O- http://ontology-api:8000/health
   ```

3. **Verify ENDPOINT_URL configuration**:
   ```bash
   docker-compose exec graph-explorer env | grep ENDPOINT
   ```

4. **Check CORS is enabled**:
   ```bash
   curl -X OPTIONS http://localhost:8000/query \
     -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: POST" \
     -v
   ```

### Query Errors

**Symptom**: Graph explorer shows "Query failed" or error messages

**Solutions**:

1. **Check API logs**:
   ```bash
   docker-compose logs ontology-api
   ```

2. **Test query directly**:
   ```bash
   curl -X POST http://localhost:8000/query \
     -H "Content-Type: application/json" \
     -d '{"query": "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10"}'
   ```

3. **Verify SPARQL syntax**:
   - Check for missing prefixes
   - Verify triple patterns are valid
   - Ensure query is properly formatted

## Configuration Changes

### Switching to Fuseki

To connect the graph explorer to Fuseki instead of the Python API:

1. **Edit docker-compose.yml**:
   ```yaml
   environment:
     - ENDPOINT_URL=http://fuseki:3030/ontology/sparql
   ```

2. **Restart graph explorer**:
   ```bash
   docker-compose restart graph-explorer
   ```

3. **Verify connection**:
   ```bash
   curl http://localhost:3030/ontology/sparql?query=SELECT+*+WHERE+{?s+?p+?o}+LIMIT+1
   ```

### Enabling Authentication

To enable authentication on the Python API:

1. **Update API to require authentication** (implement in `api.py`)

2. **Update docker-compose.yml**:
   ```yaml
   environment:
     - ENDPOINT_URL=http://ontology-api:8000/query
     - USE_CREDS=yes
   ```

3. **Restart graph explorer**:
   ```bash
   docker-compose restart graph-explorer
   ```

### Custom Endpoint

To use a different SPARQL endpoint:

1. **Edit docker-compose.yml**:
   ```yaml
   environment:
     - ENDPOINT_URL=http://your-endpoint:port/sparql
   ```

2. **Restart graph explorer**:
   ```bash
   docker-compose restart graph-explorer
   ```

## Requirements Satisfied

This configuration satisfies all requirements for Task 10:

- ✅ **Configure graph explorer to connect to Python API endpoint**
  - ENDPOINT_URL set to `http://ontology-api:8000/query`
  - Environment variables properly configured in docker-compose.yml

- ✅ **Set up environment variables for API URL and connection settings**
  - ENDPOINT_URL: Python API endpoint
  - USE_CREDS: Authentication setting (no)
  - LUCENE_SEARCH: Search method (no for regex)

- ✅ **Ensure graph explorer can query RDF data through the API**
  - API supports standard SPARQL protocol
  - Returns SPARQL JSON results format
  - CORS enabled for browser access
  - Multiple request formats supported

- ✅ **Configure visualization settings for ontology structure display**
  - Automatic discovery of OWL classes and properties
  - Class hierarchy visualization
  - Property relationships display
  - Interactive node exploration

## Additional Resources

- [Graph Explorer GitHub Repository](https://github.com/DataTreehouse/graph-explorer)
- [SPARQL 1.1 Protocol](https://www.w3.org/TR/sparql11-protocol/)
- [SPARQL JSON Results Format](https://www.w3.org/TR/sparql11-results-json/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Flask-CORS Documentation](https://flask-cors.readthedocs.io/)

## Next Steps

1. Build the graph explorer (if not already done)
2. Start all services with `docker-compose up`
3. Load ontology data into the Python API
4. Access graph explorer at `http://localhost:3000`
5. Explore the ontology visually
6. Customize queries and visualization as needed

