#!/bin/bash
set -e

# If GCP credentials are available, use them
if [ -n "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
  echo "Using provided GCP credentials"
  
  # Pull model artifacts using DVC
  echo "Pulling model artifacts from DVC remote..."
  dvc pull -v
else
  echo "Warning: No GCP credentials provided. Using the app with local artifacts if available."
fi

# Start the Flask application
python application.py
