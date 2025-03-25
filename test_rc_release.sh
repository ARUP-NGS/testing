#!/bin/bash
# filepath: /Users/mark.monroe/Documents/vscode/testing/test_scripts/test_rc_release.sh

VERSION="1.0.0"
RC_VERSION="${VERSION}-rc1"

# Create a test file
echo "Test commit for release workflow" > release_test.txt
git add release_test.txt
git commit -m "Test commit for release ${VERSION}"

# Create RC tag first
git tag $RC_VERSION
git push origin $RC_VERSION

# Create release tag on same commit
git tag $VERSION
git push origin $VERSION

# Create GitHub releases
gh release create $RC_VERSION --title "RC ${RC_VERSION}" --notes "Release candidate" --prerelease
gh release create $VERSION --title "Version ${VERSION}" --notes "Based on ${RC_VERSION}"

echo "Created release ${VERSION} with ${RC_VERSION} - check GitHub Actions"