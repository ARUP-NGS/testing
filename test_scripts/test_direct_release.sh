#!/bin/bash
# filepath: /Users/mark.monroe/Documents/vscode/testing/test_scripts/test_direct_release.sh

VERSION="2.0.0"

# Create a test file
echo "Test direct release" > direct_release.txt
git add direct_release.txt
git commit -m "Direct release ${VERSION}"

# Store the commit SHA for verification
COMMIT_SHA=$(git rev-parse HEAD)
echo "Commit SHA: $COMMIT_SHA"

# Only create release tag (no RC)
git tag $VERSION
git push origin $VERSION

# Create GitHub release
gh release create $VERSION --title "Version ${VERSION}" --notes "Direct release (no RC)"

echo "Created direct release ${VERSION} - workflow should fail verification"

# For direct release test (expecting failure)
COMMIT_SHA=$(git rev-parse HEAD)
./test_scripts/wait_on_action.sh \
  --commit "$COMMIT_SHA" \
  --workflow "Official Release Deployment" \
  --expected "failure" \
  --message "Direct release correctly failed verification"