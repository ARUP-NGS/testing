#!/usr/bin/env python3
# filepath: /Users/mark.monroe/Documents/vscode/testing/test_scripts/wait_on_action.py

"""
GitHub Actions Workflow Monitor

This script monitors GitHub Actions workflow execution and validates the outcome.
It can be used both as a command-line tool or imported into other Python scripts.
"""

import argparse
import sys
import time
from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import logging
from github import Github, GithubException, Auth
from github.WorkflowRun import WorkflowRun


def setup_logging(verbose: bool = False) -> None:
    """Configure logging based on verbosity level."""
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(message)s"
    )

def get_matching_workflow_runs(
    github_token: str,
    repo_path: str,
    workflow_name: str,
    commit_sha: str,
    test_id: Optional[str] = None
) -> List[WorkflowRun]:
    """
    Get all workflow runs matching the specified criteria.
    
    Args:
        github_token: GitHub authentication token
        repo_path: Repository path in format "owner/repo"
        workflow_name: Name or filename of the workflow
        commit_sha: Commit SHA to filter by
        test_id: Optional Test ID to search for in the display_title
        
    Returns:
        List of matching workflow runs sorted by creation time (newest first)
    """
    logging.debug(f"Looking for workflow runs in {repo_path} for commit {commit_sha}")
    if test_id:
        logging.debug(f"Also filtering by Test ID: {test_id}")
    
    try:
        # Initialize GitHub client
        g = Github(auth=Auth.Token(github_token))
        repo = g.get_repo(repo_path)
        
        # Find workflow by name or filename
        workflows = list(repo.get_workflows())
        target_workflow = None
        
        for workflow in workflows:
            if workflow.name == workflow_name or workflow.path.endswith(f"/{workflow_name}"):
                target_workflow = workflow
                break
        
        if not target_workflow:
            logging.error(f"Workflow '{workflow_name}' not found")
            return []
            
        # Get runs for this workflow
        all_runs = list(target_workflow.get_runs())
        
        # Filter by commit SHA and optionally by test_id
        if test_id:
            matching_runs = []
            for run in all_runs:
                if run.head_sha == commit_sha:
                    # Check if test_id is in the display_title
                    display_title = getattr(run, "display_title", "") or ""
                    run_name = getattr(run, "name", "") or ""
                    
                    if test_id in display_title or test_id in run_name:
                        matching_runs.append(run)
        else:
            # Just filter by commit SHA if no test_id
            matching_runs = [run for run in all_runs if run.head_sha == commit_sha]
        
        # Sort by created_at (newest first)
        matching_runs.sort(key=lambda run: run.created_at, reverse=True)
        
        if test_id and not matching_runs:
            logging.debug(f"No runs found with Test ID: {test_id}")
                
        return matching_runs
    
    except GithubException as e:
        logging.error(f"GitHub API error: {e}")
        return []
    except Exception as e:
        logging.error(f"Error getting workflow runs: {e}")
        return []


def watch_workflow_run(
    github_token: str,
    repo_path: str,
    run_id: int,
    poll_interval: int = 5
) -> str:
    """
    Watch a workflow run until it completes and return its conclusion.
    
    Args:
        github_token: GitHub authentication token
        repo_path: Repository path in format "owner/repo"
        run_id: ID of the workflow run to watch
        poll_interval: Time in seconds between status checks
        
    Returns:
        The conclusion of the workflow (success, failure, skipped, etc.)
    """
    g = Github(auth=Auth.Token(github_token))
    repo = g.get_repo(repo_path)
    
    while True:
        run = repo.get_workflow_run(run_id)
        status = run.status
        conclusion = run.conclusion
        
        logging.info(f"Run #{run_id} - Status: {status}")
        
        if status == "completed":
            return conclusion or "unknown"
            
        time.sleep(poll_interval)


def validate_conclusion(
    actual_conclusion: str,
    expected_conclusion: str,
    success_message: str = None,
    error_message: str = None
) -> int:
    """
    Validate if the actual conclusion matches the expected one.
    
    Args:
        actual_conclusion: The actual conclusion of the workflow run
        expected_conclusion: The expected conclusion to check against
        success_message: Custom message to display on success
        error_message: Custom message to display on error
        
    Returns:
        Exit code (0 for success, 1 for failure)
    """
    if not success_message:
        success_message = f"Test passed: Workflow completed with expected conclusion: {expected_conclusion}"
        
    if not error_message:
        error_message = f"Test failed: Workflow should have concluded with {expected_conclusion}"
    
    if actual_conclusion == expected_conclusion:
        logging.info(f"✅ {success_message}")
        return 0
    else:
        logging.error(f"❌ {error_message} (got {actual_conclusion})")
        return 1


def wait_on_action(
    github_token: str,
    repo_path: str,
    commit_sha: str,
    workflow_name: str,
    expected_conclusion: str,
    test_id: Optional[str] = None,
    timeout: int = 60,
    poll_interval: int = 5,
    success_message: str = None,
    error_message: str = None,
    verbose: bool = False
) -> int:
    """
    Main function to wait for and validate a workflow run.
    
    Args:
        github_token: GitHub authentication token
        repo_path: Repository path in format "owner/repo"
        commit_sha: Commit SHA to monitor
        workflow_name: Name or filename of the workflow
        expected_conclusion: Expected conclusion (success, failure, skipped, etc.)
        test_id: Optional Test ID to search for in the display_title
        timeout: Maximum time to wait in seconds
        poll_interval: Time between checks in seconds
        success_message: Custom message to display on success
        error_message: Custom message to display on error
        verbose: Whether to show detailed progress information
        
    Returns:
        Exit code (0 for success, 1 for failure, 2 for no workflow found)
    """
    setup_logging(verbose)
    
    if verbose:
        logging.debug("Starting workflow monitoring:")
        logging.debug(f"  Repo: {repo_path}")
        logging.debug(f"  Commit SHA: {commit_sha}")
        logging.debug(f"  Workflow: {workflow_name}")
        if test_id:
            logging.debug(f"  Test ID: {test_id}")
        logging.debug(f"  Expected Conclusion: {expected_conclusion}")
        logging.debug(f"  Timeout: {timeout} seconds")
        logging.debug(f"  Poll Interval: {poll_interval} seconds")
    
    # Initial delay before starting checks
    time.sleep(poll_interval)
    
    start_time = time.time()
    end_time = start_time + timeout
    workflow_found = False
    
    logging.info(f"Waiting for workflow to start (up to {timeout} seconds)...")
    
    while time.time() < end_time and not workflow_found:
        runs = get_matching_workflow_runs(
            github_token, repo_path, workflow_name, commit_sha, test_id
        )
        
        if runs:
            workflow_found = True
            run = runs[0]  # Get the most recent run
            run_id = run.id
            
            log_message = f"✅ Workflow triggered by commit {commit_sha}"
            if test_id:
                log_message += f" with Test ID {test_id}"
            logging.info(log_message + "!")
            
            if verbose:
                logging.debug("Workflow Details:")
                logging.debug(f"  ID: {run.id}")
                logging.debug(f"  Name: {run.name}")
                if hasattr(run, "display_title"):
                    logging.debug(f"  Display Title: {run.display_title}")
                logging.debug(f"  Status: {run.status}")
                logging.debug(f"  Created: {run.created_at}")
            
            # Watch the run until it completes
            logging.info("Watching workflow run until completion:")
            final_conclusion = watch_workflow_run(
                github_token, repo_path, run_id, poll_interval
            )
            
            logging.info(f"Workflow concluded with status: {final_conclusion}")
            logging.info(f"Expected status: {expected_conclusion}")
            
            # Validate the conclusion
            return validate_conclusion(
                final_conclusion, 
                expected_conclusion,
                success_message,
                error_message
            )
        
        else:
            if verbose:
                logging.debug(f"Checking for workflow runs... (attempt {int(time.time() - start_time) // poll_interval + 1})")
            else:
                print(".", end="", flush=True)
            
            time.sleep(poll_interval)
    
    # If we get here, no workflow was found
    error_msg = f"❌ Error: No workflow was triggered by commit {commit_sha}"
    if test_id:
        error_msg += f" with Test ID {test_id}"
    error_msg += f" after {timeout} seconds"
    logging.error(error_msg)
    return 2


def main():
    """Parse command-line arguments and run the workflow monitor."""
    parser = argparse.ArgumentParser(
        description="GitHub Actions Workflow Monitor"
    )
    
    # Required arguments
    parser.add_argument("--token", required=True, help="GitHub authentication token")
    parser.add_argument("--repo", required=True, help="Repository in format 'owner/repo'")
    parser.add_argument("--commit", required=True, help="Commit SHA to match for workflow runs")
    parser.add_argument("--workflow", required=True, help="Name of the workflow to monitor")
    parser.add_argument("--expected", required=True, 
                        choices=["success", "failure", "skipped", "cancelled", 
                                 "startup_failure", "timed_out", "action_required", "neutral"],
                        help="Expected conclusion")
    
    # Optional arguments
    parser.add_argument("--test-id", help="Test ID to search for in the workflow display title")
    parser.add_argument("--timeout", type=int, default=60, 
                        help="Maximum wait time in seconds (default: 60)")
    parser.add_argument("--poll-interval", type=int, default=5,
                        help="Time between status checks in seconds (default: 5)")
    parser.add_argument("--message", help="Custom message to display on success")
    parser.add_argument("--error", help="Custom message to display on error")
    parser.add_argument("--verbose", action="store_true", help="Show detailed progress information")
    
    args = parser.parse_args()
    
    exit_code = wait_on_action(
        github_token=args.token,
        repo_path=args.repo,
        commit_sha=args.commit,
        workflow_name=args.workflow,
        expected_conclusion=args.expected,
        test_id=args.test_id,
        timeout=args.timeout,
        poll_interval=args.poll_interval,
        success_message=args.message,
        error_message=args.error,
        verbose=args.verbose
    )
    
    sys.exit(exit_code)