"""
Test script for SHACL Validator

This script demonstrates the functionality of the SHACL validator.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from ontology.validator import (
    SHACLValidator, 
    ValidationReport, 
    ValidationResult,
    SeverityLevel,
    create_validator
)
from ontology.loader import load_ontology_files


def test_severity_levels():
    """Test severity level functionality."""
    print("\n" + "=" * 60)
    print("TEST: Severity Levels")
    print("=" * 60)
    
    print("\nSeverity level URIs:")
    for level in SeverityLevel.all_levels():
        label = SeverityLevel.get_label(level)
        print(f"  {label}: {level}")


def test_validation_result():
    """Test ValidationResult class."""
    print("\n" + "=" * 60)
    print("TEST: Validation Result")
    print("=" * 60)
    
    # Create sample validation result
    result = ValidationResult(
        focus_node="http://example.org/entity1",
        result_path="http://example.org/ontology#hasName",
        value="test",
        message="Entity must have at least one name",
        severity=SeverityLevel.VIOLATION,
        source_constraint="sh:minCount",
        source_shape="http://example.org/ontology#EntityShape"
    )
    
    print(f"\nValidation Result:")
    print(f"  {result}")
    
    print(f"\nResult as dictionary:")
    result_dict = result.to_dict()
    for key, value in result_dict.items():
        print(f"  {key}: {value}")


def test_validation_report():
    """Test ValidationReport class."""
    print("\n" + "=" * 60)
    print("TEST: Validation Report")
    print("=" * 60)
    
    # Create validation report
    report = ValidationReport(conforms=True)
    
    # Add sample results
    results = [
        ValidationResult(
            focus_node="http://example.org/entity1",
            result_path="http://example.org/ontology#hasIdentifier",
            value=None,
            message="Entity must have exactly one identifier",
            severity=SeverityLevel.VIOLATION
        ),
        ValidationResult(
            focus_node="http://example.org/entity1",
            result_path="http://example.org/ontology#hasDescription",
            value=None,
            message="Entity should have a description",
            severity=SeverityLevel.WARNING
        ),
        ValidationResult(
            focus_node="http://example.org/entity2",
            result_path="http://example.org/ontology#hasValue",
            value="123",
            message="Entity may have a numeric value",
            severity=SeverityLevel.INFO
        ),
    ]
    
    for result in results:
        report.add_result(result)
    
    print(f"\nValidation Report: {report}")
    
    print(f"\nSummary:")
    summary = report.get_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print(f"\nViolations: {len(report.get_violations())}")
    print(f"Warnings: {len(report.get_warnings())}")
    print(f"Info: {len(report.get_info())}")


def test_shape_loading():
    """Test loading SHACL shapes."""
    print("\n" + "=" * 60)
    print("TEST: Shape Loading")
    print("=" * 60)
    
    validator = SHACLValidator()
    
    # Test loading single shape file
    shapes_file = Path("validation/shapes.ttl")
    if shapes_file.exists():
        try:
            validator.load_shapes(shapes_file)
            print(f"\n✓ Loaded shapes from: {shapes_file}")
            print(f"  Total shape files loaded: {len(validator.get_loaded_shapes())}")
        except Exception as e:
            print(f"\n✗ Failed to load shapes: {str(e)}")
    else:
        print(f"\n✗ Shapes file not found: {shapes_file}")
    
    # Test loading from directory
    validator2 = SHACLValidator()
    validation_dir = Path("validation")
    if validation_dir.exists():
        try:
            successful, failed = validator2.load_shapes_directory(validation_dir)
            print(f"\n✓ Loaded shapes from directory: {validation_dir}")
            print(f"  Successful: {len(successful)}")
            print(f"  Failed: {len(failed)}")
        except Exception as e:
            print(f"\n✗ Failed to load shapes directory: {str(e)}")


def test_validator_with_data():
    """Test validator with loaded RDF data."""
    print("\n" + "=" * 60)
    print("TEST: Validator with Loaded Data")
    print("=" * 60)
    
    try:
        # Load ontology files
        loader = load_ontology_files()
        print(f"\nLoaded {loader.get_triple_count()} files")
        
        # Create validator
        validator = SHACLValidator(loader)
        
        # Load shapes
        shapes_file = Path("validation/shapes.ttl")
        if shapes_file.exists():
            validator.load_shapes(shapes_file)
            print(f"Loaded shapes from: {shapes_file}")
        
        # Get validator statistics
        stats = validator.get_statistics()
        print(f"\nValidator Statistics:")
        for key, value in stats.items():
            if key != 'shape_files':
                print(f"  {key}: {value}")
        
        # Execute validation
        print("\nExecuting validation...")
        report = validator.validate()
        
        print(f"\nValidation completed: {report}")
        
        # Check if valid
        is_valid = validator.is_valid(report)
        print(f"Data is valid: {is_valid}")
        
        # Get summary
        summary = validator.get_summary(report)
        print(f"\nDetailed Summary:")
        for key, value in summary.items():
            print(f"  {key}: {value}")
        
    except Exception as e:
        print(f"Error: {str(e)}")


def test_report_formatting():
    """Test validation report formatting."""
    print("\n" + "=" * 60)
    print("TEST: Report Formatting")
    print("=" * 60)
    
    # Create sample report
    report = ValidationReport(conforms=False)
    
    # Add sample results
    report.add_result(ValidationResult(
        focus_node="http://example.org/entity1",
        result_path="http://example.org/ontology#hasIdentifier",
        value=None,
        message="Entity must have exactly one identifier",
        severity=SeverityLevel.VIOLATION,
        source_shape="http://example.org/ontology#EntityShape"
    ))
    
    report.add_result(ValidationResult(
        focus_node="http://example.org/entity1",
        result_path="http://example.org/ontology#hasDescription",
        value=None,
        message="Entity should have a description",
        severity=SeverityLevel.WARNING,
        source_shape="http://example.org/ontology#EntityShape"
    ))
    
    validator = SHACLValidator()
    
    # Test text format
    print("\n--- Text Format ---")
    text_report = validator.format_report(report, format="text", include_details=True)
    print(text_report)
    
    # Test markdown format
    print("\n--- Markdown Format ---")
    md_report = validator.format_report(report, format="markdown", include_details=True)
    print(md_report)


def test_report_export():
    """Test exporting validation reports."""
    print("\n" + "=" * 60)
    print("TEST: Report Export")
    print("=" * 60)
    
    # Create sample report
    report = ValidationReport(conforms=False)
    
    report.add_result(ValidationResult(
        focus_node="http://example.org/entity1",
        result_path="http://example.org/ontology#hasIdentifier",
        value=None,
        message="Entity must have exactly one identifier",
        severity=SeverityLevel.VIOLATION,
        source_shape="http://example.org/ontology#EntityShape"
    ))
    
    validator = SHACLValidator()
    
    # Export to Turtle
    output_dir = Path("output")
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "test_validation_report.ttl"
    
    try:
        validator.export_report(report, output_file)
        print(f"\n✓ Report exported to: {output_file}")
        
        # Read and display the exported file
        if output_file.exists():
            print(f"\nExported content (first 20 lines):")
            with open(output_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines[:20]:
                    print(f"  {line.rstrip()}")
                if len(lines) > 20:
                    print(f"  ... ({len(lines) - 20} more lines)")
    except Exception as e:
        print(f"\n✗ Export failed: {str(e)}")


def test_result_grouping():
    """Test grouping validation results."""
    print("\n" + "=" * 60)
    print("TEST: Result Grouping")
    print("=" * 60)
    
    # Create report with multiple results
    report = ValidationReport(conforms=False)
    
    results = [
        ValidationResult(
            focus_node="http://example.org/entity1",
            result_path="http://example.org/ontology#hasIdentifier",
            value=None,
            message="Missing identifier",
            severity=SeverityLevel.VIOLATION,
            source_shape="http://example.org/ontology#EntityShape"
        ),
        ValidationResult(
            focus_node="http://example.org/entity1",
            result_path="http://example.org/ontology#hasName",
            value=None,
            message="Missing name",
            severity=SeverityLevel.VIOLATION,
            source_shape="http://example.org/ontology#EntityShape"
        ),
        ValidationResult(
            focus_node="http://example.org/entity2",
            result_path="http://example.org/ontology#hasIdentifier",
            value=None,
            message="Missing identifier",
            severity=SeverityLevel.VIOLATION,
            source_shape="http://example.org/ontology#EntityShape"
        ),
    ]
    
    for result in results:
        report.add_result(result)
    
    validator = SHACLValidator()
    
    # Group by focus node
    print("\nResults grouped by focus node:")
    by_node = validator.get_results_by_focus_node(report)
    for node, node_results in by_node.items():
        print(f"  {node}: {len(node_results)} results")
    
    # Group by shape
    print("\nResults grouped by shape:")
    by_shape = validator.get_results_by_shape(report)
    for shape, shape_results in by_shape.items():
        print(f"  {shape}: {len(shape_results)} results")


def test_create_validator():
    """Test convenience function for creating validator."""
    print("\n" + "=" * 60)
    print("TEST: Create Validator Convenience Function")
    print("=" * 60)
    
    try:
        validator = create_validator()
        
        print(f"\n✓ Validator created successfully")
        
        stats = validator.get_statistics()
        print(f"\nValidator Statistics:")
        print(f"  Shapes loaded: {stats['shapes_loaded']}")
        print(f"  Validation count: {stats['validation_count']}")
        
        if validator.rdf_loader:
            print(f"  RDF files loaded: {validator.rdf_loader.get_triple_count()}")
        
    except Exception as e:
        print(f"\n✗ Failed to create validator: {str(e)}")


def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("SHACL Validator Test Suite")
    print("=" * 60)
    
    test_severity_levels()
    test_validation_result()
    test_validation_report()
    test_shape_loading()
    test_validator_with_data()
    test_report_formatting()
    test_report_export()
    test_result_grouping()
    test_create_validator()
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
