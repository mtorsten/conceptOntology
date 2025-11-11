# REST API Documentation

This document describes the REST API interface for the W3C Semantic Web ontology system.

## Starting the API Server

### Development Mode

```bash
# Using Python directly
python src/ontology/api.py

# Using Flask CLI
export FLASK_APP=src/ontology/api.py
flask run --port 8000

# On Windows
set FLASK_APP=src/ontology/api.py
flask run --port 8000
```

The API will be available at `http://localhost:8000`

### Production Mode

For production deployment, use a WSGI server like Gunicorn:

```bash
gunicorn -w 4 -b 0.0.0.0:8000 "src.ontology.api:create_app()"
```

## API Endpoints

### Health Check

**GET /health**

Check the health status of the API service.

**Response:**
```json
{
  "success": true,
  "message": "Service is healthy",
  "data": {
    "status": "healthy",
    "components": {
      "rdf_loader": "initialized",
      "query_engine": "initialized",
      "validator": "initialized"
    },
    "statistics": {
      "loaded_files": 3,
      "queries_executed": 10,
      "validations_run": 2
    }
  }
}
```

### Load Turtle Files

**POST /load**

Load one or more Turtle files into the RDF store.

**Request Body:**
```json
{
  "files": ["ontology/core.ttl", "ontology/extensions.ttl"],
  "validate": true,
  "continue_on_error": false
}
```

**Parameters:**
- `files` (required): Array of file paths to load
- `validate` (optional): Whether to validate Turtle syntax before loading (default: true)
- `continue_on_error` (optional): Whether to continue loading other files if one fails (default: false)

**Response:**
```json
{
  "success": true,
  "message": "Loaded 2 files successfully",
  "data": {
    "successful_files": ["ontology/core.ttl", "ontology/extensions.ttl"],
    "failed_files": [],
    "total_loaded": 2,
    "total_files_in_store": 2
  }
}
```

### Execute SPARQL Query

**POST /query**

Execute a SPARQL query against the loaded RDF data.

**Request Body:**
```json
{
  "query": "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10",
  "timeout": 30.0,
  "output_format": "json"
}
```

**Parameters:**
- `query` (required): SPARQL query string
- `timeout` (optional): Query timeout in seconds
- `output_format` (optional): Output format - "json" or "python" (default: "python")

**Response:**
```json
{
  "success": true,
  "message": "Query executed successfully",
  "data": {
    "results": [],
    "execution_time": 0.123,
    "output_format": "json"
  }
}
```

**Example Queries:**

```sparql
# Select all triples
SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10

# Select all classes
SELECT ?class ?label
WHERE {
  ?class a owl:Class .
  OPTIONAL { ?class rdfs:label ?label }
}

# Select with filter
SELECT ?entity ?property
WHERE {
  ?entity ?property ?value .
  FILTER(?property = rdf:type)
}
```

### Run SHACL Validation

**POST /validate**

Run SHACL validation against the loaded RDF data.

**Request Body:**
```json
{
  "shapes_file": "validation/shapes.ttl",
  "output_format": "json"
}
```

**Parameters:**
- `shapes_file` (optional): Path to SHACL shapes file to load
- `output_format` (optional): Output format - "json", "text", or "markdown" (default: "json")

**Response:**
```json
{
  "success": true,
  "message": "Validation completed",
  "data": {
    "conforms": true,
    "timestamp": "2024-11-11T10:30:00",
    "summary": {
      "total_results": 0,
      "violation_count": 0,
      "warning_count": 0,
      "info_count": 0
    },
    "results": []
  }
}
```

### Get Triples

**GET /triples**

Retrieve information about loaded triples.

**Query Parameters:**
- `format` (optional): Output format - "json" or "turtle" (default: "json")
- `limit` (optional): Maximum number of triples to return

**Response:**
```json
{
  "success": true,
  "message": "Retrieved information for 2 loaded files",
  "data": {
    "loaded_files": ["ontology/core.ttl", "ontology/extensions.ttl"],
    "file_count": 2,
    "namespaces": {
      "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
      "rdfs": "http://www.w3.org/2000/01/rdf-schema#",
      "owl": "http://www.w3.org/2002/07/owl#"
    },
    "namespace_count": 3
  }
}
```

### Add Triples

**POST /triples**

Add new triples to the RDF store.

**Request Body:**
```json
{
  "turtle": "@prefix : <http://example.org/> . :entity1 a :Entity .",
  "format": "turtle"
}
```

**Parameters:**
- `turtle` (optional): Turtle-formatted triples to add
- `triples` (optional): Array of triple objects
- `format` (optional): Input format - "turtle" or "json" (default: "json")

**Response:**
```json
{
  "success": true,
  "message": "Triple addition endpoint is available but requires maplib implementation",
  "data": {
    "triples_added": 0,
    "note": "This feature requires maplib API implementation"
  }
}
```

### Delete Triples

**DELETE /triples**

Delete triples from the RDF store.

**Request Body:**
```json
{
  "clear_all": true
}
```

**Parameters:**
- `clear_all` (optional): Clear all triples (default: false)
- `triples` (optional): Array of specific triples to delete

**Response:**
```json
{
  "success": true,
  "message": "All triples cleared",
  "data": {
    "files_cleared": 2
  }
}
```

## Error Responses

All error responses follow this format:

```json
{
  "success": false,
  "error": {
    "type": "ValidationError",
    "message": "Query is required",
    "timestamp": "2024-11-11T10:30:00",
    "details": "Additional error details if available"
  }
}
```

**Common Error Types:**
- `ValidationError` - Invalid request parameters
- `InitializationError` - Component not initialized
- `LoadError` - Failed to load files
- `QueryError` - Query execution failed
- `QuerySyntaxError` - Invalid SPARQL syntax
- `QueryTimeoutError` - Query exceeded timeout
- `NotFoundError` - Endpoint not found (404)
- `MethodNotAllowedError` - HTTP method not allowed (405)
- `InternalServerError` - Unexpected server error (500)

## HTTP Status Codes

- `200 OK` - Request successful
- `207 Multi-Status` - Partial success (some files failed to load)
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Endpoint not found
- `405 Method Not Allowed` - HTTP method not allowed
- `500 Internal Server Error` - Server error

## CORS Support

The API has CORS enabled for all routes, allowing cross-origin requests from web applications.

## Example Usage with cURL

```bash
# Health check
curl http://localhost:8000/health

# Load files
curl -X POST http://localhost:8000/load \
  -H "Content-Type: application/json" \
  -d '{"files": ["ontology/core.ttl"]}'

# Execute query
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10"}'

# Run validation
curl -X POST http://localhost:8000/validate \
  -H "Content-Type: application/json" \
  -d '{"shapes_file": "validation/shapes.ttl"}'

# Get triples
curl http://localhost:8000/triples

# Clear all triples
curl -X DELETE http://localhost:8000/triples \
  -H "Content-Type: application/json" \
  -d '{"clear_all": true}'
```

## Example Usage with Python

```python
import requests

# Base URL
base_url = "http://localhost:8000"

# Health check
response = requests.get(f"{base_url}/health")
print(response.json())

# Load files
response = requests.post(
    f"{base_url}/load",
    json={"files": ["ontology/core.ttl", "ontology/extensions.ttl"]}
)
print(response.json())

# Execute query
response = requests.post(
    f"{base_url}/query",
    json={"query": "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10"}
)
print(response.json())

# Run validation
response = requests.post(
    f"{base_url}/validate",
    json={"shapes_file": "validation/shapes.ttl"}
)
print(response.json())
```

## Testing

Run the test suite:

```bash
python test_api.py
```

This will test all endpoints and verify proper error handling.
