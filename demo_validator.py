"""
SHACL Validator Demonstration

This script demonstrates the key features of the SHACL validator module.
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / 'src'))

from ontology.validator import create_validator, ValidationResult, SeverityLevel


def main():
    print("=" * 70)
    print("SHACL Validator Demonstration")
    print("=" * 70)
    
    # Create validator with loaded ontology and shapes
    print("\n1. Creating validator with loaded data...")
    validator = create_validator()
    
    stats = validator.get_statistics()
    print(f"   - Shapes loaded: {stats['shapes_loaded']}")
    print(f"   - Shape files: {', '.join(stats['shape_files'])}")
    
    # Execute validation
    print("\n2. Executing SHACL validation...")
    report = validator.validate()
    print(f"   - Validation completed: {report}")
    
    # Get summary
    print("\n3. Validation summary:")
    summary = validator.get_summary(report)
    print(f"   - Conforms: {summary['conforms']}")
    print(f"   - Total results: {summary['total_results']}")
    print(f"   - Violations: {summary['violation_count']}")
    print(f"   - Warnings: {summary['warning_count']}")
    print(f"   - Info: {summary['info_count']}")
    print(f"   - Affected nodes: {summary['affected_nodes']}")
    
    # Check if valid
    print("\n4. Checking validity:")
    is_valid = validator.is_valid(report)
    print(f"   - Data is valid: {is_valid}")
    
    # Export report in Turtle format
    print("\n5. Exporting validation report...")
    output_file = Path("output/validation_report.ttl")
    validator.export_report(report, output_file)
    print(f"   - Report exported to: {output_file}")
    
    # Format report as text
    print("\n6. Formatted text report:")
    text_report = validator.format_report(report, format="text", include_details=True)
    print(text_report)
    
    # Demonstrate with sample violations
    print("\n7. Demonstrating report with sample violations:")
    from ontology.validator import ValidationReport
    
    sample_report = ValidationReport(conforms=False)
    
    # Add sample violations
    sample_report.add_result(ValidationResult(
        focus_node="http://example.org/entity1",
        result_path="http://example.org/ontology#hasIdentifier",
        value=None,
        message="Entity must have exactly one identifier",
        severity=SeverityLevel.VIOLATION,
        source_shape="http://example.org/ontology#EntityShape"
    ))
    
    sample_report.add_result(ValidationResult(
        focus_node="http://example.org/entity1",
        result_path="http://example.org/ontology#hasDescription",
        value=None,
        message="Entity should have a description",
        severity=SeverityLevel.WARNING,
        source_shape="http://example.org/ontology#EntityShape"
    ))
    
    print(f"   - Sample report: {sample_report}")
    
    # Export sample report
    sample_output = Path("output/sample_validation_report.ttl")
    validator.export_report(sample_report, sample_output)
    print(f"   - Sample report exported to: {sample_output}")
    
    # Show formatted sample report
    print("\n8. Formatted sample report:")
    sample_text = validator.format_report(sample_report, format="text", include_details=True)
    print(sample_text)
    
    print("\n" + "=" * 70)
    print("Demonstration completed successfully!")
    print("=" * 70)


if __name__ == "__main__":
    main()
