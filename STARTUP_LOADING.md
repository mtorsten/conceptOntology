# Automatic Ontology Loading on Startup

This document describes the automatic ontology loading feature that initializes the RDF store when the Docker container starts.

## Overview

The ontology API container automatically loads core ontology files during startup, ensuring that all required RDF data is available before the API server begins accepting requests.

## Files Loaded

The following files are loaded automatically in order:

1. **ontology/core.ttl** - Core ontology definitions (classes, properties, base vocabulary)
2. **ontology/extensions.ttl** - Domain-specific extensions to the core ontology
3. **validation/shapes.ttl** - SHACL validation shapes for data quality enforcement

## Implementation

### Components

#### 1. Startup Script (`src/ontology/startup.py`)

The startup script is responsible for:
- Loading the three core ontology files
- Validating Turtle syntax before loading
- Extracting and registering namespace prefixes
- Logging detailed status information
- Handling errors gracefully without failing the container

**Key Features:**
- Automatic path resolution (works in Docker and local environments)
- Detailed logging with success/failure indicators
- Namespace registration summary
- Graceful error handling (logs errors but doesn't fail container startup)

#### 2. Entrypoint Script (`entrypoint.sh`)

The entrypoint script orchestrates the startup sequence:
1. Runs the startup initialization script
2. Logs the initialization status
3. Starts the API server

**Execution Flow:**
```bash
#!/bin/bash
echo "Starting Ontology API Container"
python -m ontology.startup  # Load ontology files
exec python -m ontology.api  # Start API server
```

#### 3. Dockerfile Configuration

The Dockerfile is configured to:
- Copy the entrypoint script to `/app/entrypoint.sh`
- Make the script executable with `chmod +x`
- Set the entrypoint to run the script

```dockerfile
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh
ENTRYPOINT ["/app/entrypoint.sh"]
```

## Startup Logs

When the container starts, you'll see detailed logs like this:

```
==========================================
Starting Ontology API Container
==========================================
Running startup initialization...
======================================================================
ONTOLOGY STARTUP INITIALIZATION
======================================================================
Base directory: /app
Loading: /app/ontology/core.ttl
✓ Successfully loaded: /app/ontology/core.ttl
Loading: /app/ontology/extensions.ttl
✓ Successfully loaded: /app/ontology/extensions.ttl
Loading: /app/validation/shapes.ttl
✓ Successfully loaded: /app/validation/shapes.ttl
----------------------------------------------------------------------
STARTUP LOADING SUMMARY:
  Total files attempted: 3
  Successfully loaded: 3
  Failed to load: 0
  Loaded files:
    - /app/ontology/core.ttl
    - /app/ontology/extensions.ttl
    - /app/validation/shapes.ttl
  Registered namespaces: 7
    : http://example.org/ontology#
    rdf: http://www.w3.org/1999/02/22-rdf-syntax-ns#
    rdfs: http://www.w3.org/2000/01/rdf-schema#
    owl: http://www.w3.org/2002/07/owl#
    xsd: http://www.w3.org/2001/XMLSchema#
    ext: http://example.org/ontology/extensions#
    sh: http://www.w3.org/ns/shacl#
======================================================================
✓ Startup initialization completed successfully
======================================================================
==========================================
Starting API Server
==========================================
```

## Error Handling

### Missing Files

If a file is not found, the startup script logs a warning and continues:

```
WARNING: File not found: /app/ontology/core.ttl - Skipping
```

### Syntax Errors

If a file contains invalid Turtle syntax, the error is logged:

```
ERROR: ✗ Failed to load /app/ontology/core.ttl: Syntax error at line 42: Unclosed string
```

### Graceful Degradation

The startup script is designed to be resilient:
- Missing files are skipped with warnings
- Syntax errors are logged but don't stop the container
- The API server starts even if some files fail to load
- The health check endpoint reports the actual loading status

## Testing Locally

You can test the startup script locally without Docker:

```bash
# From the project root
python -m ontology.startup

# Or with explicit Python path
PYTHONPATH=src python -m ontology.startup
```

## Docker Usage

### Building the Container

```bash
docker-compose build ontology-api
```

### Starting the Container

```bash
docker-compose up ontology-api
```

### Viewing Startup Logs

```bash
docker-compose logs ontology-api
```

### Checking Health Status

After startup, check the health endpoint to verify loading status:

```bash
curl http://localhost:8000/health
```

Response includes loading statistics:

```json
{
  "success": true,
  "message": "Service is healthy",
  "data": {
    "status": "healthy",
    "components": {
      "rdf_loader": "initialized",
      "query_engine": "initialized",
      "validator": "initialized"
    },
    "statistics": {
      "loaded_files": 3,
      "namespaces": 7,
      "queries_executed": 0,
      "validations_run": 0,
      "shapes_loaded": 0
    }
  }
}
```

## Volume Mounts

The ontology files are mounted as volumes in docker-compose.yml:

```yaml
volumes:
  - ./ontology:/app/ontology
  - ./validation:/app/validation
  - ./data:/app/data
```

This allows you to:
- Edit ontology files on your host machine
- Restart the container to reload changes
- Share ontology files between services

## Customization

### Adding More Files

To load additional files on startup, edit `src/ontology/startup.py`:

```python
files_to_load = [
    base_dir / "ontology" / "core.ttl",
    base_dir / "ontology" / "extensions.ttl",
    base_dir / "ontology" / "custom.ttl",  # Add your file here
    base_dir / "validation" / "shapes.ttl"
]
```

### Changing Load Order

Files are loaded in the order they appear in the `files_to_load` list. Reorder the list to change the loading sequence.

### Disabling Validation

To skip syntax validation during startup (faster but less safe):

```python
loader.load_file(str(file_path), validate=False)
```

## Troubleshooting

### Container Fails to Start

Check the logs:
```bash
docker-compose logs ontology-api
```

Common issues:
- Missing ontology files (check volume mounts)
- Syntax errors in Turtle files (validate with a Turtle parser)
- Permission issues (ensure files are readable)

### Files Not Loading

Verify the files exist in the mounted volumes:
```bash
docker-compose exec ontology-api ls -la /app/ontology
docker-compose exec ontology-api ls -la /app/validation
```

### Syntax Validation Errors

Test your Turtle files locally:
```bash
python -c "from ontology.loader import RDFLoader; loader = RDFLoader(); loader.load_file('ontology/core.ttl')"
```

## Requirements Satisfied

This implementation satisfies the following requirements from the design document:

- **Requirement 4.3**: "WHEN multiple files are loaded, THE RDF Store SHALL merge all triples into a unified graph"
- **Requirement 7.3**: "WHEN the Docker container starts, THE Ontology System SHALL automatically load the ontology files from a mounted volume"

## Related Files

- `src/ontology/startup.py` - Startup initialization script
- `entrypoint.sh` - Container entrypoint script
- `Dockerfile` - Container configuration
- `docker-compose.yml` - Service orchestration
- `src/ontology/loader.py` - RDF loader module
- `src/ontology/api.py` - API server

## Future Enhancements

Potential improvements for the startup loading feature:

1. **Configuration File**: Load file list from a configuration file
2. **Conditional Loading**: Load files based on environment variables
3. **Retry Logic**: Retry failed loads with exponential backoff
4. **Progress Reporting**: Report loading progress to a monitoring service
5. **Parallel Loading**: Load independent files in parallel for faster startup
6. **Validation Reports**: Generate detailed validation reports during startup
7. **Hot Reload**: Watch for file changes and reload automatically
