#!/usr/bin/env python3
"""
Load RDF Data into Apache Jena Fuseki

This script loads Turtle files from the ontology and data directories
into the Fuseki SPARQL server.

Usage:
    python load_data_to_fuseki.py
    python load_data_to_fuseki.py --files ontology/core.ttl ontology/extensions.ttl
    python load_data_to_fuseki.py --clear
"""

import sys
import argparse
import requests
from pathlib import Path
from typing import List, Tuple


def print_header(text: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {text}")
    print("=" * 70)


def print_success(text: str):
    """Print a success message."""
    print(f"✓ {text}")


def print_error(text: str):
    """Print an error message."""
    print(f"✗ {text}")


def print_info(text: str):
    """Print an info message."""
    print(f"ℹ {text}")


def check_fuseki_health(fuseki_url: str) -> bool:
    """
    Check if Fuseki is running and accessible.
    
    Args:
        fuseki_url: Base URL of Fuseki server
    
    Returns:
        True if Fuseki is healthy, False otherwise
    """
    try:
        response = requests.get(f"{fuseki_url}/$/ping", timeout=5)
        return response.status_code == 200
    except requests.exceptions.RequestException:
        return False


def clear_dataset(fuseki_url: str, dataset: str) -> Tuple[bool, str]:
    """
    Clear all data from the dataset.
    
    Args:
        fuseki_url: Base URL of Fuseki server
        dataset: Dataset name
    
    Returns:
        Tuple of (success, message)
    """
    try:
        # Delete all triples using SPARQL UPDATE
        update_query = "DELETE WHERE { ?s ?p ?o }"
        
        response = requests.post(
            f"{fuseki_url}/{dataset}/update",
            data={'update': update_query},
            headers={'Content-Type': 'application/x-www-form-urlencoded'},
            timeout=30
        )
        
        if response.status_code in [200, 204]:
            return True, "Dataset cleared successfully"
        else:
            return False, f"Failed to clear dataset: {response.status_code} - {response.text}"
    
    except requests.exceptions.RequestException as e:
        return False, f"Error clearing dataset: {str(e)}"


def load_turtle_file(fuseki_url: str, dataset: str, file_path: Path) -> Tuple[bool, str]:
    """
    Load a Turtle file into Fuseki.
    
    Args:
        fuseki_url: Base URL of Fuseki server
        dataset: Dataset name
        file_path: Path to Turtle file
    
    Returns:
        Tuple of (success, message)
    """
    try:
        if not file_path.exists():
            return False, f"File not found: {file_path}"
        
        # Read file content
        with open(file_path, 'r', encoding='utf-8') as f:
            turtle_data = f.read()
        
        # POST to Fuseki Graph Store endpoint
        response = requests.post(
            f"{fuseki_url}/{dataset}/data?default",
            data=turtle_data,
            headers={'Content-Type': 'text/turtle'},
            timeout=60
        )
        
        if response.status_code in [200, 201, 204]:
            return True, f"Loaded {file_path.name}"
        else:
            return False, f"Failed to load {file_path.name}: {response.status_code} - {response.text}"
    
    except requests.exceptions.RequestException as e:
        return False, f"Error loading {file_path.name}: {str(e)}"
    except Exception as e:
        return False, f"Error reading {file_path.name}: {str(e)}"


def count_triples(fuseki_url: str, dataset: str) -> Tuple[bool, int]:
    """
    Count the number of triples in the dataset.
    
    Args:
        fuseki_url: Base URL of Fuseki server
        dataset: Dataset name
    
    Returns:
        Tuple of (success, count)
    """
    try:
        query = "SELECT (COUNT(*) as ?count) WHERE { ?s ?p ?o }"
        
        response = requests.post(
            f"{fuseki_url}/{dataset}/sparql",
            data={'query': query},
            headers={'Accept': 'application/sparql-results+json'},
            timeout=30
        )
        
        if response.status_code == 200:
            results = response.json()
            bindings = results.get('results', {}).get('bindings', [])
            if bindings:
                count = int(bindings[0]['count']['value'])
                return True, count
        
        return False, 0
    
    except Exception as e:
        print_error(f"Error counting triples: {str(e)}")
        return False, 0


def discover_turtle_files() -> List[Path]:
    """
    Discover all Turtle files in ontology and data directories.
    
    Returns:
        List of Path objects for Turtle files
    """
    turtle_files = []
    
    # Check ontology directory
    ontology_dir = Path('ontology')
    if ontology_dir.exists():
        turtle_files.extend(ontology_dir.glob('*.ttl'))
    
    # Check data directory
    data_dir = Path('data')
    if data_dir.exists():
        turtle_files.extend(data_dir.glob('*.ttl'))
    
    return sorted(turtle_files)


def main():
    """Main function."""
    parser = argparse.ArgumentParser(
        description='Load RDF data into Apache Jena Fuseki'
    )
    parser.add_argument(
        '--fuseki-url',
        default='http://localhost:3030',
        help='Fuseki server URL (default: http://localhost:3030)'
    )
    parser.add_argument(
        '--dataset',
        default='ontology',
        help='Dataset name (default: ontology)'
    )
    parser.add_argument(
        '--files',
        nargs='+',
        help='Specific files to load (default: auto-discover)'
    )
    parser.add_argument(
        '--clear',
        action='store_true',
        help='Clear dataset before loading'
    )
    
    args = parser.parse_args()
    
    print_header("Apache Jena Fuseki Data Loader")
    
    # Check Fuseki health
    print_info(f"Checking Fuseki at {args.fuseki_url}...")
    if not check_fuseki_health(args.fuseki_url):
        print_error("Fuseki is not accessible")
        print_info("Ensure Fuseki is running: docker-compose up -d fuseki")
        return 1
    
    print_success("Fuseki is running")
    
    # Clear dataset if requested
    if args.clear:
        print_header("Clearing Dataset")
        success, message = clear_dataset(args.fuseki_url, args.dataset)
        if success:
            print_success(message)
        else:
            print_error(message)
            return 1
    
    # Determine files to load
    if args.files:
        files_to_load = [Path(f) for f in args.files]
    else:
        print_info("Auto-discovering Turtle files...")
        files_to_load = discover_turtle_files()
    
    if not files_to_load:
        print_error("No Turtle files found")
        print_info("Specify files with --files or ensure ontology/*.ttl or data/*.ttl exist")
        return 1
    
    print_info(f"Found {len(files_to_load)} files to load")
    
    # Load files
    print_header("Loading Files")
    
    successful = 0
    failed = 0
    
    for file_path in files_to_load:
        print_info(f"Loading {file_path}...")
        success, message = load_turtle_file(args.fuseki_url, args.dataset, file_path)
        
        if success:
            print_success(message)
            successful += 1
        else:
            print_error(message)
            failed += 1
    
    # Count triples
    print_header("Summary")
    
    success, count = count_triples(args.fuseki_url, args.dataset)
    if success:
        print_info(f"Total triples in dataset: {count:,}")
    
    print_info(f"Files loaded successfully: {successful}")
    if failed > 0:
        print_info(f"Files failed: {failed}")
    
    # Final status
    if failed == 0:
        print_success("All files loaded successfully!")
        print_info(f"\nAccess Fuseki web UI: {args.fuseki_url}")
        print_info(f"SPARQL endpoint: {args.fuseki_url}/{args.dataset}/sparql")
        print_info(f"Graph Explorer: http://localhost:3000")
        return 0
    else:
        print_error("Some files failed to load")
        return 1


if __name__ == '__main__':
    sys.exit(main())
