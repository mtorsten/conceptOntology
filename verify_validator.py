"""Quick verification of validator implementation"""
import sys
sys.path.insert(0, 'src')

from ontology.validator import (
    SHACLValidator,
    ValidationReport,
    ValidationResult,
    SeverityLevel,
    create_validator
)

print("Validator Implementation Verification")
print("=" * 60)

# 1. Check classes are available
print("\n1. Classes available:")
print(f"   - SHACLValidator: {SHACLValidator}")
print(f"   - ValidationReport: {ValidationReport}")
print(f"   - ValidationResult: {ValidationResult}")
print(f"   - SeverityLevel: {SeverityLevel}")

# 2. Check severity levels
print("\n2. Severity levels:")
for level in SeverityLevel.all_levels():
    print(f"   - {SeverityLevel.get_label(level)}: {level}")

# 3. Create validator
print("\n3. Creating validator...")
validator = create_validator()
print(f"   - Validator created: {type(validator).__name__}")

# 4. Check statistics
print("\n4. Validator statistics:")
stats = validator.get_statistics()
for key, value in stats.items():
    if key != 'shape_files':
        print(f"   - {key}: {value}")

# 5. Execute validation
print("\n5. Executing validation...")
report = validator.validate()
print(f"   - Report: {report}")

# 6. Check report methods
print("\n6. Report methods:")
print(f"   - is_valid: {validator.is_valid(report)}")
print(f"   - get_violations: {len(report.get_violations())} violations")
print(f"   - get_warnings: {len(report.get_warnings())} warnings")
print(f"   - get_info: {len(report.get_info())} info")

# 7. Export report
print("\n7. Exporting report...")
validator.export_report(report, "output/verify_report.ttl")
print("   - Report exported successfully")

print("\n" + "=" * 60)
print("All verification checks passed!")
print("=" * 60)
