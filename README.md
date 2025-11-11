# W3C Semantic Web Ontology System

A W3C standards-compliant ontology system built on RDF 1.2, SPARQL, SHACL, and Turtle serialization. This system provides a complete semantic web infrastructure with Python APIs, SPARQL querying, SHACL validation, and interactive graph visualization.

## Features

- **RDF 1.2 Ontology**: Structured vocabulary with classes and properties in Turtle format
- **SPARQL 1.1 Queries**: Full support for SELECT, CONSTRUCT, ASK, and DESCRIBE queries
- **SHACL Validation**: Constraint-based validation with detailed reports
- **REST API**: Python-based API for programmatic access to all features
- **Graph Visualization**: Interactive exploration using Data Treehouse Graph Explorer
- **Apache Jena Fuseki**: Production-grade SPARQL server with TDB2 persistence
- **Docker Deployment**: Containerized services for consistent execution

## Prerequisites

- **Docker Desktop** (required)
  - Download from: https://www.docker.com/products/docker-desktop
  - Ensure Docker Desktop is running before starting services
  - Minimum 4GB RAM allocated to Docker recommended

## Quick Start

### 1. Start All Services

```bash
docker-compose up --build
```

This command will:
- Build the Python API service
- Start Apache Jena Fuseki SPARQL server
- Load ontology files (core.ttl and extensions.ttl) into Fuseki's TDB2 database
- Launch the Graph Explorer web interface

**Note**: The first startup may take a few minutes as it builds images and loads data into Fuseki.

### 2. Access the Services

Once all services are running (wait for health checks to pass):

- **Graph Explorer**: http://localhost:3000
  - Interactive visualization of the ontology
  - Browse classes, properties, and relationships
  - Execute SPARQL queries through the UI

- **Python API**: http://localhost:8000
  - RESTful endpoints for RDF operations
  - API documentation: http://localhost:8000/health

- **Fuseki SPARQL Endpoint**: http://localhost:3030
  - Web UI for SPARQL queries
  - Dataset name: `/ontology`
  - Query endpoint: http://localhost:3030/ontology/sparql
  - Admin credentials: username `admin`, password `admin123`

### 3. Stop Services

```bash
docker-compose down
```

To remove all data and volumes:

```bash
docker-compose down -v
```

## Project Structure

```
.
├── ontology/              # Ontology definitions in Turtle format
│   ├── core.ttl          # Core classes and properties
│   └── extensions.ttl    # Domain-specific extensions
├── validation/           # SHACL validation shapes
│   └── shapes.ttl       # Constraint definitions
├── data/                # RDF instance data
├── output/              # Validation reports and exports
├── src/ontology/        # Python source code
│   ├── loader.py        # RDF loading module
│   ├── query.py         # SPARQL query engine
│   ├── validator.py     # SHACL validation
│   ├── api.py           # REST API interface
│   └── startup.py       # Automatic ontology loading
├── docker-compose.yml   # Service orchestration
├── Dockerfile          # Python API container
└── requirements.txt    # Python dependencies
```

## API Endpoints

### Health Check

```bash
GET http://localhost:8000/health
```

Returns service status and statistics.

### Load Turtle Files

```bash
POST http://localhost:8000/load
Content-Type: application/json

{
  "files": ["ontology/core.ttl", "ontology/extensions.ttl"],
  "validate": true
}
```

### Execute SPARQL Query

```bash
POST http://localhost:8000/query
Content-Type: application/json

{
  "query": "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10",
  "timeout": 30.0,
  "output_format": "json"
}
```

Or using standard SPARQL protocol:

```bash
POST http://localhost:8000/query
Content-Type: application/x-www-form-urlencoded

query=SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10
```

### Run SHACL Validation

```bash
POST http://localhost:8000/validate
Content-Type: application/json

{
  "shapes_file": "validation/shapes.ttl",
  "output_format": "json"
}
```

### Get Triples Information

```bash
GET http://localhost:8000/triples?limit=10
```

### Clear All Data

```bash
DELETE http://localhost:8000/triples
Content-Type: application/json

{
  "clear_all": true
}
```

## SPARQL Query Examples

### Example 1: List All Classes

```sparql
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl: <http://www.w3.org/2002/07/owl#>

SELECT ?class ?label ?comment
WHERE {
  ?class a owl:Class .
  OPTIONAL { ?class rdfs:label ?label }
  OPTIONAL { ?class rdfs:comment ?comment }
}
ORDER BY ?class
```

### Example 2: Find All Properties of a Class

```sparql
PREFIX : <http://example.org/ontology#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

SELECT ?property ?label ?range
WHERE {
  ?property rdfs:domain :Entity .
  OPTIONAL { ?property rdfs:label ?label }
  OPTIONAL { ?property rdfs:range ?range }
}
```

### Example 3: Query with FILTER

```sparql
PREFIX : <http://example.org/ontology#>
PREFIX ext: <http://example.org/ontology/extensions#>

SELECT ?person ?name ?email
WHERE {
  ?person a ext:Person ;
          :hasName ?name ;
          ext:email ?email .
  FILTER (CONTAINS(?email, "@example.com"))
}
```

### Example 4: CONSTRUCT Query

```sparql
PREFIX : <http://example.org/ontology#>
PREFIX ext: <http://example.org/ontology/extensions#>

CONSTRUCT {
  ?person :worksFor ?org .
  ?org :hasEmployee ?person .
}
WHERE {
  ?person ext:worksFor ?org .
}
```

### Example 5: ASK Query

```sparql
PREFIX : <http://example.org/ontology#>
PREFIX ext: <http://example.org/ontology/extensions#>

ASK {
  ?person a ext:Person ;
          ext:email ?email .
}
```

### Example 6: Query with OPTIONAL

```sparql
PREFIX : <http://example.org/ontology#>
PREFIX ext: <http://example.org/ontology/extensions#>

SELECT ?person ?name ?email ?phone
WHERE {
  ?person a ext:Person ;
          :hasName ?name .
  OPTIONAL { ?person ext:email ?email }
  OPTIONAL { ?person ext:phoneNumber ?phone }
}
```

## Using the Graph Explorer

1. **Access the Interface**: Navigate to http://localhost:3000

2. **Connection**: The Graph Explorer connects to Fuseki at `http://localhost:3030/ontology/sparql`

3. **Execute Queries**: 
   - Use the query editor to write SPARQL queries
   - Click "Execute" to run the query
   - Results appear in the visualization panel

4. **Navigate the Graph**:
   - Click on nodes to expand relationships
   - Use zoom and pan controls to navigate
   - Filter by class type using the sidebar

5. **Explore Classes**:
   - Browse the class hierarchy
   - View properties and relationships
   - Inspect instance data

**Note**: If you see a "NetworkError", ensure Fuseki is running and accessible at http://localhost:3030

## Validation

The system includes comprehensive SHACL validation shapes for data quality:

### Run Validation via API

```bash
curl -X POST http://localhost:8000/validate \
  -H "Content-Type: application/json" \
  -d '{"shapes_file": "validation/shapes.ttl"}'
```

### Run Validation via Python

```python
from ontology.validator import SHACLValidator
from ontology.loader import RDFLoader

# Load ontology
loader = RDFLoader()
loader.load_files(["ontology/core.ttl", "data/instances.ttl"])

# Run validation
validator = SHACLValidator(loader)
validator.load_shapes("validation/shapes.ttl")
report = validator.validate()

# Print results
print(f"Conforms: {report.conforms}")
print(f"Violations: {len(report.get_violations())}")
```

### Validation Report Format

```json
{
  "success": true,
  "message": "Validation completed with 2 violations",
  "data": {
    "conforms": false,
    "summary": {
      "total_results": 2,
      "violation_count": 2,
      "warning_count": 0,
      "info_count": 0
    },
    "results": [
      {
        "focus_node": "http://example.org/ontology#entity1",
        "result_path": "http://example.org/ontology#hasIdentifier",
        "severity": "Violation",
        "message": "Entity must have exactly one non-empty identifier"
      }
    ]
  }
}
```

## Development

### Running Tests

```bash
# Run all tests
python -m pytest

# Run specific test file
python -m pytest test_api.py

# Run with coverage
python -m pytest --cov=src/ontology
```

### Adding New Ontology Classes

1. Edit `ontology/extensions.ttl`:

```turtle
@prefix : <http://example.org/ontology#>
@prefix ext: <http://example.org/ontology/extensions#>

ext:MyNewClass a owl:Class ;
    rdfs:subClassOf :Entity ;
    rdfs:label "My New Class"@en ;
    rdfs:comment "Description of the new class"@en .
```

2. Add SHACL validation in `validation/shapes.ttl`:

```turtle
ext:MyNewClassShape a sh:NodeShape ;
    sh:targetClass ext:MyNewClass ;
    sh:property [
        sh:path :hasIdentifier ;
        sh:minCount 1 ;
        sh:severity sh:Violation ;
    ] .
```

3. Restart services to load changes:

```bash
docker-compose restart
```

## Troubleshooting

### Services Won't Start

**Problem**: Docker containers fail to start

**Solutions**:
- Ensure Docker Desktop is running
- Check port availability (3000, 3030, 8000)
- Review logs: `docker-compose logs`
- Try rebuilding: `docker-compose up --build --force-recreate`

### Port Already in Use

**Problem**: Error message about ports 3000, 3030, or 8000 being in use

**Solutions**:
- Stop other services using these ports
- Change ports in `docker-compose.yml`:
  ```yaml
  ports:
    - "8001:8000"  # Change host port
  ```

### Graph Explorer Not Loading

**Problem**: Graph Explorer shows blank page or connection error

**Solutions**:
- Wait for all services to pass health checks (30-60 seconds)
- Check API is running: `curl http://localhost:8000/health`
- Check Fuseki is running: `curl http://localhost:3030/$/ping`
- Review logs: `docker-compose logs graph-explorer`
- Verify network connectivity: `docker network inspect ontology-network`

### SPARQL Queries Return No Results

**Problem**: Queries execute but return empty results

**Solutions**:
- Verify ontology files are loaded: `curl http://localhost:8000/triples`
- Check for syntax errors in Turtle files
- Ensure correct namespace prefixes in queries
- Load data manually: `curl -X POST http://localhost:8000/load -H "Content-Type: application/json" -d '{"files": ["ontology/core.ttl"]}'`

### Validation Fails to Load Shapes

**Problem**: SHACL validation returns "No shapes loaded" error

**Solutions**:
- Verify shapes file exists: `ls validation/shapes.ttl`
- Check Turtle syntax in shapes file
- Load shapes explicitly in API call:
  ```json
  {
    "shapes_file": "validation/shapes.ttl"
  }
  ```

### Container Memory Issues

**Problem**: Services crash or become unresponsive

**Solutions**:
- Increase Docker memory allocation (Docker Desktop → Settings → Resources)
- Reduce dataset size for testing
- Adjust JVM memory in `docker-compose.yml`:
  ```yaml
  environment:
    - JVM_ARGS=-Xmx4g -Xms2g
  ```

### Permission Denied Errors

**Problem**: Cannot write to output directory or mount volumes

**Solutions**:
- Check directory permissions: `ls -la output/`
- Create directories if missing: `mkdir -p output data`
- On Linux, adjust ownership: `sudo chown -R $USER:$USER output data`

### API Returns 500 Internal Server Error

**Problem**: API endpoints return server errors

**Solutions**:
- Check API logs: `docker-compose logs ontology-api`
- Verify Python dependencies are installed
- Restart API service: `docker-compose restart ontology-api`
- Check for syntax errors in Python code

### Data Not Persisting

**Problem**: Data is lost when containers restart

**Solutions**:
- Verify volumes are configured in `docker-compose.yml`
- Check volume mounts: `docker volume ls`
- Don't use `docker-compose down -v` unless you want to delete data
- Use `docker-compose restart` instead of `down` and `up`

### Fuseki Admin UI Not Accessible

**Problem**: Cannot access Fuseki at http://localhost:3030

**Solutions**:
- Check Fuseki container is running: `docker ps`
- Verify health check: `docker-compose ps`
- Check logs: `docker-compose logs fuseki`
- Try default credentials: username `admin`, password `admin123`

## Advanced Configuration

### Custom SPARQL Endpoint

To use a different SPARQL endpoint in Graph Explorer, edit `docker-compose.yml`:

```yaml
graph-explorer:
  environment:
    - ENDPOINT_URL=http://your-sparql-endpoint:3030/dataset/sparql
```

### Enable Query Logging

Add to `docker-compose.yml` under `ontology-api`:

```yaml
environment:
  - LOG_LEVEL=DEBUG
  - QUERY_LOGGING=true
```

### Persistent Data Storage

Volumes are automatically configured for persistence. To backup data:

```bash
# Backup Fuseki database
docker cp fuseki:/fuseki ./fuseki-backup

# Backup output files
cp -r output output-backup
```

## Performance Tips

- **Large Datasets**: Use Fuseki directly for better performance with >100k triples
- **Query Optimization**: Add LIMIT clauses to prevent large result sets
- **Caching**: Enable query result caching in production
- **Indexing**: Fuseki automatically indexes data for fast queries

## Additional Resources

- [RDF 1.2 Specification](https://www.w3.org/TR/rdf12-concepts/)
- [SPARQL 1.1 Query Language](https://www.w3.org/TR/sparql11-query/)
- [SHACL Specification](https://www.w3.org/TR/shacl/)
- [Turtle Syntax](https://www.w3.org/TR/turtle/)
- [Apache Jena Fuseki](https://jena.apache.org/documentation/fuseki2/)

## License

This project is provided as-is for educational and development purposes.

## Support

For issues and questions:
1. Check the troubleshooting section above
2. Review Docker logs: `docker-compose logs`
3. Verify service health: `curl http://localhost:8000/health`
