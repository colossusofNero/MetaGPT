from flask import Flask, request, jsonify
from slack_sdk.web import WebClient
from slack_sdk.errors import SlackApiError
import requests
import os
import hmac
import hashlib
import time
from threading import Thread
import logging
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration from environment variables
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
SLACK_SIGNING_SECRET = os.getenv('SLACK_SIGNING_SECRET')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_OWNER = os.getenv('REPO_OWNER')
REPO_NAME = os.getenv('REPO_NAME')

# Initialize Slack client
slack_client = WebClient(token=SLACK_BOT_TOKEN)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verify_slack_request(request):
    """Verify that the request actually came from Slack"""
    try:
        if os.getenv('DEVELOPMENT_MODE') == 'true':
            logger.warning("Development mode enabled - skipping signature verification")
            return True
            
        timestamp = request.headers.get('X-Slack-Request-Timestamp')
        if not timestamp:
            logger.error("No timestamp in headers")
            return False
            
        current_time = time.time()
        if abs(current_time - int(timestamp)) > 60 * 5:
            logger.error(f"Invalid timestamp. Current time: {current_time}, Request time: {timestamp}")
            return False

        slack_signature = request.headers.get('X-Slack-Signature')
        if not slack_signature:
            logger.error("No Slack signature in headers")
            return False

        request_body = request.get_data().decode('utf-8')
        sig_basestring = f"v0:{timestamp}:{request_body}"
        
        # Get signing secret
        signing_secret = os.getenv('SLACK_SIGNING_SECRET')
        if not signing_secret:
            logger.error("No signing secret found in environment variables")
            return False
            
        my_signature = 'v0=' + hmac.new(
            signing_secret.encode('utf-8'),
            sig_basestring.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        logger.debug(f"Base string: {sig_basestring}")
        logger.debug(f"My signature: {my_signature}")
        logger.debug(f"Slack signature: {slack_signature}")
        
        return hmac.compare_digest(my_signature, slack_signature)
    except Exception as e:
        logger.error(f"Error in verify_slack_request: {str(e)}")
        return False

def create_github_branch(branch_name):
    """Create a new branch in GitHub repository"""
    try:
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        base_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
        
        # Get the SHA of the main branch
        response = requests.get(f"{base_url}/git/refs/heads/main", headers=headers)
        
        if response.status_code == 404:
            response = requests.get(f"{base_url}/git/refs/heads/master", headers=headers)
            if response.status_code == 404:
                return "❌ Could not find main or master branch"
        
        response.raise_for_status()
        base_sha = response.json()["object"]["sha"]
        
        data = {
            "ref": f"refs/heads/{branch_name}",
            "sha": base_sha
        }
        
        response = requests.post(f"{base_url}/git/refs", headers=headers, json=data)
        
        if response.status_code == 422:
            error_message = response.json().get("message", "Unknown error")
            if "Reference already exists" in error_message:
                return f"❌ Branch '{branch_name}' already exists"
            return f"❌ Error creating branch: {error_message}"
            
        response.raise_for_status()
        return f"✅ Branch '{branch_name}' created successfully"
        
    except Exception as e:
        logger.error(f"Error creating branch: {str(e)}")
        return f"❌ Error: {str(e)}"

def list_github_branches():
    """List all branches in GitHub repository"""
    try:
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        base_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
        response = requests.get(f"{base_url}/branches", headers=headers)
        response.raise_for_status()
        
        branches = response.json()
        if not branches:
            return "No branches found in the repository."
            
        branch_list = []
        for branch in branches:
            branch_list.append(f"• {branch['name']} ({branch['commit']['sha'][:7]})")
            
        return "Repository branches:\n" + "\n".join(branch_list)
        
    except Exception as e:
        logger.error(f"Error listing branches: {str(e)}")
        return f"❌ Error: {str(e)}"

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "message": "Server is running"}), 200

@app.route("/slack", methods=["POST"])
@app.route("/slack/events", methods=["POST"])
def slack_handler():
    logger.info("Received Slack request")
    
    if not verify_slack_request(request):
        logger.error("Failed to verify Slack request")
        return jsonify({"error": "Invalid request signature"}), 403

    try:
        # Handle URL verification
        if request.is_json and request.json.get('type') == 'url_verification':
            return jsonify({"challenge": request.json.get('challenge')})

        # Get command text and channel
        command_text = request.form.get('text', '').strip()
        channel_id = request.form.get('channel_id')
        
        logger.info(f"Processing command: {command_text}")

        def process_command():
            try:
                if not channel_id:
                    logger.error("No channel_id provided in request")
                    return
                
                if command_text.startswith("create-branch"):
                    parts = command_text.split(maxsplit=1)
                    if len(parts) != 2:
                        response_text = "❌ Please provide a branch name: `/command create-branch branch-name`"
                    else:
                        branch_name = parts[1].strip()
                        response_text = create_github_branch(branch_name)
                elif command_text.strip() == "list-branches":
                    response_text = list_github_branches()
                else:
                    response_text = "❌ Unknown command. Available commands:\n• create-branch <branch-name>\n• list-branches"

                slack_client.chat_postMessage(
                    channel=channel_id,
                    text=response_text
                )
            except Exception as e:
                logger.error(f"Error processing command: {str(e)}")
                slack_client.chat_postMessage(
                    channel=channel_id,
                    text=f"❌ Error: {str(e)}"
                )

        Thread(target=process_command).start()
        return jsonify({"message": "Processing request..."}), 200

    except Exception as e:
        logger.error(f"Error handling request: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port)