#!/bin/bash
# filepath: /Users/mark.monroe/Documents/vscode/testing/test_scripts/test_direct_release.sh

VERSION="2.0.0"

# Create a test file
echo "Test direct release" > direct_release.txt
git add direct_release.txt
git commit -m "Direct release ${VERSION}"

# Only create release tag (no RC)
git tag $VERSION
git push origin $VERSION

# Create GitHub release
gh release create $VERSION --title "Version ${VERSION}" --notes "Direct release (no RC)"

echo "Created direct release ${VERSION} - workflow should fail verification"