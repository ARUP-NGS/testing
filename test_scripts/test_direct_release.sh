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

# Wait for workflow to start and verify it's triggered by our commit
echo "Waiting for workflow to start (up to 60 seconds)..."
MAX_ATTEMPTS=12
ATTEMPT=1
WORKFLOW_FOUND=false

while [ $ATTEMPT -le $MAX_ATTEMPTS ] && [ $WORKFLOW_FOUND = false ]
do
  echo "Checking for workflow runs (attempt $ATTEMPT/$MAX_ATTEMPTS)..."
  
  # Check if any "Official Release Deployment" workflow runs exist for our tag
  WORKFLOW_RUNS=$(gh run list --workflow "Official Release Deployment" \
    --json headSha,databaseId,status,conclusion,name \
    --jq ".[] | select(.headSha == \"$COMMIT_SHA\")")
  
  if [ -n "$WORKFLOW_RUNS" ]; then
    WORKFLOW_FOUND=true
    echo "✅ Workflow triggered by our commit!"
    echo "$WORKFLOW_RUNS" | jq -r '"\nWorkflow ID: \(.databaseId)\nStatus: \(.status)\nConclusion: \(.conclusion)"'
    #echo "$WORKFLOW_RUNS" | jq '.'
    
    # Get the run ID to watch
    RUN_ID=$(echo "$WORKFLOW_RUNS" | jq -r '.databaseId')
    
    # Watch the run until it completes
    echo -e "\nWatching workflow run until completion:"
    gh run watch $RUN_ID
    
    # Check final status
    FINAL_STATUS=$(gh run view $RUN_ID --json conclusion --jq '.conclusion')
    if [[ "$FINAL_STATUS" == "failure" ]]; then
      echo "✅ Test passed: Workflow failed as expected (no RC tag)"
    else
      echo "❌ Test failed: Workflow should have failed but didn't"
      exit 1
    fi
    
    break
  else
    echo "No matching workflow run found yet. Waiting..."
    sleep 5
    ATTEMPT=$((ATTEMPT+1))
  fi
done

if [ $WORKFLOW_FOUND = false ]; then
  echo "❌ Error: No workflow was triggered by commit $COMMIT_SHA after 60 seconds"
  exit 1
fi