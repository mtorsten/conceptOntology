"""
W3C Semantic Web Ontology System

A standards-compliant ontology system built on RDF 1.2, SPARQL, SHACL, and Turtle serialization.
Uses maplib for RDF triple manipulation, SPARQL queries, and SHACL validation.
"""

__version__ = "0.1.0"

# Import main classes for easier access
from ontology.loader import RDFLoader, load_ontology_files
from ontology.query import SPARQLQueryEngine, create_query_engine

__all__ = [
    'RDFLoader',
    'load_ontology_files',
    'SPARQLQueryEngine',
    'create_query_engine',
]
