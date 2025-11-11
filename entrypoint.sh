#!/bin/bash
# Entrypoint script for ontology API container
# This script runs startup initialization before starting the API server

set -e

echo "=========================================="
echo "Starting Ontology API Container"
echo "=========================================="

# Run startup initialization
echo "Running startup initialization..."
python -m ontology.startup

# Check if initialization was successful
if [ $? -eq 0 ]; then
    echo "Startup initialization completed"
else
    echo "Warning: Startup initialization encountered issues"
fi

echo "=========================================="
echo "Starting API Server"
echo "=========================================="

# Start the API server
exec python -m ontology.api
