#!/bin/bash
# filepath: /Users/mark.monroe/Documents/vscode/testing/test_scripts/wait_on_action.sh

# wait_on_action.sh - Monitors GitHub Actions workflow execution and validates the outcome
#
# Usage:
#   wait_on_action.sh [options]
#
# Required Options:
#   --commit <sha>           - Commit SHA to match for workflow runs
#   --workflow <name>        - Name of the workflow to monitor
#   --expected <status>      - Expected conclusion (success|failure|skipped)
#
# Optional Options:
#   --timeout <seconds>      - Maximum wait time in seconds (default: 60)
#   --poll-interval <sec>    - Time between status checks in seconds (default: 5)
#   --message <text>         - Custom message to display on success
#   --error <text>           - Custom message to display on error
#   --verbose                - Show detailed progress information
#
# Exit Codes:
#   0 - Workflow completed with expected conclusion
#   1 - Workflow completed but with unexpected conclusion
#   2 - No workflow found within timeout period
#   3 - Invalid arguments

# Default values
TIMEOUT=60
POLL_INTERVAL=5
VERBOSE=false

# Process command line arguments
while [[ "$#" -gt 0 ]]; do
  case $1 in
    --commit)
      COMMIT_SHA="$2"
      shift 2
      ;;
    --workflow)
      WORKFLOW_NAME="$2"
      shift 2
      ;;
    --expected)
      EXPECTED_CONCLUSION="$2"
      shift 2
      ;;
    --timeout)
      TIMEOUT="$2"
      shift 2
      ;;
    --poll-interval)
      POLL_INTERVAL="$2"
      shift 2
      ;;
    --message)
      SUCCESS_MESSAGE="$2"
      shift 2
      ;;
    --error)
      ERROR_MESSAGE="$2"
      shift 2
      ;;
    --verbose)
      VERBOSE=true
      shift
      ;;
    *)
      echo "Unknown parameter: $1"
      echo "Usage: wait_on_action.sh --commit <sha> --workflow <name> --expected <success|failure|skipped>"
      exit 3
      ;;
  esac
done

# Validate required parameters
if [ -z "$COMMIT_SHA" ] || [ -z "$WORKFLOW_NAME" ] || [ -z "$EXPECTED_CONCLUSION" ]; then
  echo "Error: Missing required parameters"
  echo "Usage: wait_on_action.sh --commit <sha> --workflow <name> --expected <success|failure|skipped>"
  exit 3
fi

# Validate expected conclusion values
if [[ ! "$EXPECTED_CONCLUSION" =~ ^(success|failure|skipped|cancelled|startup_failure|timed_out|action_required)$ ]]; then
  echo "Error: Invalid expected conclusion: $EXPECTED_CONCLUSION"
  echo "Valid values: success, failure, skipped, cancelled, startup_failure, timed_out, action_required"
  exit 3
fi

# Set default messages if not provided
if [ -z "$SUCCESS_MESSAGE" ]; then
  SUCCESS_MESSAGE="Test passed: Workflow completed with expected conclusion: $EXPECTED_CONCLUSION"
fi

if [ -z "$ERROR_MESSAGE" ]; then
  ERROR_MESSAGE="Test failed: Workflow should have concluded with $EXPECTED_CONCLUSION"
fi

# Calculate maximum number of attempts
MAX_ATTEMPTS=$((TIMEOUT / POLL_INTERVAL))

# Log start of monitoring
if $VERBOSE; then
  echo "Starting workflow monitoring:"
  echo "  Commit SHA: $COMMIT_SHA"
  echo "  Workflow: $WORKFLOW_NAME"
  echo "  Expected Conclusion: $EXPECTED_CONCLUSION"
  echo "  Timeout: $TIMEOUT seconds"
  echo "  Poll Interval: $POLL_INTERVAL seconds"
  echo "  Max Attempts: $MAX_ATTEMPTS"
fi

# Multiple actions can be triggered by the same commit, so we need to wait a bit
# We only look at the most recent action
sleep $POLL_INTERVAL

echo "Waiting for workflow to start (up to $TIMEOUT seconds)..."
ATTEMPT=1
WORKFLOW_FOUND=false

# Monitor loop
while [ $ATTEMPT -le $MAX_ATTEMPTS ] && [ $WORKFLOW_FOUND = false ]
do
  if $VERBOSE; then
    echo "Checking for workflow runs (attempt $ATTEMPT/$MAX_ATTEMPTS)..."
  else
    echo -n "."
  fi
  
  # Check if any workflow runs exist for our commit
  WORKFLOW_RUNS=$(gh run list --workflow "$WORKFLOW_NAME" \
    --json headSha,databaseId,status,conclusion,name,createdAt \
    --jq ".[] | select(.headSha == \"$COMMIT_SHA\")")

  if [ -n "$WORKFLOW_RUNS" ]; then
    WORKFLOW_FOUND=true
    echo -e "\n✅ Workflow triggered by commit $COMMIT_SHA!"
    
    # Get the run ID to watch
    #RUN_ID=$(echo "$WORKFLOW_RUNS" | jq -r '.databaseId')

    # Get the most recently created workflow run
    RUN_ID=$(echo "$WORKFLOW_RUNS" | jq -s 'sort_by(.createdAt) | reverse | .[0].databaseId')
    
    if $VERBOSE; then
      echo "Workflow Details:"
#      echo "$WORKFLOW_RUNS" | jq '.'
      echo "$WORKFLOW_RUNS" | jq -r '"\nWorkflow ID: \(.databaseId)\nStatus: \(.status)\nConclusion: \(.conclusion)"'
      echo "Watching Run ID: $RUN_ID"
    else
      echo "Workflow Run ID: $RUN_ID"
    fi
    
    # Watch the run until it completes
    echo -e "\nWatching workflow run until completion:"
    gh run watch $RUN_ID
    
    # Check final status
    FINAL_STATUS=$(gh run view $RUN_ID --json conclusion --jq '.conclusion')
    
    echo "Workflow concluded with status: $FINAL_STATUS"
    echo "Expected status: $EXPECTED_CONCLUSION"
    
    if [[ "$FINAL_STATUS" == "$EXPECTED_CONCLUSION" ]]; then
      echo "✅ $SUCCESS_MESSAGE"
      exit 0
    else
      echo "❌ $ERROR_MESSAGE (got $FINAL_STATUS)"
      exit 1
    fi
  else
    sleep $POLL_INTERVAL
    ATTEMPT=$((ATTEMPT+1))
  fi
done

if [ $WORKFLOW_FOUND = false ]; then
  echo -e "\n❌ Error: No workflow was triggered by commit $COMMIT_SHA after $TIMEOUT seconds"
  exit 2
fi