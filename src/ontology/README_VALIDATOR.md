# SHACL Validator Module

## Overview

The SHACL Validator module provides comprehensive functionality for validating RDF data against SHACL (Shapes Constraint Language) shapes using maplib. It supports loading shapes from Turtle files, executing validation, generating detailed reports, and exporting results in multiple formats.

## Features

- **Load SHACL Shapes**: Load shapes from single files or entire directories
- **Execute Validation**: Validate RDF data against loaded shapes
- **Detailed Reports**: Generate comprehensive validation reports with:
  - Focus nodes (the RDF nodes being validated)
  - Result paths (the properties that failed validation)
  - Constraint details (what constraint was violated)
  - Severity levels (Violation, Warning, Info)
- **Summary Statistics**: Get aggregated statistics about validation results
- **Multiple Export Formats**: Export reports in Turtle, text, or Markdown format
- **Result Grouping**: Group results by focus node or shape for analysis

## Quick Start

```python
from ontology.validator import create_validator

# Create validator with loaded ontology and shapes
validator = create_validator()

# Execute validation
report = validator.validate()

# Check if data is valid
if validator.is_valid(report):
    print("Data is valid!")
else:
    print(f"Found {len(report.get_violations())} violations")

# Export report
validator.export_report(report, "output/validation_report.ttl")
```

## Core Classes

### SHACLValidator

Main validator class that handles shape loading and validation execution.

**Key Methods:**
- `load_shapes(file_path)`: Load SHACL shapes from a Turtle file
- `load_shapes_directory(directory_path)`: Load all shapes from a directory
- `validate()`: Execute validation and return a ValidationReport
- `is_valid(report)`: Check if data conforms (no violations)
- `export_report(report, output_path)`: Export report in Turtle format
- `format_report(report, format)`: Format report as text or Markdown

### ValidationReport

Represents a complete validation report with all results.

**Key Properties:**
- `conforms`: Boolean indicating if data conforms to all shapes
- `results`: List of ValidationResult objects
- `timestamp`: When the validation was executed

**Key Methods:**
- `get_violations()`: Get all violation-level results
- `get_warnings()`: Get all warning-level results
- `get_info()`: Get all info-level results
- `get_summary()`: Get summary statistics

### ValidationResult

Represents a single validation result.

**Key Properties:**
- `focus_node`: The RDF node that was validated
- `result_path`: The property path that failed validation
- `value`: The value that caused the violation
- `message`: Human-readable validation message
- `severity`: Severity level (Violation, Warning, Info)
- `source_constraint`: The constraint component that was violated
- `source_shape`: The shape that defined the constraint

### SeverityLevel

Constants for SHACL severity levels:
- `VIOLATION`: Critical constraint violations
- `WARNING`: Non-critical issues
- `INFO`: Informational messages

## Usage Examples

### Basic Validation

```python
from ontology.validator import SHACLValidator
from ontology.loader import load_ontology_files

# Load RDF data
loader = load_ontology_files()

# Create validator
validator = SHACLValidator(loader)

# Load shapes
validator.load_shapes("validation/shapes.ttl")

# Execute validation
report = validator.validate()

# Display summary
summary = validator.get_summary(report)
print(f"Violations: {summary['violation_count']}")
print(f"Warnings: {summary['warning_count']}")
```

### Validate Specific Node

```python
# Validate a specific RDF node
node_report = validator.validate_node(
    "http://example.org/entity1",
    shape_uri="http://example.org/ontology#EntityShape"
)

print(f"Node validation: {node_report}")
```

### Export Reports

```python
# Export in Turtle format
validator.export_report(report, "output/validation_report.ttl")

# Format as text
text_report = validator.format_report(report, format="text")
print(text_report)

# Format as Markdown
md_report = validator.format_report(report, format="markdown")
with open("output/report.md", "w") as f:
    f.write(md_report)
```

### Group Results

```python
# Group results by focus node
by_node = validator.get_results_by_focus_node(report)
for node, results in by_node.items():
    print(f"{node}: {len(results)} issues")

# Group results by shape
by_shape = validator.get_results_by_shape(report)
for shape, results in by_shape.items():
    print(f"{shape}: {len(results)} issues")
```

### Filter by Severity

```python
# Get only violations
violations = report.get_violations()
for violation in violations:
    print(f"Violation: {violation.focus_node} - {violation.message}")

# Get only warnings
warnings = report.get_warnings()
for warning in warnings:
    print(f"Warning: {warning.focus_node} - {warning.message}")
```

## Validation Report Format

The validator exports reports in standard SHACL validation report format (Turtle):

```turtle
@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix : <http://example.org/validation#> .

:report_20251110_165148 a sh:ValidationReport ;
    sh:conforms false ;
    rdfs:label "SHACL Validation Report" ;
    :totalResults 2 ;
    :violationCount 1 ;
    :warningCount 1 ;
    sh:result :result_1 , :result_2 .

:result_1 a sh:ValidationResult ;
    sh:focusNode <http://example.org/entity1> ;
    sh:resultPath <http://example.org/ontology#hasIdentifier> ;
    sh:resultMessage "Entity must have exactly one identifier"@en ;
    sh:resultSeverity <http://www.w3.org/ns/shacl#Violation> ;
    sh:sourceShape <http://example.org/ontology#EntityShape> .
```

## Integration with Other Modules

The validator integrates seamlessly with other ontology modules:

```python
from ontology.loader import load_ontology_files
from ontology.query import create_query_engine
from ontology.validator import create_validator

# Load all data
loader = load_ontology_files()

# Create query engine
query_engine = create_query_engine()

# Create validator
validator = create_validator()

# Validate data
report = validator.validate()

# Query validation results if needed
if not validator.is_valid(report):
    # Use query engine to investigate issues
    pass
```

## Testing

Run the demonstration script to see all features in action:

```bash
python demo_validator.py
```

Run the test suite:

```bash
python test_validator.py
```

## Requirements

- Python 3.11+
- maplib (for RDF operations and SHACL validation)
- ontology.loader module (for loading RDF data)

## Notes

- The current implementation provides the complete validator infrastructure
- Actual SHACL validation execution requires maplib's validation API
- The module includes placeholder simulation for demonstration purposes
- All validation report structures follow W3C SHACL specification
- Reports can be consumed by other SHACL-compliant tools

## Future Enhancements

- Integration with maplib's native SHACL validation engine
- Support for custom constraint components
- Real-time validation on data changes
- Validation result caching for performance
- Advanced SPARQL-based constraints
- Validation report comparison and diff
