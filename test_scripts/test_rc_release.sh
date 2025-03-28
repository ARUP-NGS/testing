#!/bin/bash
# This script creates RC and final release tags for workflow testing
# Generate a unique ID
RUN_ID=$(date +%s)-$(openssl rand -hex 4)
echo "TEST_RUN_ID=$RUN_ID"  # Echo for the Python script to capture

VERSION="1.0.0"
RC_VERSION="${VERSION}-rc1"

# Create a test file
echo "Test commit for release workflow" > release_test.txt
git add release_test.txt
git commit -m "Test commit for release ${VERSION}"

# Store the commit SHA for verification
COMMIT_SHA=$(git rev-parse HEAD)
echo "COMMIT_SHA=$COMMIT_SHA"

# Create RC tag first
git tag $RC_VERSION
git push origin $RC_VERSION

# Create release tag on same commit
git tag $VERSION
git push origin $VERSION

# Create GitHub releases
# Create GitHub releases with the unique ID
gh release create $RC_VERSION --title "RC ${RC_VERSION} (Test:${RUN_ID})" --notes "Release candidate Test-ID: ${RUN_ID}" --prerelease

echo "Created RC release ${RC_VERSION} - now creating final release..."
