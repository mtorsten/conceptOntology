#!/usr/bin/env python3
"""
Graph Explorer Configuration Verification Script

This script verifies that the graph explorer is properly configured to connect
to the Python API endpoint and can query RDF data successfully.

Usage:
    python verify_graph_explorer_config.py
"""

import sys
import time
import requests
from typing import Dict, Any, Tuple


# Configuration
API_BASE_URL = "http://localhost:8000"
GRAPH_EXPLORER_URL = "http://localhost:3000"
TIMEOUT = 10


def print_header(text: str):
    """Print a formatted header."""
    print(f"\n{'=' * 70}")
    print(f"  {text}")
    print(f"{'=' * 70}\n")


def print_success(text: str):
    """Print a success message."""
    print(f"✓ {text}")


def print_error(text: str):
    """Print an error message."""
    print(f"✗ {text}")


def print_info(text: str):
    """Print an info message."""
    print(f"ℹ {text}")


def check_api_health() -> Tuple[bool, str]:
    """
    Check if the Python API is healthy and responding.
    
    Returns:
        Tuple of (success, message)
    """
    try:
        response = requests.get(f"{API_BASE_URL}/health", timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success'):
                return True, "Python API is healthy"
            else:
                return False, f"API returned unhealthy status: {data}"
        else:
            return False, f"API returned status code {response.status_code}"
            
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to Python API (is it running?)"
    except requests.exceptions.Timeout:
        return False, "API health check timed out"
    except Exception as e:
        return False, f"Error checking API health: {str(e)}"


def check_graph_explorer() -> Tuple[bool, str]:
    """
    Check if the graph explorer is accessible.
    
    Returns:
        Tuple of (success, message)
    """
    try:
        response = requests.get(GRAPH_EXPLORER_URL, timeout=TIMEOUT)
        
        if response.status_code == 200:
            return True, "Graph explorer is accessible"
        else:
            return False, f"Graph explorer returned status code {response.status_code}"
            
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to graph explorer (is it running?)"
    except requests.exceptions.Timeout:
        return False, "Graph explorer request timed out"
    except Exception as e:
        return False, f"Error checking graph explorer: {str(e)}"


def check_sparql_endpoint() -> Tuple[bool, str]:
    """
    Check if the SPARQL endpoint is working.
    
    Returns:
        Tuple of (success, message)
    """
    query = "SELECT ?s ?p ?o WHERE { ?s ?p ?o } LIMIT 1"
    
    try:
        # Test with JSON format (what graph explorer uses)
        response = requests.post(
            f"{API_BASE_URL}/query",
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            # Check if it's SPARQL JSON format
            if "head" in data and "results" in data:
                return True, "SPARQL endpoint returns correct format"
            else:
                return False, f"SPARQL endpoint returns unexpected format: {data}"
        else:
            return False, f"SPARQL endpoint returned status code {response.status_code}"
            
    except requests.exceptions.ConnectionError:
        return False, "Cannot connect to SPARQL endpoint"
    except requests.exceptions.Timeout:
        return False, "SPARQL query timed out"
    except Exception as e:
        return False, f"Error testing SPARQL endpoint: {str(e)}"


def check_cors() -> Tuple[bool, str]:
    """
    Check if CORS is properly configured.
    
    Returns:
        Tuple of (success, message)
    """
    try:
        # Send OPTIONS request to check CORS
        response = requests.options(
            f"{API_BASE_URL}/query",
            headers={
                "Origin": "http://localhost:3000",
                "Access-Control-Request-Method": "POST",
                "Access-Control-Request-Headers": "Content-Type"
            },
            timeout=TIMEOUT
        )
        
        # Check for CORS headers
        cors_headers = {
            "Access-Control-Allow-Origin": response.headers.get("Access-Control-Allow-Origin"),
            "Access-Control-Allow-Methods": response.headers.get("Access-Control-Allow-Methods"),
            "Access-Control-Allow-Headers": response.headers.get("Access-Control-Allow-Headers")
        }
        
        if cors_headers["Access-Control-Allow-Origin"]:
            return True, f"CORS is enabled: {cors_headers['Access-Control-Allow-Origin']}"
        else:
            return False, "CORS headers not found in response"
            
    except Exception as e:
        return False, f"Error checking CORS: {str(e)}"


def check_data_loaded() -> Tuple[bool, str]:
    """
    Check if RDF data is loaded in the API.
    
    Returns:
        Tuple of (success, message)
    """
    try:
        response = requests.get(f"{API_BASE_URL}/triples", timeout=TIMEOUT)
        
        if response.status_code == 200:
            data = response.json()
            
            if data.get('success'):
                file_count = data.get('data', {}).get('file_count', 0)
                
                if file_count > 0:
                    files = data.get('data', {}).get('loaded_files', [])
                    return True, f"Data loaded: {file_count} files ({', '.join(files)})"
                else:
                    return False, "No RDF data loaded (load ontology files first)"
            else:
                return False, f"API returned error: {data}"
        else:
            return False, f"Triples endpoint returned status code {response.status_code}"
            
    except Exception as e:
        return False, f"Error checking loaded data: {str(e)}"


def check_owl_classes() -> Tuple[bool, str]:
    """
    Check if OWL classes can be queried (what graph explorer needs).
    
    Returns:
        Tuple of (success, message)
    """
    query = """
    PREFIX owl: <http://www.w3.org/2002/07/owl#>
    PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
    
    SELECT ?class ?label WHERE {
        ?class a owl:Class .
        OPTIONAL { ?class rdfs:label ?label }
    } LIMIT 10
    """
    
    try:
        response = requests.post(
            f"{API_BASE_URL}/query",
            json={"query": query},
            headers={"Content-Type": "application/json"},
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            
            if "results" in data and "bindings" in data["results"]:
                bindings = data["results"]["bindings"]
                count = len(bindings)
                
                if count > 0:
                    return True, f"Found {count} OWL classes (graph explorer will display them)"
                else:
                    return False, "No OWL classes found (ontology may not be loaded)"
            else:
                return False, f"Unexpected query response format: {data}"
        else:
            return False, f"Query returned status code {response.status_code}"
            
    except Exception as e:
        return False, f"Error querying OWL classes: {str(e)}"


def run_verification():
    """Run all verification checks."""
    print_header("Graph Explorer Configuration Verification")
    
    print_info("This script verifies the graph explorer integration with the Python API")
    print_info(f"API URL: {API_BASE_URL}")
    print_info(f"Graph Explorer URL: {GRAPH_EXPLORER_URL}")
    
    # Track results
    checks = []
    
    # Check 1: API Health
    print_header("1. Checking Python API Health")
    success, message = check_api_health()
    checks.append(("API Health", success))
    
    if success:
        print_success(message)
    else:
        print_error(message)
        print_info("Start the API with: docker-compose up -d ontology-api")
    
    # Check 2: Graph Explorer
    print_header("2. Checking Graph Explorer Accessibility")
    success, message = check_graph_explorer()
    checks.append(("Graph Explorer", success))
    
    if success:
        print_success(message)
    else:
        print_error(message)
        print_info("Start graph explorer with: docker-compose up -d graph-explorer")
    
    # Check 3: SPARQL Endpoint
    print_header("3. Checking SPARQL Endpoint")
    success, message = check_sparql_endpoint()
    checks.append(("SPARQL Endpoint", success))
    
    if success:
        print_success(message)
    else:
        print_error(message)
        print_info("Verify the /query endpoint is working correctly")
    
    # Check 4: CORS
    print_header("4. Checking CORS Configuration")
    success, message = check_cors()
    checks.append(("CORS", success))
    
    if success:
        print_success(message)
    else:
        print_error(message)
        print_info("CORS must be enabled for graph explorer to work")
    
    # Check 5: Data Loaded
    print_header("5. Checking RDF Data")
    success, message = check_data_loaded()
    checks.append(("Data Loaded", success))
    
    if success:
        print_success(message)
    else:
        print_error(message)
        print_info("Load data with: curl -X POST http://localhost:8000/load -H 'Content-Type: application/json' -d '{\"files\": [\"ontology/core.ttl\"]}'")
    
    # Check 6: OWL Classes
    print_header("6. Checking OWL Classes")
    success, message = check_owl_classes()
    checks.append(("OWL Classes", success))
    
    if success:
        print_success(message)
    else:
        print_error(message)
        print_info("Ensure your ontology files contain OWL classes")
    
    # Summary
    print_header("Verification Summary")
    
    passed = sum(1 for _, success in checks if success)
    total = len(checks)
    
    print(f"\nPassed: {passed}/{total} checks\n")
    
    for check_name, success in checks:
        status = "✓ PASS" if success else "✗ FAIL"
        print(f"  {status}: {check_name}")
    
    print()
    
    if passed == total:
        print_success("All checks passed! Graph explorer is properly configured.")
        print_info(f"Access graph explorer at: {GRAPH_EXPLORER_URL}")
        return 0
    else:
        print_error(f"{total - passed} check(s) failed. See messages above for details.")
        return 1


if __name__ == "__main__":
    try:
        exit_code = run_verification()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nVerification interrupted by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n\nUnexpected error: {str(e)}")
        sys.exit(1)
