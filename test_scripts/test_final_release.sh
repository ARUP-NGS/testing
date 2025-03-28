#!/bin/bash
# This script creates RC and final release tags for workflow testing
# Generate a unique ID
RUN_ID=$(date +%s)-$(openssl rand -hex 4)
echo "TEST_RUN_ID=$RUN_ID"  # Echo for the Python script to capture

VERSION="1.0.0"
RC_VERSION="${VERSION}-rc1"

# Store the commit SHA for verification
COMMIT_SHA=$(git rev-parse HEAD)
echo "COMMIT_SHA=$COMMIT_SHA"

gh release create $VERSION --title "Version ${VERSION} (Test:${RUN_ID})" --notes "Based on ${RC_VERSION}\nTest-ID: ${RUN_ID}"

echo "Created final release ${VERSION} with Test-ID: ${RUN_ID}"