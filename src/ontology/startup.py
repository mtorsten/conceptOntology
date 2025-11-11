"""
Startup Initialization Script

This script automatically loads ontology files when the container starts.
It loads core.ttl, extensions.ttl, and shapes.ttl from their respective directories,
logs the loading status, and handles any errors during startup.

This script is executed before the API server starts to ensure all ontology
data is available when the service becomes ready.
"""

import logging
import sys
from pathlib import Path
from typing import List, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def load_startup_files() -> Tuple[bool, List[str], List[str]]:
    """
    Load ontology files during container startup.
    
    Loads the following files in order:
    1. ontology/core.ttl - Core ontology definitions
    2. ontology/extensions.ttl - Domain-specific extensions
    3. validation/shapes.ttl - SHACL validation shapes
    
    Returns:
        Tuple of (success, loaded_files, failed_files)
    """
    try:
        from ontology.loader import RDFLoader
    except ImportError as e:
        logger.error(f"Failed to import RDFLoader: {e}")
        return False, [], []
    
    logger.info("=" * 70)
    logger.info("ONTOLOGY STARTUP INITIALIZATION")
    logger.info("=" * 70)
    
    # Determine the base directory (app root)
    # When running in Docker, the working directory is /app
    # When running locally, we need to find the project root
    base_dir = Path.cwd()
    
    # If we're in the src directory, go up one level
    if base_dir.name == 'src':
        base_dir = base_dir.parent
    
    logger.info(f"Base directory: {base_dir}")
    
    # Define files to load in order (relative to base directory)
    files_to_load = [
        base_dir / "ontology" / "core.ttl",
        base_dir / "ontology" / "extensions.ttl",
        base_dir / "validation" / "shapes.ttl"
    ]
    
    # Initialize loader
    loader = RDFLoader()
    
    loaded_files = []
    failed_files = []
    
    # Load each file
    for file_path in files_to_load:
        # Check if file exists
        if not file_path.exists():
            logger.warning(f"File not found: {file_path} - Skipping")
            continue
        
        logger.info(f"Loading: {file_path}")
        
        try:
            # Load the file
            loader.load_file(str(file_path), validate=True)
            loaded_files.append(str(file_path))
            logger.info(f"✓ Successfully loaded: {file_path}")
            
        except Exception as e:
            failed_files.append(str(file_path))
            logger.error(f"✗ Failed to load {file_path}: {str(e)}")
    
    # Log summary
    logger.info("-" * 70)
    logger.info(f"STARTUP LOADING SUMMARY:")
    logger.info(f"  Total files attempted: {len(files_to_load)}")
    logger.info(f"  Successfully loaded: {len(loaded_files)}")
    logger.info(f"  Failed to load: {len(failed_files)}")
    
    if loaded_files:
        logger.info(f"  Loaded files:")
        for file in loaded_files:
            logger.info(f"    - {file}")
    
    if failed_files:
        logger.warning(f"  Failed files:")
        for file in failed_files:
            logger.warning(f"    - {file}")
    
    # Log namespace information
    namespaces = loader.get_namespaces()
    if namespaces:
        logger.info(f"  Registered namespaces: {len(namespaces)}")
        for prefix, uri in namespaces.items():
            logger.info(f"    {prefix}: {uri}")
    
    logger.info("=" * 70)
    
    # Determine overall success
    success = len(loaded_files) > 0 and len(failed_files) == 0
    
    if success:
        logger.info("✓ Startup initialization completed successfully")
    elif len(loaded_files) > 0:
        logger.warning("⚠ Startup initialization completed with some failures")
    else:
        logger.error("✗ Startup initialization failed - no files loaded")
    
    logger.info("=" * 70)
    
    return success, loaded_files, failed_files


def main():
    """
    Main entry point for startup initialization.
    
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    try:
        success, loaded_files, failed_files = load_startup_files()
        
        # Exit with appropriate code
        if success:
            logger.info("Startup initialization successful - proceeding to start API server")
            return 0
        elif len(loaded_files) > 0:
            logger.warning("Startup initialization completed with warnings - proceeding to start API server")
            return 0
        else:
            logger.error("Startup initialization failed - API server may not function correctly")
            # Don't fail the container startup, just log the error
            return 0
            
    except Exception as e:
        logger.error(f"Unexpected error during startup initialization: {str(e)}")
        logger.exception(e)
        # Don't fail the container startup, just log the error
        return 0


if __name__ == '__main__':
    sys.exit(main())
