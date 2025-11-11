#!/bin/bash
set -e

echo "=========================================="
echo "Initializing Fuseki with Ontology Data"
echo "=========================================="

# Create database directory
DB_DIR="/fuseki/databases/ontology"
mkdir -p "$DB_DIR"

# Load ontology files into TDB2 database using tdbloader2
echo "Loading ontology files into TDB2 database..."
if [ -f /ontology/core.ttl ]; then
    echo "Loading core.ttl..."
    /jena-fuseki/tdbloader2 --loc "$DB_DIR" /ontology/core.ttl
fi

if [ -f /ontology/extensions.ttl ]; then
    echo "Loading extensions.ttl..."
    /jena-fuseki/tdbloader2 --loc "$DB_DIR" /ontology/extensions.ttl
fi

# Load any data files if they exist
if [ -d /data ] && [ "$(ls -A /data/*.ttl 2>/dev/null)" ]; then
    echo "Loading data files..."
    for file in /data/*.ttl; do
        if [ -f "$file" ]; then
            echo "Loading $file..."
            /jena-fuseki/tdbloader2 --loc "$DB_DIR" "$file"
        fi
    done
fi

echo "=========================================="
echo "Data loading complete!"
echo "Starting Fuseki server..."
echo "=========================================="

# Start Fuseki server with the loaded database
exec /jena-fuseki/fuseki-server --loc "$DB_DIR" --update /ontology
