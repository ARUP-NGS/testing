#!/bin/bash
# filepath: /Users/mark.monroe/Documents/vscode/testing/test_scripts/test_rc_release.sh

VERSION="1.0.0"
RC_VERSION="${VERSION}-rc1"

# Create a test file
echo "Test commit for release workflow" > release_test.txt
git add release_test.txt
git commit -m "Test commit for release ${VERSION}"

# Store the commit SHA for verification
COMMIT_SHA=$(git rev-parse HEAD)
echo "Commit SHA: $COMMIT_SHA"

# Create RC tag first
git tag $RC_VERSION
git push origin $RC_VERSION

# Create release tag on same commit
git tag $VERSION
git push origin $VERSION

# Create GitHub releases
gh release create $RC_VERSION --title "RC ${RC_VERSION}" --notes "Release candidate" --prerelease

# Wait for workflow to start and verify it's triggered by our commit
# This is the RC release test (expecting skipped)
./test_scripts/wait_on_action.sh \
  --commit "$COMMIT_SHA" \
  --workflow "Official Release Deployment" \
  --expected "skipped" \
  --message "RC release workflow skipped successfully" \
  --verbose

gh release create $VERSION --title "Version ${VERSION}" --notes "Based on ${RC_VERSION}"

# The wait_on_action.sh script selects the most recent workflow run. 
# If we don't wait a bit, it might pick up the RC workflow instead of the release workflow.
sleep 5
echo "Created release ${VERSION} with ${RC_VERSION} - waiting for workflow to run..."
# Wait for workflow to start and verify it's triggered by our commit
# This is the final release test (expecting success)
COMMIT_SHA=$(git rev-parse HEAD)
./test_scripts/wait_on_action.sh \
  --commit "$COMMIT_SHA" \
  --workflow "Official Release Deployment" \
  --expected "success" \
  --message "RC release workflow completed successfully" \
  --verbose

