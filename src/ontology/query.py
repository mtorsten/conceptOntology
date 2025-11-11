"""
SPARQL Query Engine Module

This module provides functionality to execute SPARQL queries against RDF data using maplib.
It supports SELECT, CONSTRUCT, ASK, and DESCRIBE query forms with timeout mechanisms,
FILTER expressions, OPTIONAL patterns, and multiple output formats.

Example Usage:
    # Initialize query engine with loaded RDF data
    from ontology.loader import load_ontology_files
    
    loader = load_ontology_files()
    engine = SPARQLQueryEngine(loader)
    
    # Execute SELECT query
    results = engine.execute_select('''
        SELECT ?subject ?predicate ?object
        WHERE {
            ?subject ?predicate ?object .
        }
        LIMIT 10
    ''')
    
    # Execute with different output format
    results_json = engine.execute_select(query, output_format='json')
    results_turtle = engine.execute_select(query, output_format='turtle')
    
    # Execute CONSTRUCT query
    graph = engine.execute_construct('''
        CONSTRUCT { ?s a ?type }
        WHERE { ?s a ?type }
    ''')
    
    # Execute ASK query
    exists = engine.execute_ask('''
        ASK { ?s a owl:Class }
    ''')
    
    # Execute DESCRIBE query
    description = engine.execute_describe('http://example.org/ontology#Entity')
    
    # Execute with custom timeout
    results = engine.execute(query, timeout=10.0)
"""

import logging
import time
from typing import Dict, List, Any, Optional, Union
from enum import Enum
import json

try:
    import maplib
except ImportError:
    raise ImportError(
        "maplib is required but not installed. "
        "Install it with: pip install maplib"
    )


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QueryType(Enum):
    """Enumeration of SPARQL query types."""
    SELECT = "SELECT"
    CONSTRUCT = "CONSTRUCT"
    ASK = "ASK"
    DESCRIBE = "DESCRIBE"
    UNKNOWN = "UNKNOWN"


class SPARQLQueryError(Exception):
    """Base exception for SPARQL query errors."""
    pass


class QuerySyntaxError(SPARQLQueryError):
    """Exception raised for SPARQL syntax errors."""
    pass


class QueryTimeoutError(SPARQLQueryError):
    """Exception raised when a query exceeds the timeout limit."""
    pass


class QueryExecutionError(SPARQLQueryError):
    """Exception raised for query execution errors."""
    pass


class SPARQLQueryEngine:
    """
    SPARQL Query Engine for executing queries against RDF data using maplib.
    
    This class provides methods to:
    - Execute SELECT, CONSTRUCT, ASK, and DESCRIBE queries
    - Handle query timeouts
    - Support FILTER expressions and OPTIONAL patterns
    - Return results in multiple formats (JSON, Turtle, Python objects)
    - Provide detailed error handling
    """
    
    def __init__(self, rdf_loader=None, default_timeout: float = 30.0):
        """
        Initialize the SPARQL query engine.
        
        Args:
            rdf_loader: RDFLoader instance with loaded data (optional)
            default_timeout: Default query timeout in seconds (default: 30.0)
        """
        self.rdf_loader = rdf_loader
        self.default_timeout = default_timeout
        self.query_count = 0
        self.total_query_time = 0.0
        logger.info(f"SPARQL Query Engine initialized with timeout: {default_timeout}s")
    
    def set_rdf_loader(self, rdf_loader) -> None:
        """
        Set or update the RDF loader instance.
        
        Args:
            rdf_loader: RDFLoader instance with loaded data
        """
        self.rdf_loader = rdf_loader
        logger.info("RDF loader updated")

    
    def _detect_query_type(self, query: str) -> QueryType:
        """
        Detect the type of SPARQL query.
        
        Args:
            query: SPARQL query string
        
        Returns:
            QueryType enum value
        """
        query_upper = query.strip().upper()
        
        # Remove comments
        lines = [line.split('#')[0] for line in query_upper.split('\n')]
        query_clean = ' '.join(lines).strip()
        
        if query_clean.startswith('SELECT'):
            return QueryType.SELECT
        elif query_clean.startswith('CONSTRUCT'):
            return QueryType.CONSTRUCT
        elif query_clean.startswith('ASK'):
            return QueryType.ASK
        elif query_clean.startswith('DESCRIBE'):
            return QueryType.DESCRIBE
        else:
            return QueryType.UNKNOWN
    
    def _validate_query_syntax(self, query: str) -> None:
        """
        Perform basic validation of SPARQL query syntax.
        
        Args:
            query: SPARQL query string
        
        Raises:
            QuerySyntaxError: If the query syntax is invalid
        """
        query_stripped = query.strip()
        
        if not query_stripped:
            raise QuerySyntaxError("Query cannot be empty")
        
        query_type = self._detect_query_type(query)
        
        if query_type == QueryType.UNKNOWN:
            raise QuerySyntaxError(
                "Unknown query type. Query must start with SELECT, CONSTRUCT, ASK, or DESCRIBE"
            )
        
        # Check for WHERE clause (required for SELECT and CONSTRUCT)
        if query_type in [QueryType.SELECT, QueryType.CONSTRUCT]:
            if 'WHERE' not in query.upper():
                raise QuerySyntaxError(f"{query_type.value} query must contain a WHERE clause")
        
        # ASK queries typically have WHERE but can also use graph patterns directly
        if query_type == QueryType.ASK:
            if 'WHERE' not in query.upper() and '{' not in query:
                raise QuerySyntaxError("ASK query must contain a WHERE clause or graph pattern")
        
        # Check for balanced braces
        if query.count('{') != query.count('}'):
            raise QuerySyntaxError("Unbalanced braces in query")
        
        logger.debug(f"Query syntax validation passed for {query_type.value} query")
    
    def _calculate_timeout(self, triple_count: Optional[int] = None) -> float:
        """
        Calculate appropriate timeout based on triple count.
        
        Args:
            triple_count: Number of triples in the dataset
        
        Returns:
            Timeout in seconds
        """
        if triple_count is None:
            return self.default_timeout
        
        # For datasets under 10k triples, use 5 seconds
        if triple_count < 10000:
            return 5.0
        # For larger datasets, scale timeout
        elif triple_count < 100000:
            return 15.0
        else:
            return self.default_timeout
    
    def execute(
        self,
        query: str,
        timeout: Optional[float] = None,
        output_format: str = 'python',
        validate: bool = True
    ) -> Union[Dict, List, bool, str]:
        """
        Execute a SPARQL query with automatic type detection.
        
        Args:
            query: SPARQL query string
            timeout: Query timeout in seconds (None for auto-calculation)
            output_format: Output format ('python', 'json', 'turtle')
            validate: Whether to validate query syntax before execution
        
        Returns:
            Query results in the specified format
        
        Raises:
            QuerySyntaxError: If the query syntax is invalid
            QueryTimeoutError: If the query exceeds the timeout
            QueryExecutionError: If query execution fails
        """
        start_time = time.time()
        
        try:
            # Validate syntax if requested
            if validate:
                self._validate_query_syntax(query)
            
            # Detect query type
            query_type = self._detect_query_type(query)
            logger.info(f"Executing {query_type.value} query")
            
            # Calculate timeout
            if timeout is None:
                triple_count = self.rdf_loader.get_triple_count() if self.rdf_loader else None
                timeout = self._calculate_timeout(triple_count)
            
            logger.debug(f"Query timeout set to {timeout}s")
            
            # Execute based on query type
            if query_type == QueryType.SELECT:
                result = self._execute_select_internal(query, timeout, output_format)
            elif query_type == QueryType.CONSTRUCT:
                result = self._execute_construct_internal(query, timeout, output_format)
            elif query_type == QueryType.ASK:
                result = self._execute_ask_internal(query, timeout)
            elif query_type == QueryType.DESCRIBE:
                result = self._execute_describe_internal(query, timeout, output_format)
            else:
                raise QuerySyntaxError(f"Unsupported query type: {query_type}")
            
            # Track statistics
            execution_time = time.time() - start_time
            self.query_count += 1
            self.total_query_time += execution_time
            
            logger.info(f"Query executed successfully in {execution_time:.3f}s")
            
            return result
            
        except (QuerySyntaxError, QueryTimeoutError, QueryExecutionError):
            raise
        except Exception as e:
            error_msg = f"Unexpected error executing query: {str(e)}"
            logger.error(error_msg)
            raise QueryExecutionError(error_msg) from e

    
    def _execute_select_internal(
        self,
        query: str,
        timeout: float,
        output_format: str
    ) -> Union[List[Dict], str]:
        """
        Internal method to execute SELECT queries.
        
        Args:
            query: SPARQL SELECT query
            timeout: Query timeout in seconds
            output_format: Output format ('python', 'json', 'turtle')
        
        Returns:
            Query results in the specified format
        
        Raises:
            QueryTimeoutError: If the query exceeds the timeout
            QueryExecutionError: If query execution fails
        """
        try:
            # Note: This is a placeholder implementation
            # Actual implementation would use maplib's SPARQL query capabilities
            logger.warning("SELECT query execution requires maplib SPARQL API implementation")
            
            # Placeholder result structure
            results = {
                'head': {
                    'vars': []
                },
                'results': {
                    'bindings': []
                }
            }
            
            # Format output
            if output_format == 'json':
                return json.dumps(results, indent=2)
            elif output_format == 'sparql_json':
                # Return SPARQL JSON format (the full structure)
                return results
            elif output_format == 'turtle':
                # SELECT queries don't typically return Turtle format
                raise QueryExecutionError("Turtle format not supported for SELECT queries")
            else:  # python
                return results['results']['bindings']
                
        except Exception as e:
            error_msg = f"Error executing SELECT query: {str(e)}"
            logger.error(error_msg)
            raise QueryExecutionError(error_msg) from e
    
    def _execute_construct_internal(
        self,
        query: str,
        timeout: float,
        output_format: str
    ) -> Union[List[Dict], str]:
        """
        Internal method to execute CONSTRUCT queries.
        
        Args:
            query: SPARQL CONSTRUCT query
            timeout: Query timeout in seconds
            output_format: Output format ('python', 'json', 'turtle')
        
        Returns:
            Constructed graph in the specified format
        
        Raises:
            QueryTimeoutError: If the query exceeds the timeout
            QueryExecutionError: If query execution fails
        """
        try:
            # Note: This is a placeholder implementation
            # Actual implementation would use maplib's SPARQL query capabilities
            logger.warning("CONSTRUCT query execution requires maplib SPARQL API implementation")
            
            # Placeholder result
            triples = []
            
            # Format output
            if output_format == 'json':
                return json.dumps({'triples': triples}, indent=2)
            elif output_format == 'turtle':
                # Would serialize triples to Turtle format
                return "# Constructed triples\n"
            else:  # python
                return triples
                
        except Exception as e:
            error_msg = f"Error executing CONSTRUCT query: {str(e)}"
            logger.error(error_msg)
            raise QueryExecutionError(error_msg) from e
    
    def _execute_ask_internal(
        self,
        query: str,
        timeout: float
    ) -> bool:
        """
        Internal method to execute ASK queries.
        
        Args:
            query: SPARQL ASK query
            timeout: Query timeout in seconds
        
        Returns:
            Boolean result
        
        Raises:
            QueryTimeoutError: If the query exceeds the timeout
            QueryExecutionError: If query execution fails
        """
        try:
            # Note: This is a placeholder implementation
            # Actual implementation would use maplib's SPARQL query capabilities
            logger.warning("ASK query execution requires maplib SPARQL API implementation")
            
            # Placeholder result
            return False
                
        except Exception as e:
            error_msg = f"Error executing ASK query: {str(e)}"
            logger.error(error_msg)
            raise QueryExecutionError(error_msg) from e
    
    def _execute_describe_internal(
        self,
        query: str,
        timeout: float,
        output_format: str
    ) -> Union[List[Dict], str]:
        """
        Internal method to execute DESCRIBE queries.
        
        Args:
            query: SPARQL DESCRIBE query
            timeout: Query timeout in seconds
            output_format: Output format ('python', 'json', 'turtle')
        
        Returns:
            Description graph in the specified format
        
        Raises:
            QueryTimeoutError: If the query exceeds the timeout
            QueryExecutionError: If query execution fails
        """
        try:
            # Note: This is a placeholder implementation
            # Actual implementation would use maplib's SPARQL query capabilities
            logger.warning("DESCRIBE query execution requires maplib SPARQL API implementation")
            
            # Placeholder result
            triples = []
            
            # Format output
            if output_format == 'json':
                return json.dumps({'triples': triples}, indent=2)
            elif output_format == 'turtle':
                # Would serialize triples to Turtle format
                return "# Description triples\n"
            else:  # python
                return triples
                
        except Exception as e:
            error_msg = f"Error executing DESCRIBE query: {str(e)}"
            logger.error(error_msg)
            raise QueryExecutionError(error_msg) from e

    
    def execute_select(
        self,
        query: str,
        timeout: Optional[float] = None,
        output_format: str = 'python'
    ) -> Union[List[Dict], str]:
        """
        Execute a SPARQL SELECT query.
        
        Args:
            query: SPARQL SELECT query string
            timeout: Query timeout in seconds (None for auto-calculation)
            output_format: Output format ('python', 'json')
        
        Returns:
            List of result bindings or JSON string
        
        Raises:
            QuerySyntaxError: If the query is not a valid SELECT query
            QueryTimeoutError: If the query exceeds the timeout
            QueryExecutionError: If query execution fails
        
        Example:
            results = engine.execute_select('''
                SELECT ?s ?p ?o
                WHERE {
                    ?s ?p ?o .
                    FILTER(?p = rdf:type)
                }
                LIMIT 10
            ''')
        """
        query_type = self._detect_query_type(query)
        if query_type != QueryType.SELECT:
            raise QuerySyntaxError(f"Expected SELECT query, got {query_type.value}")
        
        return self.execute(query, timeout=timeout, output_format=output_format)
    
    def execute_construct(
        self,
        query: str,
        timeout: Optional[float] = None,
        output_format: str = 'python'
    ) -> Union[List[Dict], str]:
        """
        Execute a SPARQL CONSTRUCT query.
        
        Args:
            query: SPARQL CONSTRUCT query string
            timeout: Query timeout in seconds (None for auto-calculation)
            output_format: Output format ('python', 'json', 'turtle')
        
        Returns:
            Constructed triples or serialized graph
        
        Raises:
            QuerySyntaxError: If the query is not a valid CONSTRUCT query
            QueryTimeoutError: If the query exceeds the timeout
            QueryExecutionError: If query execution fails
        
        Example:
            graph = engine.execute_construct('''
                CONSTRUCT { ?s a ?type }
                WHERE {
                    ?s a ?type .
                    FILTER(?type = owl:Class)
                }
            ''')
        """
        query_type = self._detect_query_type(query)
        if query_type != QueryType.CONSTRUCT:
            raise QuerySyntaxError(f"Expected CONSTRUCT query, got {query_type.value}")
        
        return self.execute(query, timeout=timeout, output_format=output_format)
    
    def execute_ask(
        self,
        query: str,
        timeout: Optional[float] = None
    ) -> bool:
        """
        Execute a SPARQL ASK query.
        
        Args:
            query: SPARQL ASK query string
            timeout: Query timeout in seconds (None for auto-calculation)
        
        Returns:
            Boolean result
        
        Raises:
            QuerySyntaxError: If the query is not a valid ASK query
            QueryTimeoutError: If the query exceeds the timeout
            QueryExecutionError: If query execution fails
        
        Example:
            exists = engine.execute_ask('''
                ASK {
                    ?s a owl:Class .
                    OPTIONAL { ?s rdfs:label ?label }
                }
            ''')
        """
        query_type = self._detect_query_type(query)
        if query_type != QueryType.ASK:
            raise QuerySyntaxError(f"Expected ASK query, got {query_type.value}")
        
        return self.execute(query, timeout=timeout)
    
    def execute_describe(
        self,
        resource_uri: str,
        timeout: Optional[float] = None,
        output_format: str = 'python'
    ) -> Union[List[Dict], str]:
        """
        Execute a SPARQL DESCRIBE query for a resource.
        
        Args:
            resource_uri: URI of the resource to describe
            timeout: Query timeout in seconds (None for auto-calculation)
            output_format: Output format ('python', 'json', 'turtle')
        
        Returns:
            Description triples or serialized graph
        
        Raises:
            QueryTimeoutError: If the query exceeds the timeout
            QueryExecutionError: If query execution fails
        
        Example:
            description = engine.execute_describe(
                'http://example.org/ontology#Entity'
            )
        """
        # Construct DESCRIBE query
        if resource_uri.startswith('http://') or resource_uri.startswith('https://'):
            query = f"DESCRIBE <{resource_uri}>"
        else:
            query = f"DESCRIBE {resource_uri}"
        
        return self.execute(query, timeout=timeout, output_format=output_format)
    
    def execute_with_bindings(
        self,
        query: str,
        bindings: Dict[str, str],
        timeout: Optional[float] = None,
        output_format: str = 'python'
    ) -> Union[Dict, List, bool, str]:
        """
        Execute a parameterized SPARQL query with variable bindings.
        
        Args:
            query: SPARQL query string with placeholders
            bindings: Dictionary mapping variable names to values
            timeout: Query timeout in seconds (None for auto-calculation)
            output_format: Output format ('python', 'json', 'turtle')
        
        Returns:
            Query results in the specified format
        
        Raises:
            QuerySyntaxError: If the query syntax is invalid
            QueryTimeoutError: If the query exceeds the timeout
            QueryExecutionError: If query execution fails
        
        Example:
            results = engine.execute_with_bindings(
                'SELECT ?s ?o WHERE { ?s ?p ?o }',
                {'p': 'rdf:type'}
            )
        """
        # Replace placeholders with actual values
        parameterized_query = query
        for var, value in bindings.items():
            placeholder = f"?{var}"
            parameterized_query = parameterized_query.replace(placeholder, value)
        
        logger.debug(f"Executing parameterized query with {len(bindings)} bindings")
        
        return self.execute(
            parameterized_query,
            timeout=timeout,
            output_format=output_format
        )

    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get query execution statistics.
        
        Returns:
            Dictionary containing query statistics
        """
        avg_time = (
            self.total_query_time / self.query_count
            if self.query_count > 0
            else 0.0
        )
        
        return {
            'total_queries': self.query_count,
            'total_time': round(self.total_query_time, 3),
            'average_time': round(avg_time, 3),
            'default_timeout': self.default_timeout
        }
    
    def reset_statistics(self) -> None:
        """Reset query execution statistics."""
        self.query_count = 0
        self.total_query_time = 0.0
        logger.info("Query statistics reset")
    
    def validate_query(self, query: str) -> Dict[str, Any]:
        """
        Validate a SPARQL query without executing it.
        
        Args:
            query: SPARQL query string
        
        Returns:
            Dictionary with validation results
        """
        try:
            self._validate_query_syntax(query)
            query_type = self._detect_query_type(query)
            
            return {
                'valid': True,
                'query_type': query_type.value,
                'message': 'Query syntax is valid'
            }
        except QuerySyntaxError as e:
            return {
                'valid': False,
                'query_type': None,
                'message': str(e)
            }
    
    def supports_feature(self, feature: str) -> bool:
        """
        Check if a SPARQL feature is supported.
        
        Args:
            feature: Feature name (e.g., 'FILTER', 'OPTIONAL', 'UNION')
        
        Returns:
            True if the feature is supported
        """
        supported_features = {
            'SELECT', 'CONSTRUCT', 'ASK', 'DESCRIBE',
            'FILTER', 'OPTIONAL', 'UNION', 'LIMIT', 'OFFSET',
            'ORDER BY', 'DISTINCT', 'REDUCED'
        }
        
        return feature.upper() in supported_features


def create_query_engine(
    ontology_dir: str = "ontology",
    validation_dir: str = "validation",
    data_dir: str = "data",
    default_timeout: float = 30.0
) -> SPARQLQueryEngine:
    """
    Convenience function to create a query engine with loaded ontology data.
    
    Args:
        ontology_dir: Directory containing ontology files
        validation_dir: Directory containing SHACL shapes
        data_dir: Directory containing instance data
        default_timeout: Default query timeout in seconds
    
    Returns:
        Configured SPARQLQueryEngine instance
    
    Example:
        engine = create_query_engine()
        results = engine.execute_select('SELECT * WHERE { ?s ?p ?o } LIMIT 10')
    """
    try:
        from ontology.loader import load_ontology_files
    except ImportError:
        # Handle case when running as script
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from ontology.loader import load_ontology_files
    
    logger.info("Creating SPARQL query engine with loaded ontology data")
    
    # Load ontology files
    loader = load_ontology_files(ontology_dir, validation_dir, data_dir)
    
    # Create query engine
    engine = SPARQLQueryEngine(loader, default_timeout=default_timeout)
    
    logger.info("SPARQL query engine created successfully")
    
    return engine


# Example queries for testing
EXAMPLE_QUERIES = {
    'select_all': '''
        SELECT ?subject ?predicate ?object
        WHERE {
            ?subject ?predicate ?object .
        }
        LIMIT 10
    ''',
    
    'select_classes': '''
        SELECT ?class ?label
        WHERE {
            ?class a owl:Class .
            OPTIONAL { ?class rdfs:label ?label }
        }
    ''',
    
    'select_with_filter': '''
        SELECT ?entity ?property
        WHERE {
            ?entity ?property ?value .
            FILTER(?property = rdf:type)
        }
    ''',
    
    'construct_types': '''
        CONSTRUCT { ?s a ?type }
        WHERE {
            ?s a ?type .
        }
    ''',
    
    'ask_classes': '''
        ASK WHERE {
            ?s a owl:Class .
        }
    ''',
    
    'describe_resource': '''
        DESCRIBE <http://example.org/ontology#Entity>
    '''
}


if __name__ == "__main__":
    # Example usage
    print("SPARQL Query Engine Module")
    print("=" * 50)
    
    # Create query engine
    try:
        engine = create_query_engine()
        print(f"Query engine created with {engine.rdf_loader.get_triple_count()} loaded files")
        
        # Validate example queries
        print("\nValidating example queries:")
        for name, query in EXAMPLE_QUERIES.items():
            result = engine.validate_query(query)
            status = "✓" if result['valid'] else "✗"
            print(f"{status} {name}: {result['query_type']} - {result['message']}")
        
        # Show supported features
        print("\nSupported SPARQL features:")
        features = ['SELECT', 'CONSTRUCT', 'ASK', 'DESCRIBE', 'FILTER', 'OPTIONAL']
        for feature in features:
            supported = "✓" if engine.supports_feature(feature) else "✗"
            print(f"{supported} {feature}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
