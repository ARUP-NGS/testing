import subprocess
import re
import os
import pytest
import logging
from wait_on_action import wait_on_action
from github import Github


# def get_latest_workflow_run(github_token, repo_path, workflow_name):
#     """Get the latest run number for a specific workflow"""
#     g = Github(github_token)
#     repo = g.get_repo(repo_path)
#     workflow = repo.get_workflow(workflow_name)
    
#     # Get the most recent run
#     runs = workflow.get_runs().reversed
#     try:
#         latest_run = runs[0]
#         return {
#             "number": latest_run.run_number,
#             "id": latest_run.id,
#             "conclusion": latest_run.conclusion,
#             "status": latest_run.status,
#             "created_at": latest_run.created_at
#         }
#     except StopIteration:
#         return None

def test_hello_world():
    assert 1 + 1 == 2

def test_rc_release():
    """Test the RC release process (with RC tag, should succeed)"""
    # Run the bash script
    script_path = os.path.join("test_scripts", "test_rc_release.sh")
    
    # Execute the script and capture output
    result = subprocess.run(
        [script_path],
        capture_output=True,
        text=True,
        check=False
    )
    
    # Check exit code
    assert result.returncode == 0, f"Script failed with error: {result.stderr}"
    
    print(result.stdout)



def test_direct_release():
    """
    Test direct release without RC tag.
    
    This test verifies that:
    1. A direct release without RC tag is properly created
    2. The GitHub Actions workflow properly fails verification
    """
    # Set up logging
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    
    # Test setup
    workflow_name = "onrelease.yml"
    
    # Get GitHub token and repo information
    github_token = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()
    repo_path = subprocess.run(
        ["gh", "repo", "view", "--json", "owner,name", "--jq", ".owner.login + \"/\" + .name"],
        capture_output=True, 
        text=True
    ).stdout.strip()

    # Run the bash script that handles git/GitHub CLI operations
    script_path = os.path.join("test_scripts", "test_direct_release.sh")
    result = subprocess.run([script_path], capture_output=True, text=True)
    
    # Ensure the script executed successfully
    assert result.returncode == 0, f"Script failed with error: {result.stderr}"
    
    # Extract commit SHA and test ID
    commit_match = re.search(r"COMMIT_SHA=([a-f0-9]+)", result.stdout)
    test_id_match = re.search(r"TEST_RUN_ID=([a-f0-9\-]+)", result.stdout)
    
    assert commit_match, "Could not extract commit SHA"
    assert test_id_match, "Could not extract test ID"
    
    commit_sha = commit_match.group(1)
    test_id = test_id_match.group(1)

    
    # Call wait_on_action directly as a Python function
    exit_code = wait_on_action(
        github_token=github_token,
        repo_path=repo_path,
        commit_sha=commit_sha,
        workflow_name=workflow_name,
        test_id=test_id,
        expected_conclusion="failure",
        timeout=120,  # Allow more time for workflow to complete
        poll_interval=5,
        success_message="Direct release correctly failed verification",
        error_message="Direct release should have failed verification",
        verbose=True
    )
    
    # Assert that the wait_on_action call was successful
    assert exit_code == 0, "Workflow validation failed"

def test_rc_release_workflow():
    """
    Test RC and final release workflow verification
    
    This test verifies:
    1. RC release should be skipped by the workflow
    2. Final release should successfully run the workflow
    """
    # Set up logging
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    
    # Test setup
    workflow_name = "onrelease.yml"
    
    # Get GitHub token and repo information
    github_token = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()
    repo_path = subprocess.run(
        ["gh", "repo", "view", "--json", "owner,name", "--jq", ".owner.login + \"/\" + .name"],
        capture_output=True, 
        text=True
    ).stdout.strip()

    # Run the bash script that handles git/GitHub CLI operations
    script_path = os.path.join("test_scripts", "test_rc_release.sh")
    result = subprocess.run([script_path], capture_output=True, text=True)
    
    # Ensure the script executed successfully
    assert result.returncode == 0, f"Script failed with error: {result.stderr}"
    
    # Log the entire output for debugging
    logging.info(f"Script output: {result.stdout}")
    
    # Extract commit SHA and test ID
    commit_match = re.search(r"COMMIT_SHA=([a-f0-9]+)", result.stdout)
    test_id_match = re.search(r"TEST_RUN_ID=([a-f0-9\-]+)", result.stdout)
    
    assert commit_match, "Could not extract commit SHA"
    assert test_id_match, "Could not extract test ID"
    
    commit_sha = commit_match.group(1)
    test_id = test_id_match.group(1)
    
    # First verification: RC release should be SKIPPED
    logging.info("Verifying RC release workflow (should be skipped)...")
    rc_exit_code = wait_on_action(
        github_token=github_token,
        repo_path=repo_path,
        commit_sha=commit_sha,
        workflow_name=workflow_name,
        test_id=test_id,
        expected_conclusion="skipped",
        timeout=60,
        poll_interval=5,
        success_message="RC release workflow skipped successfully",
        error_message="RC release workflow should have been skipped",
        verbose=True
    )
    
    # Assert that the first verification passed
    assert rc_exit_code == 0, "RC release workflow verification failed"

    # Run the bash script that handles git/GitHub CLI operations
    script_path = os.path.join("test_scripts", "test_final_release.sh")
    result = subprocess.run([script_path], capture_output=True, text=True)

    # Ensure the script executed successfully
    assert result.returncode == 0, f"Script failed with error: {result.stderr}"
    
    # Extract commit SHA and test ID
    commit_match = re.search(r"COMMIT_SHA=([a-f0-9]+)", result.stdout)
    test_id_match = re.search(r"TEST_RUN_ID=([a-f0-9\-]+)", result.stdout)
    
    assert commit_match, "Could not extract commit SHA"
    assert test_id_match, "Could not extract test ID"
    
    commit_sha = commit_match.group(1)
    test_id = test_id_match.group(1)

    # Second verification: Final release should SUCCEED
    logging.info("Verifying final release workflow (should succeed)...")
    final_exit_code = wait_on_action(
        github_token=github_token,
        repo_path=repo_path,
        commit_sha=commit_sha,
        workflow_name=workflow_name,
        test_id=test_id,
        expected_conclusion="success",
        timeout=120,  # Allow more time for workflow to complete
        poll_interval=5,
        success_message="Final release workflow completed successfully",
        error_message="Final release workflow should have succeeded",
        verbose=True
    )
    
    # Assert that the second verification passed
    assert final_exit_code == 0, "Final release workflow verification failed"