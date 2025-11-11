"""
Test script to verify automatic ontology loading on startup.

This script tests the startup initialization functionality to ensure
it correctly loads ontology files and handles errors appropriately.
"""

import sys
import os
from pathlib import Path

# Change to the script's directory (project root)
script_dir = Path(__file__).parent
os.chdir(script_dir)

# Add src to path
sys.path.insert(0, str(script_dir / 'src'))

from ontology.startup import load_startup_files


def test_startup_loading():
    """Test the startup loading functionality."""
    print("Testing automatic ontology loading...")
    print("=" * 70)
    
    # Run the startup loading
    success, loaded_files, failed_files = load_startup_files()
    
    print("\n" + "=" * 70)
    print("TEST RESULTS:")
    print("=" * 70)
    
    # Check results
    if success:
        print("✓ Startup loading test PASSED")
        print(f"  - All {len(loaded_files)} files loaded successfully")
        print(f"  - No files failed to load")
        return 0
    elif len(loaded_files) > 0:
        print("⚠ Startup loading test PASSED WITH WARNINGS")
        print(f"  - {len(loaded_files)} files loaded successfully")
        print(f"  - {len(failed_files)} files failed to load")
        return 0
    else:
        print("✗ Startup loading test FAILED")
        print(f"  - No files were loaded")
        print(f"  - {len(failed_files)} files failed to load")
        return 1


if __name__ == '__main__':
    exit_code = test_startup_loading()
    sys.exit(exit_code)
