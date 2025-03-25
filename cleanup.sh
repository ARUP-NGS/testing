#!/bin/bash
# filepath: /Users/mark.monroe/Documents/vscode/testing/test_scripts/cleanup.sh

# Delete local test files
rm -f release_test.txt direct_release.txt

# Delete local tags
git tag -d 1.0.0 1.0.0-rc1 2.0.0 2>/dev/null || true

# Delete remote tags
git push origin :1.0.0 :1.0.0-rc1 :2.0.0 2>/dev/null || true

# Delete GitHub releases
gh release delete 1.0.0 --yes 2>/dev/null || true
gh release delete 1.0.0-rc1 --yes 2>/dev/null || true
gh release delete 2.0.0 --yes 2>/dev/null || true

echo "Cleaned up test tags and releases"