import os
import json
import sys
import hmac
import hashlib
import base64
import logging
import tempfile
import subprocess
from typing import Dict, Any, Optional, Tuple
import boto3
from dotenv import load_dotenv

# Constants
DEFAULT_REPO_URL = "https://github.com/SFang-cmd/obiKnowledge"
DEFAULT_BRANCH = "main"
DEFAULT_REPO_PATH = "./backend/data/obiKnowledge"

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger("webhook-handler")

# Add parent directory to path for imports to work in both modes (script and Lambda)
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(os.path.dirname(os.path.dirname(current_dir)))
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

# Import the RAG pipeline after adding the parent to path
from backend.app.core.rag_pipeline import RAGPipeline


def verify_github_signature(payload: bytes, signature_header: str, secret: str) -> bool:
    """
    Verify that the webhook request is coming from GitHub by checking the signature.
    
    Args:
        payload: Raw request body bytes
        signature_header: X-Hub-Signature header value
        secret: Webhook secret
        
    Returns:
        bool: True if signature is valid
    """
    if not secret or not signature_header:
        logger.warning("Missing webhook secret or signature header")
        return False
        
    # Get signature from header
    sha_name, signature = signature_header.split('=')
    if sha_name != 'sha1':
        logger.warning(f"Unsupported signature hash algorithm: {sha_name}")
        return False
        
    # Create expected signature
    mac = hmac.new(secret.encode(), msg=payload, digestmod=hashlib.sha1)
    expected_signature = mac.hexdigest()
    
    # Compare signatures securely
    return hmac.compare_digest(signature, expected_signature)


def clone_or_pull_repo(repo_url: str, target_path: str, branch: str = "main") -> bool:
    """
    Clone a repository or pull latest changes if it already exists.
    
    Args:
        repo_url: Repository URL
        target_path: Local path where to clone/pull
        branch: Branch name to checkout
        
    Returns:
        bool: True if successful
    """
    try:
        if os.path.exists(os.path.join(target_path, ".git")):
            logger.info(f"Repository exists, pulling latest changes from {branch}")
            result = subprocess.run(
                ["git", "pull", "origin", branch],
                cwd=target_path,
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"Pull result: {result.stdout.strip()}")
        else:
            logger.info(f"Cloning repository {repo_url} to {target_path}")
            os.makedirs(os.path.dirname(target_path), exist_ok=True)
            result = subprocess.run(
                ["git", "clone", "--branch", branch, repo_url, target_path],
                capture_output=True,
                text=True,
                check=True
            )
            logger.info(f"Clone result: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        logger.error(f"Git operation failed: {e.stderr}")
        return False
    except Exception as e:
        logger.error(f"Repository operation failed: {str(e)}")
        return False


def update_knowledge_base(repo_path: str, openai_api_key: str) -> Dict[str, Any]:
    """
    Process documents from repository and update the knowledge base.
    
    Args:
        repo_path: Path to the cloned repository
        openai_api_key: OpenAI API key
        
    Returns:
        Dict: Statistics about the update
    """
    logger.info("Initializing RAG pipeline")
    try:
        # Initialize the RAG pipeline - will use Chroma Cloud or local based on env vars
        pipeline = RAGPipeline(openai_api_key=openai_api_key)
        
        # Process documents and update the knowledge base
        logger.info(f"Ingesting documents from {repo_path}")
        stats = pipeline.ingest_documents(repo_path)
        
        logger.info(f"Knowledge base updated: {stats}")
        return stats
    except Exception as e:
        logger.error(f"Error updating knowledge base: {str(e)}")
        raise


def process_github_webhook(event: Dict[str, Any], webhook_secret: Optional[str] = None) -> Dict[str, Any]:
    """
    Process a GitHub webhook event.
    
    Args:
        event: GitHub webhook event data
        webhook_secret: Secret for verifying webhook signature
        
    Returns:
        Dict: Response with status
    """
    try:
        # Extract repository information from the event
        repository = event.get("repository", {})
        repo_name = repository.get("name")
        repo_url = repository.get("clone_url")
        
        if "ref" in event:
            branch = event["ref"].split("/")[-1]  # Extract branch name from refs/heads/main
        else:
            branch = "main"  # Default to main branch if not specified
            
        logger.info(f"Processing webhook for {repo_name}/{branch}")
        
        # Get repository path from environment or use default
        repo_path = os.environ.get("REPO_PATH", DEFAULT_REPO_PATH)
        
        # Clone or pull the latest changes
        if not clone_or_pull_repo(repo_url, repo_path, branch):
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "Failed to update repository"})
            }
        
        # Get OpenAI API key
        openai_key = os.environ.get("OPENAI_API_KEY")
        if not openai_key:
            return {
                "statusCode": 500,
                "body": json.dumps({"error": "OpenAI API key not found"})
            }
            
        # Update knowledge base
        stats = update_knowledge_base(repo_path, openai_key)
        
        return {
            "statusCode": 200,
            "body": json.dumps({
                "message": "Knowledge base updated successfully",
                "stats": stats
            })
        }
        
    except Exception as e:
        logger.error(f"Error processing webhook: {str(e)}")
        return {
            "statusCode": 500,
            "body": json.dumps({"error": f"Error processing webhook: {str(e)}"})
        }


def lambda_handler(event, context):
    """
    AWS Lambda handler function.
    
    Args:
        event: AWS Lambda event
        context: AWS Lambda context
        
    Returns:
        Dict: Response with status code and body
    """
    load_dotenv()  # Load environment variables from .env file if available
    
    # Check if this is an API Gateway event
    if "headers" in event and "body" in event:
        # Extract headers and body
        headers = event.get("headers", {})
        
        # Handle GitHub signature verification if configured
        github_secret = os.environ.get("GITHUB_WEBHOOK_SECRET")
        if github_secret:
            signature = headers.get("X-Hub-Signature")
            if not signature:
                return {
                    "statusCode": 403,
                    "body": json.dumps({"error": "Missing X-Hub-Signature header"})
                }
                
            # Get body and verify signature
            body = event["body"]
            is_base64 = event.get("isBase64Encoded", False)
            
            if is_base64:
                body_bytes = base64.b64decode(body)
            else:
                body_bytes = body.encode()
                
            if not verify_github_signature(body_bytes, signature, github_secret):
                return {
                    "statusCode": 403,
                    "body": json.dumps({"error": "Invalid signature"})
                }
        
        # Parse body as JSON
        if isinstance(event["body"], str):
            try:
                webhook_payload = json.loads(event["body"])
            except json.JSONDecodeError:
                return {
                    "statusCode": 400,
                    "body": json.dumps({"error": "Invalid JSON payload"})
                }
        else:
            webhook_payload = event["body"]
            
        # Check if this is a GitHub push event
        github_event = headers.get("X-GitHub-Event")
        if github_event != "push":
            return {
                "statusCode": 200,
                "body": json.dumps({"message": f"Ignoring non-push event: {github_event}"})
            }
            
        # Process the webhook
        return process_github_webhook(webhook_payload, github_secret)
    else:
        # Direct invocation with event data
        return process_github_webhook(event)


def update_from_repo(repo_url: str, branch: str = "main", repo_path: str = None):
    """
    Update knowledge base from a repository - for manual runs.
    
    Args:
        repo_url: URL of the repository
        branch: Branch to use
        repo_path: Path where to clone/pull the repository
        
    Returns:
        Dict: Statistics about the update
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Get repository path from argument or environment or use default
    if not repo_path:
        repo_path = os.environ.get("REPO_PATH", DEFAULT_REPO_PATH)
        
    logger.info(f"Updating knowledge base from {repo_url} ({branch}) to {repo_path}")
    
    # Clone or pull the repository
    if not clone_or_pull_repo(repo_url, repo_path, branch):
        logger.error("Failed to update repository")
        return None
        
    # Get OpenAI API key
    openai_key = os.environ.get("OPENAI_API_KEY")
    if not openai_key:
        logger.error("OpenAI API key not found")
        return None
        
    # Update knowledge base
    return update_knowledge_base(repo_path, openai_key)


if __name__ == "__main__":
    # When run as a script, update from a repository
    import argparse
    
    parser = argparse.ArgumentParser(description="Update knowledge base from a GitHub repository")
    parser.add_argument("--repo", default=DEFAULT_REPO_URL, help="Repository URL to clone/pull")
    parser.add_argument("--branch", default=DEFAULT_BRANCH, help="Branch to use")
    parser.add_argument("--path", help="Path where to clone/pull the repository")
    
    args = parser.parse_args()
    
    stats = update_from_repo(args.repo, args.branch, args.path)
    
    if stats:
        print(f"Knowledge base updated successfully: {json.dumps(stats, indent=2)}")
    else:
        print("Failed to update knowledge base")
        sys.exit(1)
