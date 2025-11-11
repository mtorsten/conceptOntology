# Implementation Plan

- [x] 1. Set up project structure and dependencies





  - Create directory structure for ontology files, validation shapes, data, and Python source code
  - Create requirements.txt with maplib and other Python dependencies
  - Create .gitignore for Python and Docker artifacts
  - _Requirements: 1.1, 5.1_

- [x] 2. Create sample ontology files in Turtle format





  - Write core.ttl with base classes and properties following RDF 1.2 and OWL standards
  - Define namespace prefixes (rdf, rdfs, owl, xsd) in all Turtle files
  - Create extensions.ttl for domain-specific vocabulary
  - _Requirements: 1.1, 1.2, 1.3, 1.4_

- [x] 3. Create SHACL validation shapes





  - Write shapes.ttl with NodeShape and PropertyShape definitions
  - Define constraint components (minCount, maxCount, datatype, pattern)
  - Add severity levels and validation messages to shapes
  - _Requirements: 2.1, 2.2, 2.5_

- [x] 4. Implement RDF loader module with maplib





  - Create ontology/loader.py with functions to load Turtle files using maplib
  - Implement Turtle syntax validation before loading
  - Add namespace prefix management and resolution
  - Implement multi-file loading with graph merging
  - Add error handling for syntax errors and missing files
  - _Requirements: 1.1, 1.2, 1.5, 4.1, 4.2, 4.3, 5.1, 5.2_

- [ ]* 4.1 Write unit tests for RDF loader
  - Test valid Turtle file loading
  - Test syntax error handling
  - Test multiple file loading and namespace resolution
  - _Requirements: 1.5, 4.1, 4.2_

- [x] 5. Implement SPARQL query engine with maplib





  - Create ontology/query.py with SPARQL query execution using maplib
  - Support SELECT, CONSTRUCT, ASK, and DESCRIBE query forms
  - Implement query timeout mechanism (5 seconds for <10k triples)
  - Add support for FILTER expressions and OPTIONAL patterns
  - Return results in JSON and Turtle formats
  - Add error handling for invalid queries and timeouts
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5, 5.3, 5.4_

- [ ]* 5.1 Write unit tests for SPARQL queries
  - Test SELECT, CONSTRUCT, ASK, DESCRIBE queries
  - Test FILTER and OPTIONAL patterns
  - Test query timeout and error handling
  - _Requirements: 3.1, 3.2, 3.4, 3.5_

- [x] 6. Implement SHACL validator with maplib





  - Create ontology/validator.py with SHACL validation using maplib
  - Load SHACL shapes from Turtle files
  - Execute validation and generate RDF validation reports
  - Include focus node, result path, and constraint details in reports
  - Categorize results by severity (Violation, Warning, Info)
  - Generate summary statistics for validation results
  - Serialize validation reports in Turtle format
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 5.5, 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ]* 6.1 Write unit tests for SHACL validation
  - Test constraint violation detection
  - Test severity level assignment
  - Test validation report generation
  - _Requirements: 2.3, 2.4, 6.1, 6.2, 6.3_

- [x] 7. Implement REST API interface





  - Create ontology/api.py with Flask or FastAPI framework
  - Implement POST /load endpoint for loading Turtle files
  - Implement POST /query endpoint for SPARQL queries
  - Implement POST /validate endpoint for SHACL validation
  - Implement GET /triples, POST /triples, DELETE /triples endpoints
  - Implement GET /health endpoint for health checks
  - Add error handling and status codes for all endpoints
  - Return success/failure indicators in API responses
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5, 5.6_

- [ ]* 7.1 Write integration tests for API endpoints
  - Test all API endpoints with valid and invalid inputs
  - Test error responses and status codes
  - _Requirements: 5.6_

- [x] 8. Create Dockerfile for Python API service





  - Write Dockerfile with Python 3.11+ base image
  - Install maplib and other dependencies from requirements.txt
  - Copy source code and set working directory
  - Expose API port (8000)
  - Set entrypoint to start API service
  - Configure non-root user for security
  - _Requirements: 7.1, 7.4_

- [x] 9. Create docker-compose.yml for service orchestration






  - Define ontology-api service with build context and volume mounts
  - Define graph-explorer service using Data Treehouse image
  - Configure shared volumes for ontology, data, validation, and output directories
  - Set up internal bridge network for service communication
  - Expose ports for API (8000) and graph explorer (3000)
  - Configure automatic ontology loading on container start
  - Add volume configuration for data persistence across restarts
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 8.4, 8.5_

- [x] 10. Configure Data Treehouse graph explorer integration













  - Configure graph explorer to connect to Python API endpoint
  - Set up environment variables for API URL and connection settings
  - Ensure graph explorer can query RDF data through the API
  - Configure visualization settings for ontology structure display
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5_

- [ ] 11. Create sample instance data
  - Write instances.ttl with example RDF instances
  - Create examples.ttl with test data for validation
  - Ensure instances reference classes and properties from core ontology
  - _Requirements: 1.1, 4.3_

- [x] 12. Implement automatic ontology loading on startup






  - Add initialization script to load ontology files when container starts
  - Load core.ttl, extensions.ttl, and shapes.ttl automatically
  - Log loading status and any errors during startup
  - _Requirements: 4.3, 7.3_

- [x] 13. Create README with setup and usage instructions





  - Document Docker Desktop requirement
  - Provide docker-compose up command for starting services
  - Document API endpoints and usage examples
  - Provide SPARQL query examples
  - Document how to access graph explorer at localhost:3000
  - Include troubleshooting section
  - _Requirements: 7.1, 7.2, 8.4_

- [ ]* 14. Write end-to-end integration tests
  - Test complete workflow: load ontology → query → validate
  - Test Docker container startup and service communication
  - Test data persistence across container restarts
  - Test graph explorer connectivity
  - _Requirements: 4.3, 7.3, 7.5, 8.4_
