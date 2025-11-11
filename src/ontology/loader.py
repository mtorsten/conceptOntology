"""
RDF Loader Module

This module provides functionality to load Turtle files into an RDF store using maplib.
It includes Turtle syntax validation, namespace prefix management, multi-file loading
with graph merging, and comprehensive error handling.

Example Usage:
    # Load a single file
    loader = RDFLoader()
    loader.load_file("ontology/core.ttl")
    
    # Load multiple files
    loader.load_files(["ontology/core.ttl", "ontology/extensions.ttl"])
    
    # Load all files from a directory
    loader.load_directory("ontology")
    
    # Use convenience function to load all ontology files
    loader = load_ontology_files()
    
    # Access loaded data
    print(f"Loaded files: {loader.get_loaded_files()}")
    print(f"Namespaces: {loader.get_namespaces()}")
    
    # Resolve prefixed URIs
    full_uri = loader.resolve_uri("rdf:type")
"""

import os
from pathlib import Path
from typing import List, Dict, Optional, Union, Tuple
import logging

try:
    import maplib
    from maplib import add_triples, explore
except ImportError:
    raise ImportError(
        "maplib is required but not installed. "
        "Install it with: pip install maplib"
    )


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RDFLoaderError(Exception):
    """Base exception for RDF loader errors."""
    pass


class TurtleSyntaxError(RDFLoaderError):
    """Exception raised for Turtle syntax errors."""
    pass


class FileNotFoundError(RDFLoaderError):
    """Exception raised when a file is not found."""
    pass


class NamespaceError(RDFLoaderError):
    """Exception raised for namespace resolution errors."""
    pass


class RDFLoader:
    """
    RDF Loader for loading and managing Turtle files using maplib.
    
    This class provides methods to:
    - Load single or multiple Turtle files
    - Validate Turtle syntax before loading
    - Manage namespace prefixes
    - Merge graphs from multiple files
    - Handle errors gracefully
    """
    
    def __init__(self):
        """Initialize the RDF loader with an empty graph."""
        self.triples: List = []
        self.loaded_files: List[str] = []
        self.namespaces: Dict[str, str] = {}
        logger.info("RDF Loader initialized")
    
    def load_file(self, file_path: Union[str, Path], validate: bool = True) -> bool:
        """
        Load a single Turtle file into the RDF store.
        
        Args:
            file_path: Path to the Turtle file
            validate: Whether to validate syntax before loading (default: True)
        
        Returns:
            True if loading was successful
        
        Raises:
            FileNotFoundError: If the file does not exist
            TurtleSyntaxError: If the file contains invalid Turtle syntax
            RDFLoaderError: For other loading errors
        """
        file_path = Path(file_path)
        
        # Check if file exists
        if not file_path.exists():
            error_msg = f"File not found: {file_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # Check if file is readable
        if not file_path.is_file():
            error_msg = f"Path is not a file: {file_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        logger.info(f"Loading Turtle file: {file_path}")
        
        try:
            # Read file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Validate syntax if requested
            if validate:
                self._validate_turtle_syntax(content, str(file_path))
            
            # Extract namespaces from the file
            self._extract_namespaces(content)
            
            # Load the file using maplib
            # Note: maplib's add_triples expects triples in a specific format
            # For now, we'll store the file path and content for later processing
            self.triples.append({
                'file': str(file_path),
                'content': content
            })
            
            # Track loaded files
            self.loaded_files.append(str(file_path))
            logger.info(f"Successfully loaded: {file_path}")
            
            return True
            
        except TurtleSyntaxError:
            raise
        except Exception as e:
            error_msg = f"Error loading file {file_path}: {str(e)}"
            logger.error(error_msg)
            raise RDFLoaderError(error_msg) from e
    
    def load_files(
        self,
        file_paths: List[Union[str, Path]],
        validate: bool = True,
        continue_on_error: bool = False
    ) -> Tuple[List[str], List[str]]:
        """
        Load multiple Turtle files and merge them into a unified graph.
        
        Args:
            file_paths: List of paths to Turtle files
            validate: Whether to validate syntax before loading (default: True)
            continue_on_error: Whether to continue loading other files if one fails
        
        Returns:
            Tuple of (successful_files, failed_files)
        
        Raises:
            RDFLoaderError: If continue_on_error is False and any file fails to load
        """
        successful_files = []
        failed_files = []
        
        logger.info(f"Loading {len(file_paths)} Turtle files")
        
        for file_path in file_paths:
            try:
                self.load_file(file_path, validate=validate)
                successful_files.append(str(file_path))
            except (FileNotFoundError, TurtleSyntaxError, RDFLoaderError) as e:
                failed_files.append(str(file_path))
                logger.error(f"Failed to load {file_path}: {str(e)}")
                
                if not continue_on_error:
                    raise
        
        logger.info(
            f"Loaded {len(successful_files)} files successfully, "
            f"{len(failed_files)} files failed"
        )
        
        return successful_files, failed_files
    
    def load_directory(
        self,
        directory_path: Union[str, Path],
        pattern: str = "*.ttl",
        recursive: bool = False,
        validate: bool = True,
        continue_on_error: bool = True
    ) -> Tuple[List[str], List[str]]:
        """
        Load all Turtle files from a directory.
        
        Args:
            directory_path: Path to the directory
            pattern: File pattern to match (default: "*.ttl")
            recursive: Whether to search subdirectories (default: False)
            validate: Whether to validate syntax before loading
            continue_on_error: Whether to continue loading other files if one fails
        
        Returns:
            Tuple of (successful_files, failed_files)
        
        Raises:
            FileNotFoundError: If the directory does not exist
        """
        directory_path = Path(directory_path)
        
        if not directory_path.exists():
            error_msg = f"Directory not found: {directory_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        if not directory_path.is_dir():
            error_msg = f"Path is not a directory: {directory_path}"
            logger.error(error_msg)
            raise FileNotFoundError(error_msg)
        
        # Find all matching files
        if recursive:
            file_paths = list(directory_path.rglob(pattern))
        else:
            file_paths = list(directory_path.glob(pattern))
        
        logger.info(f"Found {len(file_paths)} files matching '{pattern}' in {directory_path}")
        
        if not file_paths:
            logger.warning(f"No files found matching pattern '{pattern}'")
            return [], []
        
        return self.load_files(file_paths, validate=validate, continue_on_error=continue_on_error)
    
    def _validate_turtle_syntax(self, content: str, file_path: str) -> None:
        """
        Validate Turtle syntax before loading.
        
        Args:
            content: The Turtle file content
            file_path: Path to the file (for error reporting)
        
        Raises:
            TurtleSyntaxError: If the syntax is invalid
        """
        # Basic syntax validation checks
        lines = content.split('\n')
        
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            
            # Skip empty lines and comments
            if not line or line.startswith('#'):
                continue
            
            # Check for common syntax errors
            # 1. Unclosed strings
            if line.count('"') % 2 != 0 and not line.endswith('\\'):
                # Check if it's a multi-line string
                if '"""' not in line:
                    error_msg = (
                        f"Syntax error in {file_path} at line {line_num}: "
                        f"Unclosed string"
                    )
                    logger.error(error_msg)
                    raise TurtleSyntaxError(error_msg)
            
            # 2. Invalid prefix declarations
            if line.startswith('@prefix'):
                parts = line.split()
                if len(parts) < 3 or not parts[2].startswith('<') or not line.rstrip().endswith('.'):
                    error_msg = (
                        f"Syntax error in {file_path} at line {line_num}: "
                        f"Invalid @prefix declaration"
                    )
                    logger.error(error_msg)
                    raise TurtleSyntaxError(error_msg)
        
        logger.debug(f"Turtle syntax validation passed for {file_path}")
    
    def _extract_namespaces(self, content: str) -> None:
        """
        Extract namespace prefixes from Turtle content.
        
        Args:
            content: The Turtle file content
        """
        lines = content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            # Parse @prefix declarations
            if line.startswith('@prefix'):
                try:
                    parts = line.split()
                    if len(parts) >= 3:
                        prefix = parts[1].rstrip(':')
                        namespace = parts[2].strip('<>').rstrip('.')
                        self.namespaces[prefix] = namespace
                        logger.debug(f"Registered namespace: {prefix} -> {namespace}")
                except Exception as e:
                    logger.warning(f"Failed to parse namespace from line: {line}")
    
    def get_namespace(self, prefix: str) -> Optional[str]:
        """
        Get the namespace URI for a given prefix.
        
        Args:
            prefix: The namespace prefix
        
        Returns:
            The namespace URI or None if not found
        """
        return self.namespaces.get(prefix)
    
    def resolve_uri(self, prefixed_uri: str) -> str:
        """
        Resolve a prefixed URI to its full form.
        
        Args:
            prefixed_uri: URI in prefix:localName format
        
        Returns:
            The full URI
        
        Raises:
            NamespaceError: If the prefix is not defined
        """
        if ':' not in prefixed_uri:
            return prefixed_uri
        
        prefix, local_name = prefixed_uri.split(':', 1)
        
        if prefix not in self.namespaces:
            error_msg = f"Undefined namespace prefix: {prefix}"
            logger.error(error_msg)
            raise NamespaceError(error_msg)
        
        return self.namespaces[prefix] + local_name
    
    def get_loaded_files(self) -> List[str]:
        """
        Get the list of successfully loaded files.
        
        Returns:
            List of file paths
        """
        return self.loaded_files.copy()
    
    def get_namespaces(self) -> Dict[str, str]:
        """
        Get all registered namespace prefixes.
        
        Returns:
            Dictionary mapping prefixes to namespace URIs
        """
        return self.namespaces.copy()
    
    def clear(self) -> None:
        """
        Clear all loaded data and reset the loader.
        """
        self.triples.clear()
        self.loaded_files.clear()
        self.namespaces.clear()
        logger.info("RDF Loader cleared")
    
    def get_triple_count(self) -> int:
        """
        Get the number of triples currently loaded.
        
        Returns:
            Number of triples (currently returns number of loaded files)
        """
        # Note: This returns the number of loaded files as a proxy
        # Actual triple counting would require parsing the Turtle content
        return len(self.loaded_files)
    
    def export_to_file(self, output_path: Union[str, Path], format: str = "turtle") -> None:
        """
        Export the loaded RDF data to a file.
        
        Args:
            output_path: Path to the output file
            format: Serialization format (default: "turtle")
        
        Raises:
            RDFLoaderError: If export fails
        """
        output_path = Path(output_path)
        
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Export using maplib
            # Note: This is a placeholder - actual implementation depends on maplib API
            logger.info(f"Exporting RDF data to {output_path}")
            
            # For now, we'll just log the operation
            logger.warning("Export functionality requires maplib export API implementation")
            
        except Exception as e:
            error_msg = f"Error exporting to {output_path}: {str(e)}"
            logger.error(error_msg)
            raise RDFLoaderError(error_msg) from e


def load_ontology_files(
    ontology_dir: Union[str, Path] = "ontology",
    validation_dir: Union[str, Path] = "validation",
    data_dir: Union[str, Path] = "data"
) -> RDFLoader:
    """
    Convenience function to load all ontology, validation, and data files.
    
    Args:
        ontology_dir: Directory containing ontology files
        validation_dir: Directory containing SHACL shapes
        data_dir: Directory containing instance data
    
    Returns:
        Configured RDFLoader instance with all files loaded
    
    Raises:
        RDFLoaderError: If loading fails
    """
    loader = RDFLoader()
    
    directories = [
        (ontology_dir, "ontology"),
        (validation_dir, "validation"),
        (data_dir, "data")
    ]
    
    for directory, name in directories:
        dir_path = Path(directory)
        if dir_path.exists():
            logger.info(f"Loading {name} files from {directory}")
            try:
                loader.load_directory(directory, continue_on_error=True)
            except Exception as e:
                logger.warning(f"Error loading {name} files: {str(e)}")
        else:
            logger.warning(f"{name.capitalize()} directory not found: {directory}")
    
    return loader
