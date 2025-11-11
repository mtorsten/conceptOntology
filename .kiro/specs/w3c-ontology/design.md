# Design Document: W3C Semantic Web Ontology System

## Overview

This design document outlines the architecture for a W3C standards-compliant ontology system built on RDF 1.2, SPARQL, SHACL, and Turtle serialization. The system leverages Python with the maplib library for programmatic RDF operations and is containerized using Docker for consistent deployment. The Data Treehouse graph explorer provides interactive visualization capabilities.

### Key Technologies

- **RDF 1.2**: Resource Description Framework for semantic data modeling
- **Turtle**: Terse RDF Triple Language for human-readable serialization
- **SPARQL 1.1**: Query language for RDF data
- **SHACL**: Shapes Constraint Language for validation
- **Python 3.11+**: Primary programming language
- **maplib**: Python library for RDF triple manipulation, SPARQL queries, and SHACL validation
- **Docker & Docker Compose**: Containerization and orchestration
- **Data Treehouse Graph Explorer**: Web-based ontology visualization tool

## Architecture

### System Components

```
┌─────────────────────────────────────────────────────────────┐
│                     Docker Environment                       │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │           Python API Service (maplib)                  │ │
│  │  ┌──────────────┐  ┌──────────────┐  ┌─────────────┐ │ │
│  │  │ RDF Loader   │  │ SPARQL Query │  │   SHACL     │ │ │
│  │  │   Module     │  │   Engine     │  │ Validator   │ │ │
│  │  └──────────────┘  └──────────────┘  └─────────────┘ │ │
│  │         │                  │                 │         │ │
│  │         └──────────────────┴─────────────────┘         │ │
│  │                           │                            │ │
│  │                    ┌──────▼──────┐                     │ │
│  │                    │  RDF Store  │                     │ │
│  │                    │  (In-Memory │                     │ │
│  │                    │   or File)  │                     │ │
│  │                    └─────────────┘                     │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │        Data Treehouse Graph Explorer Service           │ │
│  │                 (Web UI - Port 3000)                    │ │
│  └────────────────────────────────────────────────────────┘ │
│                                                              │
│  ┌────────────────────────────────────────────────────────┐ │
│  │              Shared Volumes                             │ │
│  │  - /ontology (Turtle files)                            │ │
│  │  - /data (RDF instances)                               │ │
│  │  - /validation (SHACL shapes)                          │ │
│  └────────────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

### Component Interactions

1. **Turtle Files → Python API**: Ontology definitions loaded via maplib
2. **Python API → RDF Store**: Triples stored in memory or persisted to file
3. **SPARQL Queries → Python API**: Query execution through maplib
4. **SHACL Validation → Python API**: Constraint checking via maplib
5. **Graph Explorer → Python API**: Visualization queries RDF data
6. **Docker Volumes**: Persistent storage for ontology files and data

## Components and Interfaces

### 1. Python API Service

The core service built with Python and maplib that handles all RDF operations.

#### Modules

**RDF Loader Module** (`ontology/loader.py`)
- Loads Turtle files from the file system
- Parses and validates Turtle syntax
- Populates the RDF store using maplib
- Handles namespace prefix management
- Supports incremental loading of multiple files

**SPARQL Query Engine** (`ontology/query.py`)
- Executes SPARQL SELECT, CONSTRUCT, ASK, DESCRIBE queries
- Uses maplib's SPARQL capabilities
- Returns results in JSON, Turtle, or Python objects
- Implements query timeout and error handling
- Supports parameterized queries

**SHACL Validator** (`ontology/validator.py`)
- Loads SHACL shapes from Turtle files
- Executes validation against RDF data using maplib
- Generates validation reports in RDF format
- Categorizes violations by severity (Violation, Warning, Info)
- Provides summary statistics

**API Interface** (`ontology/api.py`)
- RESTful API endpoints for external access
- Endpoints:
  - `POST /load` - Load Turtle files
  - `POST /query` - Execute SPARQL queries
  - `POST /validate` - Run SHACL validation
  - `GET /triples` - Retrieve all triples
  - `POST /triples` - Add new triples
  - `DELETE /triples` - Remove triples
  - `GET /health` - Health check

### 2. RDF Store

The storage layer for RDF triples, managed by maplib.

**Storage Options**:
- **In-Memory**: Fast access, suitable for development and small datasets
- **File-Based**: Persistent storage using Turtle serialization
- **Hybrid**: In-memory with periodic file snapshots

**Capabilities**:
- Triple insertion, deletion, and updates
- Graph merging from multiple sources
- Namespace management
- Export to Turtle format

### 3. Data Treehouse Graph Explorer

Web-based visualization interface for exploring the ontology.

**Features**:
- Interactive graph visualization
- Node and edge exploration
- Class hierarchy browsing
- Property relationship display
- Search and filter capabilities

**Integration**:
- Connects to Python API via HTTP
- Queries RDF data using SPARQL through the API
- Displays validation results
- Supports custom styling for different node types

### 4. Docker Infrastructure

**Services**:
1. **ontology-api**: Python API service
2. **graph-explorer**: Data Treehouse visualization UI

**Volumes**:
- `./ontology:/app/ontology` - Ontology Turtle files
- `./data:/app/data` - Instance data
- `./validation:/app/validation` - SHACL shapes
- `./output:/app/output` - Validation reports and exports

**Networks**:
- Internal bridge network for service communication
- Exposed ports for external access

## Data Models

### Ontology Structure

The ontology will be organized into modular Turtle files:

**1. Core Ontology** (`ontology/core.ttl`)
```turtle
@prefix : <http://example.org/ontology#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix owl: <http://www.w3.org/2002/07/owl#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .

: a owl:Ontology ;
    rdfs:label "Example Ontology" ;
    rdfs:comment "Core ontology definitions" .

# Classes
:Entity a owl:Class ;
    rdfs:label "Entity" ;
    rdfs:comment "Base class for all entities" .

# Properties
:hasProperty a owl:ObjectProperty ;
    rdfs:label "has property" ;
    rdfs:domain :Entity ;
    rdfs:range :Entity .
```

**2. SHACL Shapes** (`validation/shapes.ttl`)
```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix : <http://example.org/ontology#> .

:EntityShape a sh:NodeShape ;
    sh:targetClass :Entity ;
    sh:property [
        sh:path :hasProperty ;
        sh:minCount 1 ;
        sh:severity sh:Violation ;
        sh:message "Entity must have at least one property" ;
    ] .
```

**3. Instance Data** (`data/instances.ttl`)
```turtle
@prefix : <http://example.org/ontology#> .

:instance1 a :Entity ;
    :hasProperty :instance2 .
```

### File Organization

```
project/
├── ontology/
│   ├── core.ttl           # Core classes and properties
│   ├── extensions.ttl     # Domain-specific extensions
│   └── imports.ttl        # External ontology imports
├── validation/
│   ├── shapes.ttl         # SHACL constraint definitions
│   └── custom-rules.ttl   # Custom validation rules
├── data/
│   ├── instances.ttl      # RDF instance data
│   └── examples.ttl       # Example data for testing
├── src/
│   └── ontology/
│       ├── __init__.py
│       ├── loader.py      # RDF loading module
│       ├── query.py       # SPARQL query engine
│       ├── validator.py   # SHACL validation
│       └── api.py         # REST API interface
├── docker-compose.yml
├── Dockerfile
├── requirements.txt
└── README.md
```

## Error Handling

### RDF Loading Errors

**Syntax Errors**:
- Catch Turtle parsing exceptions from maplib
- Log the file name, line number, and error description
- Return detailed error messages to the caller
- Continue loading other files if one fails (optional)

**Namespace Resolution Errors**:
- Validate all prefix declarations
- Check for undefined prefixes in URIs
- Provide suggestions for common namespace typos

### SPARQL Query Errors

**Query Syntax Errors**:
- Validate SPARQL syntax before execution
- Return parse error details with position information
- Suggest corrections for common mistakes

**Query Timeout**:
- Implement configurable timeout (default: 30 seconds)
- Cancel long-running queries gracefully
- Return partial results if available

**Empty Results**:
- Distinguish between no matches and query errors
- Return appropriate HTTP status codes (200 vs 404)

### SHACL Validation Errors

**Shape Loading Errors**:
- Validate SHACL shape syntax
- Check for circular dependencies in shapes
- Report malformed constraint definitions

**Validation Execution Errors**:
- Handle missing target nodes gracefully
- Report constraint evaluation failures
- Continue validation even if individual shapes fail

### Docker and Service Errors

**Container Startup Failures**:
- Check for port conflicts
- Validate volume mount paths
- Ensure required environment variables are set

**Service Communication Errors**:
- Implement retry logic with exponential backoff
- Health check endpoints for service monitoring
- Graceful degradation if graph explorer is unavailable

## Testing Strategy

### Unit Tests

**RDF Loader Tests** (`tests/test_loader.py`)
- Valid Turtle file loading
- Syntax error handling
- Multiple file loading and merging
- Namespace prefix resolution
- Empty file handling

**SPARQL Query Tests** (`tests/test_query.py`)
- SELECT query execution
- CONSTRUCT query results
- ASK query boolean returns
- DESCRIBE query output
- Query with FILTER expressions
- Query with OPTIONAL patterns
- Invalid query syntax handling

**SHACL Validation Tests** (`tests/test_validator.py`)
- Valid data passes validation
- Constraint violations detected
- Severity levels correctly assigned
- Validation report generation
- Multiple shape evaluation
- Custom constraint functions

### Integration Tests

**API Integration Tests** (`tests/test_api.py`)
- Load ontology via API endpoint
- Execute queries through API
- Trigger validation via API
- Add/delete triples through API
- Error responses for invalid requests

**Docker Integration Tests** (`tests/test_docker.py`)
- Container builds successfully
- Services start and communicate
- Volumes mount correctly
- Graph explorer connects to API
- Data persists across container restarts

### End-to-End Tests

**Complete Workflow Tests** (`tests/test_e2e.py`)
- Load ontology → Query data → Validate instances
- Add new instances → Validate → Query results
- Load SHACL shapes → Validate → Generate report
- Visualize in graph explorer → Navigate relationships

### Test Data

**Fixtures** (`tests/fixtures/`)
- Sample ontology files (valid and invalid)
- SHACL shape examples
- Instance data for testing
- Expected query results
- Validation report examples

### Testing Tools

- **pytest**: Test framework
- **pytest-docker**: Docker container testing
- **requests**: API endpoint testing
- **maplib**: Direct RDF operations for test setup

## Performance Considerations

### RDF Store Optimization

- Use in-memory storage for datasets under 100,000 triples
- Implement lazy loading for large ontologies
- Cache frequently accessed triples
- Index by subject, predicate, and object for fast lookups

### Query Optimization

- Implement query result caching with TTL
- Optimize common query patterns
- Use LIMIT clauses to prevent large result sets
- Profile slow queries and add indexes

### Validation Optimization

- Validate only changed data when possible
- Parallelize independent shape evaluations
- Cache validation results for unchanged data
- Provide incremental validation mode

### Docker Optimization

- Use multi-stage builds to minimize image size
- Implement health checks for faster startup detection
- Use volume caching for dependencies
- Configure resource limits appropriately

## Security Considerations

### Input Validation

- Sanitize all file paths to prevent directory traversal
- Validate Turtle syntax before processing
- Limit file sizes to prevent DoS attacks
- Restrict SPARQL query complexity

### API Security

- Implement authentication for API endpoints (optional)
- Rate limiting to prevent abuse
- CORS configuration for graph explorer access
- Input validation for all API parameters

### Docker Security

- Run containers as non-root user
- Use read-only file systems where possible
- Limit container capabilities
- Scan images for vulnerabilities

## Deployment

### Local Development

```bash
# Build and start services
docker-compose up --build

# Access graph explorer
http://localhost:3000

# Access API
http://localhost:8000
```

### Production Considerations

- Use environment variables for configuration
- Implement logging and monitoring
- Set up automated backups for RDF data
- Configure reverse proxy for HTTPS
- Implement CI/CD pipeline for updates

## Future Enhancements

- Support for additional RDF serialization formats (JSON-LD, N-Triples)
- Advanced SPARQL features (federation, property paths)
- Custom SHACL constraint components
- Real-time validation on data changes
- Multi-user collaboration features
- Version control for ontology changes
- Export to OWL/XML for tool compatibility
- Integration with external triple stores (Apache Jena, Virtuoso)
