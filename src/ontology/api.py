"""
REST API Interface Module

This module provides a RESTful API interface for the W3C Semantic Web ontology system.
It exposes endpoints for loading Turtle files, executing SPARQL queries, running SHACL
validation, and managing RDF triples.

Example Usage:
    # Run the API server
    python -m ontology.api
    
    # Or use Flask CLI
    flask --app ontology.api run --port 8000
    
    # API Endpoints:
    # POST /load - Load Turtle files
    # POST /query - Execute SPARQL queries
    # POST /validate - Run SHACL validation
    # GET /triples - Retrieve all triples
    # POST /triples - Add new triples
    # DELETE /triples - Remove triples
    # GET /health - Health check
"""

import logging
import traceback
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime

from flask import Flask, request, jsonify, Response
from flask_cors import CORS

try:
    from ontology.loader import RDFLoader, load_ontology_files
    from ontology.query import SPARQLQueryEngine
    from ontology.validator import SHACLValidator
except ImportError:
    # Handle case when running as script
    import sys
    sys.path.insert(0, str(Path(__file__).parent.parent))
    from ontology.loader import RDFLoader, load_ontology_files
    from ontology.query import SPARQLQueryEngine
    from ontology.validator import SHACLValidator


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes


# Global instances
rdf_loader: Optional[RDFLoader] = None
query_engine: Optional[SPARQLQueryEngine] = None
validator: Optional[SHACLValidator] = None


def initialize_components():
    """Initialize RDF loader, query engine, and validator."""
    global rdf_loader, query_engine, validator
    
    logger.info("Initializing API components")
    
    # Initialize RDF loader
    rdf_loader = RDFLoader()
    
    # Initialize query engine
    query_engine = SPARQLQueryEngine(rdf_loader)
    
    # Initialize validator
    validator = SHACLValidator(rdf_loader)
    
    logger.info("API components initialized successfully")


def create_success_response(
    message: str,
    data: Optional[Dict[str, Any]] = None,
    status_code: int = 200
) -> tuple:
    """
    Create a standardized success response.
    
    Args:
        message: Success message
        data: Optional data payload
        status_code: HTTP status code
    
    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {
        'success': True,
        'message': message,
        'timestamp': datetime.now().isoformat()
    }
    
    if data is not None:
        response['data'] = data
    
    return jsonify(response), status_code


def create_error_response(
    message: str,
    error_type: str = "Error",
    details: Optional[str] = None,
    status_code: int = 400
) -> tuple:
    """
    Create a standardized error response.
    
    Args:
        message: Error message
        error_type: Type of error
        details: Optional detailed error information
        status_code: HTTP status code
    
    Returns:
        Tuple of (response_dict, status_code)
    """
    response = {
        'success': False,
        'error': {
            'type': error_type,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
    }
    
    if details is not None:
        response['error']['details'] = details
    
    return jsonify(response), status_code


# ============================================================================
# API Endpoints
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """
    Health check endpoint.
    
    Returns:
        JSON response with service health status
    
    Example:
        GET /health
        
        Response:
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
    """
    try:
        # Check component status
        components_status = {
            'rdf_loader': 'initialized' if rdf_loader else 'not_initialized',
            'query_engine': 'initialized' if query_engine else 'not_initialized',
            'validator': 'initialized' if validator else 'not_initialized'
        }
        
        # Gather statistics
        statistics = {}
        
        if rdf_loader:
            statistics['loaded_files'] = len(rdf_loader.get_loaded_files())
            statistics['namespaces'] = len(rdf_loader.get_namespaces())
        
        if query_engine:
            query_stats = query_engine.get_statistics()
            statistics['queries_executed'] = query_stats['total_queries']
        
        if validator:
            validator_stats = validator.get_statistics()
            statistics['validations_run'] = validator_stats['validation_count']
            statistics['shapes_loaded'] = validator_stats['shapes_loaded']
        
        # Determine overall health
        all_initialized = all(
            status == 'initialized'
            for status in components_status.values()
        )
        
        health_status = 'healthy' if all_initialized else 'degraded'
        
        return create_success_response(
            message='Service is healthy' if all_initialized else 'Service is degraded',
            data={
                'status': health_status,
                'components': components_status,
                'statistics': statistics
            }
        )
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return create_error_response(
            message='Health check failed',
            error_type='HealthCheckError',
            details=str(e),
            status_code=500
        )


@app.route('/load', methods=['POST'])
def load_turtle_files():
    """
    Load Turtle files into the RDF store.
    
    Request Body:
        {
            "files": ["path/to/file1.ttl", "path/to/file2.ttl"],
            "validate": true,
            "continue_on_error": false
        }
    
    Returns:
        JSON response with loading results
    
    Example:
        POST /load
        {
            "files": ["ontology/core.ttl", "ontology/extensions.ttl"]
        }
        
        Response:
        {
            "success": true,
            "message": "Loaded 2 files successfully",
            "data": {
                "successful_files": ["ontology/core.ttl", "ontology/extensions.ttl"],
                "failed_files": [],
                "total_loaded": 2
            }
        }
    """
    try:
        if not rdf_loader:
            return create_error_response(
                message='RDF loader not initialized',
                error_type='InitializationError',
                status_code=500
            )
        
        # Parse request body
        data = request.get_json()
        
        if not data:
            return create_error_response(
                message='Request body is required',
                error_type='ValidationError',
                status_code=400
            )
        
        files = data.get('files', [])
        validate = data.get('validate', True)
        continue_on_error = data.get('continue_on_error', False)
        
        if not files:
            return create_error_response(
                message='No files specified',
                error_type='ValidationError',
                status_code=400
            )
        
        if not isinstance(files, list):
            return create_error_response(
                message='Files must be a list',
                error_type='ValidationError',
                status_code=400
            )
        
        logger.info(f"Loading {len(files)} Turtle files")
        
        # Load files
        successful_files, failed_files = rdf_loader.load_files(
            files,
            validate=validate,
            continue_on_error=continue_on_error
        )
        
        # Update query engine and validator with new data
        if query_engine:
            query_engine.set_rdf_loader(rdf_loader)
        if validator:
            validator.set_rdf_loader(rdf_loader)
        
        message = f"Loaded {len(successful_files)} files successfully"
        if failed_files:
            message += f", {len(failed_files)} files failed"
        
        return create_success_response(
            message=message,
            data={
                'successful_files': successful_files,
                'failed_files': failed_files,
                'total_loaded': len(successful_files),
                'total_files_in_store': len(rdf_loader.get_loaded_files())
            },
            status_code=200 if not failed_files else 207  # 207 Multi-Status
        )
        
    except Exception as e:
        logger.error(f"Error loading files: {str(e)}")
        logger.error(traceback.format_exc())
        return create_error_response(
            message='Failed to load files',
            error_type='LoadError',
            details=str(e),
            status_code=500
        )


@app.route('/query', methods=['GET', 'POST'])
def execute_sparql_query():
    """
    Execute a SPARQL query against the RDF data.
    
    Supports both standard SPARQL protocol and JSON format:
    
    Standard SPARQL Protocol (GET):
        GET /query?query=SELECT+%3Fs+%3Fp+%3Fo+WHERE+%7B+%3Fs+%3Fp+%3Fo+%7D+LIMIT+10
    
    Standard SPARQL Protocol (POST with form data):
        POST /query
        Content-Type: application/x-www-form-urlencoded
        query=SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10
    
    JSON Format (POST):
        POST /query
        Content-Type: application/json
        {
            "query": "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10",
            "timeout": 30.0,
            "output_format": "json"
        }
    
    Returns:
        SPARQL JSON results format or custom JSON response
    
    Example:
        POST /query
        {
            "query": "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 10"
        }
        
        Response (SPARQL JSON format):
        {
            "head": {
                "vars": ["s", "p", "o"]
            },
            "results": {
                "bindings": [...]
            }
        }
    """
    try:
        if not query_engine:
            return create_error_response(
                message='Query engine not initialized',
                error_type='InitializationError',
                status_code=500
            )
        
        # Parse query from different sources
        query = None
        timeout = None
        output_format = 'sparql_json'  # Default to SPARQL JSON format for compatibility
        
        if request.method == 'GET':
            # Standard SPARQL GET request
            query = request.args.get('query')
        elif request.method == 'POST':
            content_type = request.content_type or ''
            
            if 'application/json' in content_type:
                # JSON format
                data = request.get_json()
                if data:
                    query = data.get('query')
                    timeout = data.get('timeout')
                    output_format = data.get('output_format', 'sparql_json')
            elif 'application/x-www-form-urlencoded' in content_type or 'application/sparql-query' in content_type:
                # Standard SPARQL POST with form data or direct query
                query = request.form.get('query') or request.data.decode('utf-8')
            else:
                # Try to parse as form data or raw query
                query = request.form.get('query') or request.data.decode('utf-8')
        
        if not query:
            return create_error_response(
                message='Query is required',
                error_type='ValidationError',
                status_code=400
            )
        
        logger.info(f"Executing SPARQL query (format: {output_format})")
        
        # Execute query
        import time
        start_time = time.time()
        
        results = query_engine.execute(
            query,
            timeout=timeout,
            output_format=output_format,
            validate=True
        )
        
        execution_time = time.time() - start_time
        
        # Format response based on output format
        if output_format == 'sparql_json':
            # Return standard SPARQL JSON results format
            # This is what graph-explorer expects
            return jsonify(results), 200
        else:
            # Return custom format with metadata
            return create_success_response(
                message='Query executed successfully',
                data={
                    'results': results,
                    'execution_time': round(execution_time, 3),
                    'output_format': output_format
                }
            )
        
    except Exception as e:
        logger.error(f"Error executing query: {str(e)}")
        logger.error(traceback.format_exc())
        
        # Determine error type
        error_type = 'QueryError'
        if 'syntax' in str(e).lower():
            error_type = 'QuerySyntaxError'
        elif 'timeout' in str(e).lower():
            error_type = 'QueryTimeoutError'
        
        return create_error_response(
            message='Failed to execute query',
            error_type=error_type,
            details=str(e),
            status_code=400
        )


@app.route('/validate', methods=['POST'])
def run_shacl_validation():
    """
    Run SHACL validation against the RDF data.
    
    Request Body:
        {
            "shapes_file": "validation/shapes.ttl",
            "output_format": "json"
        }
    
    Returns:
        JSON response with validation results
    
    Example:
        POST /validate
        {
            "shapes_file": "validation/shapes.ttl"
        }
        
        Response:
        {
            "success": true,
            "message": "Validation completed",
            "data": {
                "conforms": true,
                "summary": {
                    "total_results": 0,
                    "violation_count": 0,
                    "warning_count": 0
                }
            }
        }
    """
    try:
        if not validator:
            return create_error_response(
                message='Validator not initialized',
                error_type='InitializationError',
                status_code=500
            )
        
        # Parse request body
        data = request.get_json() or {}
        
        shapes_file = data.get('shapes_file')
        output_format = data.get('output_format', 'json')
        
        # Load shapes if specified
        if shapes_file:
            logger.info(f"Loading shapes from: {shapes_file}")
            validator.load_shapes(shapes_file)
        
        # Check if shapes are loaded
        if not validator.get_loaded_shapes():
            return create_error_response(
                message='No SHACL shapes loaded',
                error_type='ValidationError',
                details='Load shapes using the shapes_file parameter or load them beforehand',
                status_code=400
            )
        
        logger.info("Running SHACL validation")
        
        # Execute validation
        report = validator.validate()
        
        # Format response based on output format
        if output_format == 'json':
            response_data = report.to_dict()
        elif output_format == 'text':
            response_data = {
                'report': validator.format_report(report, format='text')
            }
        elif output_format == 'markdown':
            response_data = {
                'report': validator.format_report(report, format='markdown')
            }
        else:
            response_data = report.to_dict()
        
        message = 'Validation completed'
        if not report.conforms:
            message += f" with {len(report.get_violations())} violations"
        
        return create_success_response(
            message=message,
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"Error running validation: {str(e)}")
        logger.error(traceback.format_exc())
        return create_error_response(
            message='Failed to run validation',
            error_type='ValidationError',
            details=str(e),
            status_code=500
        )


@app.route('/triples', methods=['GET'])
def get_triples():
    """
    Retrieve all triples from the RDF store.
    
    Query Parameters:
        - format: Output format (json, turtle) - default: json
        - limit: Maximum number of triples to return
    
    Returns:
        JSON response with triples
    
    Example:
        GET /triples?limit=10
        
        Response:
        {
            "success": true,
            "message": "Retrieved triples",
            "data": {
                "triples": [...],
                "count": 10,
                "total": 1000
            }
        }
    """
    try:
        if not rdf_loader:
            return create_error_response(
                message='RDF loader not initialized',
                error_type='InitializationError',
                status_code=500
            )
        
        # Get query parameters
        output_format = request.args.get('format', 'json')
        limit = request.args.get('limit', type=int)
        
        logger.info("Retrieving triples")
        
        # Get loaded files info
        loaded_files = rdf_loader.get_loaded_files()
        namespaces = rdf_loader.get_namespaces()
        
        response_data = {
            'loaded_files': loaded_files,
            'file_count': len(loaded_files),
            'namespaces': namespaces,
            'namespace_count': len(namespaces)
        }
        
        if limit:
            response_data['limit'] = limit
        
        return create_success_response(
            message=f'Retrieved information for {len(loaded_files)} loaded files',
            data=response_data
        )
        
    except Exception as e:
        logger.error(f"Error retrieving triples: {str(e)}")
        logger.error(traceback.format_exc())
        return create_error_response(
            message='Failed to retrieve triples',
            error_type='RetrievalError',
            details=str(e),
            status_code=500
        )


@app.route('/triples', methods=['POST'])
def add_triples():
    """
    Add new triples to the RDF store.
    
    Request Body:
        {
            "triples": [
                {"subject": "...", "predicate": "...", "object": "..."}
            ],
            "format": "json"
        }
        
        OR
        
        {
            "turtle": "@prefix : <...> . :subject :predicate :object .",
            "format": "turtle"
        }
    
    Returns:
        JSON response with operation result
    
    Example:
        POST /triples
        {
            "turtle": ":entity1 a :Entity ."
        }
        
        Response:
        {
            "success": true,
            "message": "Triples added successfully",
            "data": {
                "triples_added": 1
            }
        }
    """
    try:
        if not rdf_loader:
            return create_error_response(
                message='RDF loader not initialized',
                error_type='InitializationError',
                status_code=500
            )
        
        # Parse request body
        data = request.get_json()
        
        if not data:
            return create_error_response(
                message='Request body is required',
                error_type='ValidationError',
                status_code=400
            )
        
        input_format = data.get('format', 'json')
        
        logger.info(f"Adding triples in {input_format} format")
        
        # Note: This is a placeholder implementation
        # Actual implementation would use maplib to add triples
        logger.warning("Adding triples requires maplib triple addition API implementation")
        
        return create_success_response(
            message='Triple addition endpoint is available but requires maplib implementation',
            data={
                'triples_added': 0,
                'note': 'This feature requires maplib API implementation'
            }
        )
        
    except Exception as e:
        logger.error(f"Error adding triples: {str(e)}")
        logger.error(traceback.format_exc())
        return create_error_response(
            message='Failed to add triples',
            error_type='AdditionError',
            details=str(e),
            status_code=500
        )


@app.route('/triples', methods=['DELETE'])
def delete_triples():
    """
    Delete triples from the RDF store.
    
    Request Body:
        {
            "triples": [
                {"subject": "...", "predicate": "...", "object": "..."}
            ]
        }
        
        OR
        
        {
            "clear_all": true
        }
    
    Returns:
        JSON response with operation result
    
    Example:
        DELETE /triples
        {
            "clear_all": true
        }
        
        Response:
        {
            "success": true,
            "message": "All triples cleared",
            "data": {
                "triples_deleted": 1000
            }
        }
    """
    try:
        if not rdf_loader:
            return create_error_response(
                message='RDF loader not initialized',
                error_type='InitializationError',
                status_code=500
            )
        
        # Parse request body
        data = request.get_json() or {}
        
        clear_all = data.get('clear_all', False)
        
        if clear_all:
            logger.info("Clearing all triples")
            
            # Clear the RDF loader
            files_count = len(rdf_loader.get_loaded_files())
            rdf_loader.clear()
            
            # Update query engine and validator
            if query_engine:
                query_engine.set_rdf_loader(rdf_loader)
            if validator:
                validator.set_rdf_loader(rdf_loader)
                validator.clear_shapes()
            
            return create_success_response(
                message='All triples cleared',
                data={
                    'files_cleared': files_count
                }
            )
        else:
            # Note: This is a placeholder implementation
            # Actual implementation would use maplib to delete specific triples
            logger.warning("Deleting specific triples requires maplib triple deletion API implementation")
            
            return create_success_response(
                message='Triple deletion endpoint is available but requires maplib implementation',
                data={
                    'triples_deleted': 0,
                    'note': 'This feature requires maplib API implementation'
                }
            )
        
    except Exception as e:
        logger.error(f"Error deleting triples: {str(e)}")
        logger.error(traceback.format_exc())
        return create_error_response(
            message='Failed to delete triples',
            error_type='DeletionError',
            details=str(e),
            status_code=500
        )


# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return create_error_response(
        message='Endpoint not found',
        error_type='NotFoundError',
        details=f'The requested endpoint does not exist',
        status_code=404
    )


@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 errors."""
    return create_error_response(
        message='Method not allowed',
        error_type='MethodNotAllowedError',
        details=f'The HTTP method is not allowed for this endpoint',
        status_code=405
    )


@app.errorhandler(500)
def internal_server_error(error):
    """Handle 500 errors."""
    logger.error(f"Internal server error: {str(error)}")
    return create_error_response(
        message='Internal server error',
        error_type='InternalServerError',
        details='An unexpected error occurred',
        status_code=500
    )


# ============================================================================
# Application Initialization
# ============================================================================

def create_app(config: Optional[Dict[str, Any]] = None) -> Flask:
    """
    Create and configure the Flask application.
    
    Args:
        config: Optional configuration dictionary
    
    Returns:
        Configured Flask application
    """
    if config:
        app.config.update(config)
    
    # Initialize components
    initialize_components()
    
    logger.info("Flask application created and configured")
    
    return app


# ============================================================================
# Main Entry Point
# ============================================================================

if __name__ == '__main__':
    # Create application
    create_app()
    
    # Run development server
    logger.info("Starting Flask development server")
    app.run(
        host='0.0.0.0',
        port=8000,
        debug=True
    )
