#!/bin/bash
# This script creates a direct release without an RC tag
# The GitHub workflow should fail for this type of release
# Generate a unique ID
RUN_ID=$(date +%s)-$(openssl rand -hex 4)
echo "TEST_RUN_ID=$RUN_ID"  # Echo for the Python script to capture

VERSION="2.0.0"

# Create a test file
echo "Test direct release" > direct_release.txt
git add direct_release.txt
git commit -m "Direct release ${VERSION}"

# Store the commit SHA for verification
COMMIT_SHA=$(git rev-parse HEAD)
echo "COMMIT_SHA=$COMMIT_SHA"

# Only create release tag (no RC)
git tag $VERSION
git push origin $VERSION

# Create GitHub release
gh release create $VERSION --title "Version ${VERSION} (Test:${RUN_ID})" --notes "Direct release (no RC) Test-ID: ${RUN_ID}"

echo "Created direct release ${VERSION} - workflow should fail verification"
# The Python test will use the commit SHA to validate the workflow outcome