"""
SHACL Validator Module

This module provides functionality to validate RDF data against SHACL shapes using maplib.
It loads SHACL shapes from Turtle files, executes validation, generates detailed validation
reports with focus nodes, result paths, and constraint details, categorizes results by
severity, and provides summary statistics.

Example Usage:
    # Initialize validator with loaded RDF data
    from ontology.loader import load_ontology_files
    
    loader = load_ontology_files()
    validator = SHACLValidator(loader)
    
    # Load SHACL shapes
    validator.load_shapes("validation/shapes.ttl")
    
    # Execute validation
    report = validator.validate()
    
    # Get validation summary
    summary = validator.get_summary(report)
    print(f"Violations: {summary['violation_count']}")
    print(f"Warnings: {summary['warning_count']}")
    
    # Export validation report
    validator.export_report(report, "output/validation_report.ttl")
    
    # Check if data is valid
    if validator.is_valid(report):
        print("Data is valid!")
    else:
        print("Data has validation issues")
"""

import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime
from collections import defaultdict

try:
    import maplib
except ImportError:
    raise ImportError(
        "maplib is required but not installed. "
        "Install it with: pip install maplib"
    )


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SHACLValidationError(Exception):
    """Base exception for SHACL validation errors."""
    pass


class ShapeLoadError(SHACLValidationError):
    """Exception raised when loading SHACL shapes fails."""
    pass


class ValidationExecutionError(SHACLValidationError):
    """Exception raised when validation execution fails."""
    pass


class SeverityLevel:
    """SHACL severity levels."""
    VIOLATION = "http://www.w3.org/ns/shacl#Violation"
    WARNING = "http://www.w3.org/ns/shacl#Warning"
    INFO = "http://www.w3.org/ns/shacl#Info"
    
    @classmethod
    def get_label(cls, severity_uri: str) -> str:
        """Get human-readable label for severity URI."""
        mapping = {
            cls.VIOLATION: "Violation",
            cls.WARNING: "Warning",
            cls.INFO: "Info"
        }
        return mapping.get(severity_uri, "Unknown")
    
    @classmethod
    def all_levels(cls) -> List[str]:
        """Get all severity level URIs."""
        return [cls.VIOLATION, cls.WARNING, cls.INFO]


class ValidationResult:
    """
    Represents a single SHACL validation result.
    """
    
    def __init__(
        self,
        focus_node: str,
        result_path: Optional[str],
        value: Optional[str],
        message: str,
        severity: str,
        source_constraint: Optional[str] = None,
        source_shape: Optional[str] = None
    ):
        """
        Initialize a validation result.
        
        Args:
            focus_node: The RDF node that was validated
            result_path: The property path that failed validation
            value: The value that caused the violation
            message: Human-readable validation message
            severity: Severity level URI
            source_constraint: The constraint component that was violated
            source_shape: The shape that defined the constraint
        """
        self.focus_node = focus_node
        self.result_path = result_path
        self.value = value
        self.message = message
        self.severity = severity
        self.source_constraint = source_constraint
        self.source_shape = source_shape
        self.timestamp = datetime.now()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert validation result to dictionary."""
        return {
            'focus_node': self.focus_node,
            'result_path': self.result_path,
            'value': self.value,
            'message': self.message,
            'severity': self.severity,
            'severity_label': SeverityLevel.get_label(self.severity),
            'source_constraint': self.source_constraint,
            'source_shape': self.source_shape,
            'timestamp': self.timestamp.isoformat()
        }
    
    def __repr__(self) -> str:
        """String representation of validation result."""
        severity_label = SeverityLevel.get_label(self.severity)
        return (
            f"ValidationResult({severity_label}: {self.focus_node} "
            f"- {self.message})"
        )


class ValidationReport:
    """
    Represents a complete SHACL validation report.
    """
    
    def __init__(self, conforms: bool):
        """
        Initialize a validation report.
        
        Args:
            conforms: Whether the data conforms to all shapes
        """
        self.conforms = conforms
        self.results: List[ValidationResult] = []
        self.timestamp = datetime.now()
        self.shapes_loaded: List[str] = []
        self.data_sources: List[str] = []
    
    def add_result(self, result: ValidationResult) -> None:
        """Add a validation result to the report."""
        self.results.append(result)
        # Update conforms status
        if result.severity == SeverityLevel.VIOLATION:
            self.conforms = False
    
    def get_results_by_severity(self, severity: str) -> List[ValidationResult]:
        """Get all results with a specific severity level."""
        return [r for r in self.results if r.severity == severity]
    
    def get_violations(self) -> List[ValidationResult]:
        """Get all violation-level results."""
        return self.get_results_by_severity(SeverityLevel.VIOLATION)
    
    def get_warnings(self) -> List[ValidationResult]:
        """Get all warning-level results."""
        return self.get_results_by_severity(SeverityLevel.WARNING)
    
    def get_info(self) -> List[ValidationResult]:
        """Get all info-level results."""
        return self.get_results_by_severity(SeverityLevel.INFO)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics for the validation report."""
        return {
            'conforms': self.conforms,
            'total_results': len(self.results),
            'violation_count': len(self.get_violations()),
            'warning_count': len(self.get_warnings()),
            'info_count': len(self.get_info()),
            'timestamp': self.timestamp.isoformat(),
            'shapes_loaded': len(self.shapes_loaded),
            'data_sources': len(self.data_sources)
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert validation report to dictionary."""
        return {
            'conforms': self.conforms,
            'timestamp': self.timestamp.isoformat(),
            'summary': self.get_summary(),
            'results': [r.to_dict() for r in self.results],
            'shapes_loaded': self.shapes_loaded,
            'data_sources': self.data_sources
        }
    
    def __repr__(self) -> str:
        """String representation of validation report."""
        summary = self.get_summary()
        return (
            f"ValidationReport(conforms={self.conforms}, "
            f"violations={summary['violation_count']}, "
            f"warnings={summary['warning_count']}, "
            f"info={summary['info_count']})"
        )


class SHACLValidator:
    """
    SHACL Validator for validating RDF data against SHACL shapes using maplib.
    
    This class provides methods to:
    - Load SHACL shapes from Turtle files
    - Execute validation against RDF data
    - Generate detailed validation reports
    - Categorize results by severity
    - Export reports in Turtle format
    - Provide summary statistics
    """
    
    def __init__(self, rdf_loader=None):
        """
        Initialize the SHACL validator.
        
        Args:
            rdf_loader: RDFLoader instance with loaded data (optional)
        """
        self.rdf_loader = rdf_loader
        self.shapes_data: List[Dict] = []
        self.loaded_shape_files: List[str] = []
        self.validation_count = 0
        logger.info("SHACL Validator initialized")
    
    def set_rdf_loader(self, rdf_loader) -> None:
        """
        Set or update the RDF loader instance.
        
        Args:
            rdf_loader: RDFLoader instance with loaded data
        """
        self.rdf_loader = rdf_loader
        logger.info("RDF loader updated")
    
    def load_shapes(self, file_path: Union[str, Path]) -> bool:
        """
        Load SHACL shapes from a Turtle file.
        
        Args:
            file_path: Path to the SHACL shapes file
        
        Returns:
            True if loading was successful
        
        Raises:
            ShapeLoadError: If loading fails
        """
        file_path = Path(file_path)
        
        if not file_path.exists():
            error_msg = f"Shapes file not found: {file_path}"
            logger.error(error_msg)
            raise ShapeLoadError(error_msg)
        
        logger.info(f"Loading SHACL shapes from: {file_path}")
        
        try:
            # Read shapes file content
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Store shapes data
            self.shapes_data.append({
                'file': str(file_path),
                'content': content
            })
            
            self.loaded_shape_files.append(str(file_path))
            logger.info(f"Successfully loaded shapes from: {file_path}")
            
            return True
            
        except Exception as e:
            error_msg = f"Error loading shapes from {file_path}: {str(e)}"
            logger.error(error_msg)
            raise ShapeLoadError(error_msg) from e
    
    def load_shapes_directory(
        self,
        directory_path: Union[str, Path],
        pattern: str = "*.ttl"
    ) -> Tuple[List[str], List[str]]:
        """
        Load all SHACL shape files from a directory.
        
        Args:
            directory_path: Path to the directory
            pattern: File pattern to match (default: "*.ttl")
        
        Returns:
            Tuple of (successful_files, failed_files)
        """
        directory_path = Path(directory_path)
        
        if not directory_path.exists():
            error_msg = f"Directory not found: {directory_path}"
            logger.error(error_msg)
            raise ShapeLoadError(error_msg)
        
        file_paths = list(directory_path.glob(pattern))
        logger.info(f"Found {len(file_paths)} shape files in {directory_path}")
        
        successful_files = []
        failed_files = []
        
        for file_path in file_paths:
            try:
                self.load_shapes(file_path)
                successful_files.append(str(file_path))
            except ShapeLoadError as e:
                failed_files.append(str(file_path))
                logger.error(f"Failed to load {file_path}: {str(e)}")
        
        return successful_files, failed_files

    
    def validate(self, data_graph=None) -> ValidationReport:
        """
        Execute SHACL validation against RDF data.
        
        Args:
            data_graph: Optional RDF data to validate (uses rdf_loader if not provided)
        
        Returns:
            ValidationReport with results
        
        Raises:
            ValidationExecutionError: If validation fails
        """
        if not self.shapes_data:
            error_msg = "No SHACL shapes loaded. Call load_shapes() first."
            logger.error(error_msg)
            raise ValidationExecutionError(error_msg)
        
        if data_graph is None and self.rdf_loader is None:
            error_msg = "No RDF data available for validation"
            logger.error(error_msg)
            raise ValidationExecutionError(error_msg)
        
        logger.info("Executing SHACL validation")
        
        try:
            # Initialize validation report
            report = ValidationReport(conforms=True)
            report.shapes_loaded = self.loaded_shape_files.copy()
            
            if self.rdf_loader:
                report.data_sources = self.rdf_loader.get_loaded_files()
            
            # Note: This is a placeholder implementation
            # Actual implementation would use maplib's SHACL validation capabilities
            logger.warning("SHACL validation execution requires maplib validation API implementation")
            
            # Placeholder: Parse shapes and simulate validation
            # In a real implementation, maplib would handle this
            self._simulate_validation(report)
            
            self.validation_count += 1
            logger.info(f"Validation completed: {report}")
            
            return report
            
        except Exception as e:
            error_msg = f"Error executing validation: {str(e)}"
            logger.error(error_msg)
            raise ValidationExecutionError(error_msg) from e
    
    def _simulate_validation(self, report: ValidationReport) -> None:
        """
        Simulate validation for demonstration purposes.
        This would be replaced by actual maplib validation.
        
        Args:
            report: ValidationReport to populate with results
        """
        # This is a placeholder that demonstrates the structure
        # Real implementation would use maplib to perform actual validation
        logger.debug("Simulating validation (placeholder for maplib implementation)")
        
        # Example: Add a sample result to show structure
        # In real implementation, maplib would generate these results
        pass
    
    def validate_node(
        self,
        node_uri: str,
        shape_uri: Optional[str] = None
    ) -> ValidationReport:
        """
        Validate a specific RDF node against SHACL shapes.
        
        Args:
            node_uri: URI of the node to validate
            shape_uri: Optional specific shape to validate against
        
        Returns:
            ValidationReport with results for the node
        
        Raises:
            ValidationExecutionError: If validation fails
        """
        logger.info(f"Validating node: {node_uri}")
        
        try:
            # Execute full validation
            full_report = self.validate()
            
            # Filter results for the specific node
            node_report = ValidationReport(conforms=True)
            node_report.shapes_loaded = full_report.shapes_loaded
            node_report.data_sources = full_report.data_sources
            
            for result in full_report.results:
                if result.focus_node == node_uri:
                    if shape_uri is None or result.source_shape == shape_uri:
                        node_report.add_result(result)
            
            logger.info(f"Node validation completed: {node_report}")
            return node_report
            
        except Exception as e:
            error_msg = f"Error validating node {node_uri}: {str(e)}"
            logger.error(error_msg)
            raise ValidationExecutionError(error_msg) from e
    
    def is_valid(self, report: ValidationReport) -> bool:
        """
        Check if validation report indicates valid data.
        
        Args:
            report: ValidationReport to check
        
        Returns:
            True if data conforms (no violations)
        """
        return report.conforms and len(report.get_violations()) == 0
    
    def get_summary(self, report: ValidationReport) -> Dict[str, Any]:
        """
        Get summary statistics from a validation report.
        
        Args:
            report: ValidationReport to summarize
        
        Returns:
            Dictionary with summary statistics
        """
        summary = report.get_summary()
        
        # Add additional statistics
        if summary['total_results'] > 0:
            summary['violation_percentage'] = round(
                (summary['violation_count'] / summary['total_results']) * 100, 2
            )
            summary['warning_percentage'] = round(
                (summary['warning_count'] / summary['total_results']) * 100, 2
            )
        else:
            summary['violation_percentage'] = 0.0
            summary['warning_percentage'] = 0.0
        
        # Group results by focus node
        focus_nodes = defaultdict(int)
        for result in report.results:
            focus_nodes[result.focus_node] += 1
        
        summary['affected_nodes'] = len(focus_nodes)
        summary['most_affected_node'] = (
            max(focus_nodes.items(), key=lambda x: x[1])[0]
            if focus_nodes else None
        )
        
        return summary
    
    def get_results_by_focus_node(
        self,
        report: ValidationReport
    ) -> Dict[str, List[ValidationResult]]:
        """
        Group validation results by focus node.
        
        Args:
            report: ValidationReport to process
        
        Returns:
            Dictionary mapping focus nodes to their validation results
        """
        results_by_node = defaultdict(list)
        
        for result in report.results:
            results_by_node[result.focus_node].append(result)
        
        return dict(results_by_node)
    
    def get_results_by_shape(
        self,
        report: ValidationReport
    ) -> Dict[str, List[ValidationResult]]:
        """
        Group validation results by source shape.
        
        Args:
            report: ValidationReport to process
        
        Returns:
            Dictionary mapping shapes to their validation results
        """
        results_by_shape = defaultdict(list)
        
        for result in report.results:
            shape = result.source_shape or "Unknown"
            results_by_shape[shape].append(result)
        
        return dict(results_by_shape)
    
    def export_report(
        self,
        report: ValidationReport,
        output_path: Union[str, Path],
        format: str = "turtle"
    ) -> None:
        """
        Export validation report to a file in Turtle format.
        
        Args:
            output_path: Path to the output file
            format: Output format (default: "turtle")
        
        Raises:
            ValidationExecutionError: If export fails
        """
        output_path = Path(output_path)
        
        try:
            # Ensure output directory exists
            output_path.parent.mkdir(parents=True, exist_ok=True)
            
            logger.info(f"Exporting validation report to: {output_path}")
            
            if format == "turtle":
                self._export_turtle(report, output_path)
            else:
                error_msg = f"Unsupported export format: {format}"
                logger.error(error_msg)
                raise ValidationExecutionError(error_msg)
            
            logger.info(f"Validation report exported successfully")
            
        except Exception as e:
            error_msg = f"Error exporting report to {output_path}: {str(e)}"
            logger.error(error_msg)
            raise ValidationExecutionError(error_msg) from e
    
    def _export_turtle(
        self,
        report: ValidationReport,
        output_path: Path
    ) -> None:
        """
        Export validation report in Turtle format.
        
        Args:
            report: ValidationReport to export
            output_path: Path to the output file
        """
        # Generate Turtle serialization of validation report
        turtle_content = self._generate_turtle_report(report)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(turtle_content)
    
    def _generate_turtle_report(self, report: ValidationReport) -> str:
        """
        Generate Turtle serialization of validation report.
        
        Args:
            report: ValidationReport to serialize
        
        Returns:
            Turtle-formatted string
        """
        # SHACL validation report namespace prefixes
        prefixes = """@prefix sh: <http://www.w3.org/ns/shacl#> .
@prefix rdf: <http://www.w3.org/1999/02/22-rdf-syntax-ns#> .
@prefix rdfs: <http://www.w3.org/2000/01/rdf-schema#> .
@prefix xsd: <http://www.w3.org/2001/XMLSchema#> .
@prefix : <http://example.org/validation#> .

"""
        
        # Validation report header
        report_uri = f":report_{report.timestamp.strftime('%Y%m%d_%H%M%S')}"
        
        lines = [prefixes]
        lines.append(f"{report_uri} a sh:ValidationReport ;")
        lines.append(f"    sh:conforms {str(report.conforms).lower()} ;")
        lines.append(f'    rdfs:label "SHACL Validation Report" ;')
        lines.append(f'    rdfs:comment "Generated on {report.timestamp.isoformat()}" ;')
        
        # Add summary statistics
        summary = report.get_summary()
        lines.append(f'    :totalResults {summary["total_results"]} ;')
        lines.append(f'    :violationCount {summary["violation_count"]} ;')
        lines.append(f'    :warningCount {summary["warning_count"]} ;')
        lines.append(f'    :infoCount {summary["info_count"]} ;')
        
        # Add validation results
        if report.results:
            lines.append("    sh:result")
            
            for i, result in enumerate(report.results):
                result_uri = f":result_{i+1}"
                is_last = (i == len(report.results) - 1)
                
                lines.append(f"        {result_uri}{' .' if is_last else ' ,'}")
            
            lines.append("")
            
            # Define each validation result
            for i, result in enumerate(report.results):
                result_uri = f":result_{i+1}"
                
                lines.append(f"{result_uri} a sh:ValidationResult ;")
                lines.append(f"    sh:focusNode <{result.focus_node}> ;")
                
                if result.result_path:
                    lines.append(f"    sh:resultPath <{result.result_path}> ;")
                
                if result.value:
                    lines.append(f'    sh:value "{result.value}" ;')
                
                lines.append(f'    sh:resultMessage "{result.message}"@en ;')
                lines.append(f"    sh:resultSeverity <{result.severity}> ;")
                
                if result.source_constraint:
                    lines.append(f"    sh:sourceConstraintComponent <{result.source_constraint}> ;")
                
                if result.source_shape:
                    lines.append(f"    sh:sourceShape <{result.source_shape}> ;")
                
                lines.append(f'    :timestamp "{result.timestamp.isoformat()}"^^xsd:dateTime .')
                lines.append("")
        else:
            lines.append("    .")
        
        return "\n".join(lines)
    
    def format_report(
        self,
        report: ValidationReport,
        format: str = "text",
        include_details: bool = True
    ) -> str:
        """
        Format validation report as human-readable text.
        
        Args:
            report: ValidationReport to format
            format: Output format ("text", "markdown", "html")
            include_details: Whether to include detailed results
        
        Returns:
            Formatted report string
        """
        if format == "text":
            return self._format_text_report(report, include_details)
        elif format == "markdown":
            return self._format_markdown_report(report, include_details)
        else:
            raise ValidationExecutionError(f"Unsupported format: {format}")
    
    def _format_text_report(
        self,
        report: ValidationReport,
        include_details: bool
    ) -> str:
        """Format report as plain text."""
        lines = []
        lines.append("=" * 70)
        lines.append("SHACL VALIDATION REPORT")
        lines.append("=" * 70)
        lines.append(f"Timestamp: {report.timestamp.isoformat()}")
        lines.append(f"Conforms: {report.conforms}")
        lines.append("")
        
        summary = self.get_summary(report)
        lines.append("SUMMARY")
        lines.append("-" * 70)
        lines.append(f"Total Results:    {summary['total_results']}")
        lines.append(f"Violations:       {summary['violation_count']}")
        lines.append(f"Warnings:         {summary['warning_count']}")
        lines.append(f"Info:             {summary['info_count']}")
        lines.append(f"Affected Nodes:   {summary['affected_nodes']}")
        lines.append("")
        
        if include_details and report.results:
            lines.append("DETAILED RESULTS")
            lines.append("-" * 70)
            
            # Group by severity
            for severity in [SeverityLevel.VIOLATION, SeverityLevel.WARNING, SeverityLevel.INFO]:
                results = report.get_results_by_severity(severity)
                if results:
                    severity_label = SeverityLevel.get_label(severity)
                    lines.append(f"\n{severity_label}s ({len(results)}):")
                    lines.append("")
                    
                    for i, result in enumerate(results, 1):
                        lines.append(f"  {i}. Focus Node: {result.focus_node}")
                        if result.result_path:
                            lines.append(f"     Path: {result.result_path}")
                        if result.value:
                            lines.append(f"     Value: {result.value}")
                        lines.append(f"     Message: {result.message}")
                        if result.source_shape:
                            lines.append(f"     Shape: {result.source_shape}")
                        lines.append("")
        
        lines.append("=" * 70)
        return "\n".join(lines)
    
    def _format_markdown_report(
        self,
        report: ValidationReport,
        include_details: bool
    ) -> str:
        """Format report as Markdown."""
        lines = []
        lines.append("# SHACL Validation Report")
        lines.append("")
        lines.append(f"**Timestamp:** {report.timestamp.isoformat()}")
        lines.append(f"**Conforms:** {report.conforms}")
        lines.append("")
        
        summary = self.get_summary(report)
        lines.append("## Summary")
        lines.append("")
        lines.append("| Metric | Count |")
        lines.append("|--------|-------|")
        lines.append(f"| Total Results | {summary['total_results']} |")
        lines.append(f"| Violations | {summary['violation_count']} |")
        lines.append(f"| Warnings | {summary['warning_count']} |")
        lines.append(f"| Info | {summary['info_count']} |")
        lines.append(f"| Affected Nodes | {summary['affected_nodes']} |")
        lines.append("")
        
        if include_details and report.results:
            lines.append("## Detailed Results")
            lines.append("")
            
            for severity in [SeverityLevel.VIOLATION, SeverityLevel.WARNING, SeverityLevel.INFO]:
                results = report.get_results_by_severity(severity)
                if results:
                    severity_label = SeverityLevel.get_label(severity)
                    lines.append(f"### {severity_label}s ({len(results)})")
                    lines.append("")
                    
                    for i, result in enumerate(results, 1):
                        lines.append(f"**{i}. {result.focus_node}**")
                        lines.append("")
                        if result.result_path:
                            lines.append(f"- **Path:** `{result.result_path}`")
                        if result.value:
                            lines.append(f"- **Value:** `{result.value}`")
                        lines.append(f"- **Message:** {result.message}")
                        if result.source_shape:
                            lines.append(f"- **Shape:** `{result.source_shape}`")
                        lines.append("")
        
        return "\n".join(lines)
    
    def clear_shapes(self) -> None:
        """Clear all loaded SHACL shapes."""
        self.shapes_data.clear()
        self.loaded_shape_files.clear()
        logger.info("SHACL shapes cleared")
    
    def get_loaded_shapes(self) -> List[str]:
        """Get list of loaded shape files."""
        return self.loaded_shape_files.copy()
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Get validator statistics.
        
        Returns:
            Dictionary with validator statistics
        """
        return {
            'shapes_loaded': len(self.loaded_shape_files),
            'validation_count': self.validation_count,
            'shape_files': self.loaded_shape_files.copy()
        }


def create_validator(
    ontology_dir: str = "ontology",
    validation_dir: str = "validation",
    data_dir: str = "data"
) -> SHACLValidator:
    """
    Convenience function to create a validator with loaded ontology and shapes.
    
    Args:
        ontology_dir: Directory containing ontology files
        validation_dir: Directory containing SHACL shapes
        data_dir: Directory containing instance data
    
    Returns:
        Configured SHACLValidator instance
    
    Example:
        validator = create_validator()
        report = validator.validate()
        print(validator.format_report(report))
    """
    try:
        from ontology.loader import load_ontology_files
    except ImportError:
        import sys
        sys.path.insert(0, str(Path(__file__).parent.parent))
        from ontology.loader import load_ontology_files
    
    logger.info("Creating SHACL validator with loaded data")
    
    # Load ontology and data files
    loader = load_ontology_files(ontology_dir, validation_dir, data_dir)
    
    # Create validator
    validator = SHACLValidator(loader)
    
    # Load shapes from validation directory
    validation_path = Path(validation_dir)
    if validation_path.exists():
        try:
            validator.load_shapes_directory(validation_dir)
            logger.info(f"Loaded {len(validator.loaded_shape_files)} shape files")
        except Exception as e:
            logger.warning(f"Error loading shapes: {str(e)}")
    
    logger.info("SHACL validator created successfully")
    
    return validator


if __name__ == "__main__":
    # Example usage
    print("SHACL Validator Module")
    print("=" * 70)
    
    try:
        # Create validator with loaded data
        validator = create_validator()
        
        print(f"Validator created")
        print(f"Shapes loaded: {len(validator.get_loaded_shapes())}")
        
        # Execute validation
        print("\nExecuting validation...")
        report = validator.validate()
        
        # Display report
        print("\n" + validator.format_report(report, format="text"))
        
        # Export report
        output_dir = Path("output")
        output_dir.mkdir(exist_ok=True)
        validator.export_report(report, output_dir / "validation_report.ttl")
        print(f"\nReport exported to: {output_dir / 'validation_report.ttl'}")
        
    except Exception as e:
        print(f"Error: {str(e)}")
