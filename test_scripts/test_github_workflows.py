import subprocess
import re
import os
import pytest
import logging
from wait_on_action import wait_on_action
from github import Github


def get_github_info():
    """
    Get GitHub authentication token and repository path.
    
    Returns:
        tuple: (github_token, repo_path) - GitHub token and repository path in format 'owner/name'
    """
    github_token = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True).stdout.strip()
    repo_path = subprocess.run(
        ["gh", "repo", "view", "--json", "owner,name", "--jq", ".owner.login + \"/\" + .name"],
        capture_output=True, 
        text=True
    ).stdout.strip()
    
    return github_token, repo_path


def run_bash_script(script_name):
    """
    Run a bash script from the test_scripts directory and validate its execution.
    
    Args:
        script_name (str): Name of the script file to execute
        
    Returns:
        str: Standard output from the script
        
    Raises:
        AssertionError: If the script execution fails
    """
    TEST_SCRIPT_DIR = "test_scripts"

    script_path = os.path.join(TEST_SCRIPT_DIR, script_name)
    result = subprocess.run([script_path], capture_output=True, text=True)
    
    # Ensure the script executed successfully
    assert result.returncode == 0, f"Script failed with error: {result.stderr}"
    
    return result.stdout


def extract_run_info(script_output):
    """
    Extract commit SHA and test run ID from script output.
    
    Args:
        script_output (str): Output from the bash script containing COMMIT_SHA and TEST_RUN_ID
        
    Returns:
        tuple: (commit_sha, test_id) - The extracted commit hash and test identifier
        
    Raises:
        AssertionError: If either commit SHA or test ID cannot be extracted
    """
    commit_match = re.search(r"COMMIT_SHA=([a-f0-9]+)", script_output)
    test_id_match = re.search(r"TEST_RUN_ID=([a-f0-9\-]+)", script_output)
    
    commit_sha = commit_match.group(1)
    assert commit_match, "Could not extract commit SHA"

    if test_id_match:
        test_id = test_id_match.group(1)
    else:
        test_id = None
        logging.warning("TEST_RUN_ID not found in script output, proceeding without it")

    return commit_sha, test_id


def test_hello_world():
    assert 1 + 1 == 2


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
    github_token, repo_path = get_github_info()

    # Run the bash script that handles git/GitHub CLI operations
    script_output = run_bash_script("test_direct_release.sh")
    
    # Extract commit SHA and test ID
    commit_sha, test_id = extract_run_info(script_output)
    
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
    assert exit_code == 0, f"Workflow validation failed: {error_message}"


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
    github_token, repo_path = get_github_info()

    # Run the bash script for RC release
    script_output = run_bash_script("test_rc_release.sh")
    
    # Log the entire output for debugging
    logging.info(f"Script output: {script_output}")
    
    # Extract commit SHA and test ID
    commit_sha, test_id = extract_run_info(script_output)
    
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

    # Run the bash script for final release
    script_output = run_bash_script("test_final_release.sh")
    
    # Extract commit SHA and test ID
    commit_sha, test_id = extract_run_info(script_output)

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