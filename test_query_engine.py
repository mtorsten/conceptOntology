"""
Test script for SPARQL Query Engine

This script demonstrates the functionality of the SPARQL query engine.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from ontology.query import SPARQLQueryEngine, create_query_engine, EXAMPLE_QUERIES
from ontology.loader import load_ontology_files


def test_query_validation():
    """Test query validation functionality."""
    print("\n" + "=" * 60)
    print("TEST: Query Validation")
    print("=" * 60)
    
    engine = SPARQLQueryEngine()
    
    # Test valid queries
    valid_queries = [
        ("SELECT", "SELECT ?s ?p ?o WHERE { ?s ?p ?o }"),
        ("CONSTRUCT", "CONSTRUCT { ?s ?p ?o } WHERE { ?s ?p ?o }"),
        ("ASK", "ASK WHERE { ?s a owl:Class }"),
        ("DESCRIBE", "DESCRIBE <http://example.org/resource>"),
    ]
    
    print("\nValid queries:")
    for name, query in valid_queries:
        result = engine.validate_query(query)
        print(f"  ✓ {name}: {result['query_type']} - {result['message']}")
    
    # Test invalid queries
    invalid_queries = [
        ("Empty query", ""),
        ("Missing WHERE", "SELECT ?s ?p ?o"),
        ("Unbalanced braces", "SELECT ?s WHERE { ?s ?p ?o"),
        ("Unknown type", "INVALID ?s WHERE { ?s ?p ?o }"),
    ]
    
    print("\nInvalid queries:")
    for name, query in invalid_queries:
        result = engine.validate_query(query)
        print(f"  ✗ {name}: {result['message']}")


def test_query_type_detection():
    """Test query type detection."""
    print("\n" + "=" * 60)
    print("TEST: Query Type Detection")
    print("=" * 60)
    
    engine = SPARQLQueryEngine()
    
    for name, query in EXAMPLE_QUERIES.items():
        query_type = engine._detect_query_type(query)
        print(f"  {name}: {query_type.value}")


def test_timeout_calculation():
    """Test timeout calculation based on triple count."""
    print("\n" + "=" * 60)
    print("TEST: Timeout Calculation")
    print("=" * 60)
    
    engine = SPARQLQueryEngine()
    
    test_cases = [
        (None, "No triple count"),
        (5000, "5,000 triples"),
        (50000, "50,000 triples"),
        (150000, "150,000 triples"),
    ]
    
    for triple_count, description in test_cases:
        timeout = engine._calculate_timeout(triple_count)
        print(f"  {description}: {timeout}s timeout")


def test_feature_support():
    """Test feature support checking."""
    print("\n" + "=" * 60)
    print("TEST: Feature Support")
    print("=" * 60)
    
    engine = SPARQLQueryEngine()
    
    features = [
        'SELECT', 'CONSTRUCT', 'ASK', 'DESCRIBE',
        'FILTER', 'OPTIONAL', 'UNION',
        'LIMIT', 'OFFSET', 'ORDER BY',
        'DISTINCT', 'REDUCED',
        'UNSUPPORTED_FEATURE'
    ]
    
    for feature in features:
        supported = engine.supports_feature(feature)
        status = "✓" if supported else "✗"
        print(f"  {status} {feature}")


def test_with_loaded_data():
    """Test query engine with loaded ontology data."""
    print("\n" + "=" * 60)
    print("TEST: Query Engine with Loaded Data")
    print("=" * 60)
    
    try:
        # Load ontology files
        loader = load_ontology_files()
        print(f"\nLoaded {loader.get_triple_count()} files")
        print(f"Registered namespaces: {list(loader.get_namespaces().keys())}")
        
        # Create query engine
        engine = SPARQLQueryEngine(loader)
        
        # Get statistics
        stats = engine.get_statistics()
        print(f"\nQuery Statistics:")
        print(f"  Total queries: {stats['total_queries']}")
        print(f"  Default timeout: {stats['default_timeout']}s")
        
        # Test query execution (will show warnings about maplib implementation)
        print("\nTesting query execution:")
        try:
            result = engine.execute_select(EXAMPLE_QUERIES['select_all'])
            print(f"  ✓ SELECT query executed (returned {len(result)} results)")
        except Exception as e:
            print(f"  ✗ SELECT query failed: {str(e)}")
        
        try:
            result = engine.execute_ask(EXAMPLE_QUERIES['ask_classes'])
            print(f"  ✓ ASK query executed (result: {result})")
        except Exception as e:
            print(f"  ✗ ASK query failed: {str(e)}")
        
    except Exception as e:
        print(f"Error: {str(e)}")


def test_parameterized_queries():
    """Test parameterized query execution."""
    print("\n" + "=" * 60)
    print("TEST: Parameterized Queries")
    print("=" * 60)
    
    engine = SPARQLQueryEngine()
    
    query = "SELECT ?s ?o WHERE { ?s ?p ?o }"
    bindings = {'p': 'rdf:type'}
    
    print(f"\nOriginal query: {query}")
    print(f"Bindings: {bindings}")
    
    # This will show the parameterized query in logs
    try:
        result = engine.execute_with_bindings(query, bindings)
        print(f"  ✓ Parameterized query executed")
    except Exception as e:
        print(f"  ✗ Parameterized query failed: {str(e)}")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("SPARQL Query Engine Test Suite")
    print("=" * 60)
    
    test_query_validation()
    test_query_type_detection()
    test_timeout_calculation()
    test_feature_support()
    test_with_loaded_data()
    test_parameterized_queries()
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
