#!/bin/bash

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

# Clean up workflow runs related to our test tags
echo "Cleaning up workflow runs..."

# Option 1: Delete workflow runs by workflow name
#gh run list --workflow "Official Release Deployment" --json databaseId --jq '.[].databaseId' | xargs -I{} gh run delete {} --yes

# Option 2: Delete recent workflow runs (last 5)
gh run list --limit 5 --json databaseId --jq '.[].databaseId' | xargs -I{} gh run delete {}

echo "Cleaned up test tags, releases, and workflow runs"