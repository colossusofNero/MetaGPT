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

if os.path.exists(".env"):
    from dotenv import load_dotenv
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
    level=logging.DEBUG,  # Set to DEBUG for more verbose output
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def verify_slack_request(request):
    """
    Verify that the request actually came from Slack
    """
    try:
        # Debug logging of request details
        logger.debug("Headers: %s", dict(request.headers))
        logger.debug("Form Data: %s", request.form)
        logger.debug("Raw Data: %s", request.get_data().decode('utf-8'))
        
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
            
        # Calculate expected signature
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

def send_to_claude(message):
    """Send a message to Claude"""
    try:
        # TODO: Implement Claude API integration
        return f"✅ Message sent to Claude: {message}"
    except Exception as e:
        return f"❌ Error sending to Claude: {str(e)}"

def send_to_chatgpt(message):
    """Send a message to ChatGPT"""
    try:
        # TODO: Implement ChatGPT API integration
        return f"✅ Message sent to ChatGPT: {message}"
    except Exception as e:
        return f"❌ Error sending to ChatGPT: {str(e)}"

def send_to_bolt(message):
    """Send a message to Bolt.new"""
    try:
        # TODO: Implement Bolt.new API integration
        return f"✅ Message sent to Bolt.new: {message}"
    except Exception as e:
        return f"❌ Error sending to Bolt.new: {str(e)}"

def start_conversation():
    """Start a new AI conversation thread"""
    try:
        # TODO: Implement conversation management
        return "✅ New conversation started"
    except Exception as e:
        return f"❌ Error starting conversation: {str(e)}"

def end_conversation():
    """End current conversation"""
    try:
        # TODO: Implement conversation end
        return "✅ Conversation ended"
    except Exception as e:
        return f"❌ Error ending conversation: {str(e)}"

def list_conversations():
    """List active conversations"""
    try:
        # TODO: Implement conversation listing
        return "✅ Active conversations:\n• None yet"
    except Exception as e:
        return f"❌ Error listing conversations: {str(e)}"

def switch_model(model_name):
    """Switch between different AI models"""
    try:
        # TODO: Implement model switching
        return f"✅ Switched to model: {model_name}"
    except Exception as e:
        return f"❌ Error switching model: {str(e)}"

def set_context(context):
    """Set conversation context"""
    try:
        # TODO: Implement context setting
        return f"✅ Context set: {context}"
    except Exception as e:
        return f"❌ Error setting context: {str(e)}"

def get_history():
    """Get conversation history"""
    try:
        # TODO: Implement history retrieval
        return "✅ Conversation history:\n• No history yet"
    except Exception as e:
        return f"❌ Error getting history: {str(e)}"

def clear_history():
    """Clear conversation history"""
    try:
        # TODO: Implement history clearing
        return "✅ Conversation history cleared"
    except Exception as e:
        return f"❌ Error clearing history: {str(e)}"

def summarize_conversation():
    """Get conversation summary"""
    try:
        # TODO: Implement conversation summarization
        return "✅ Conversation summary:\n• No active conversation"
    except Exception as e:
        return f"❌ Error summarizing conversation: {str(e)}"
    try:
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        base_url = f"https://api.github.com/repos/{REPO_OWNER}/MetaGPT"
        
        # Check if branch exists
        response = requests.get(f"{base_url}/branches/{branch_name}", headers=headers)
        if response.status_code == 404:
            return f"❌ Branch '{branch_name}' not found"
            
        # Delete branch
        delete_url = f"{base_url}/git/refs/heads/{branch_name}"
        response = requests.delete(delete_url, headers=headers)
        
        if response.status_code == 204:
            return f"✅ Branch '{branch_name}' deleted successfully"
        else:
            return f"❌ Failed to delete branch: {response.json().get('message', 'Unknown error')}"
            
    except requests.exceptions.RequestException as e:
        error_msg = f"❌ GitHub API error: {str(e)}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"❌ Error deleting branch: {str(e)}"
        logger.error(error_msg)
        return error_msg
    try:
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        base_url = f"https://api.github.com/repos/{REPO_OWNER}/MetaGPT"
        logger.debug(f"Getting branches from: {base_url}/branches")
        
        response = requests.get(f"{base_url}/branches", headers=headers)
        response.raise_for_status()
        
        branches = response.json()
        if not branches:
            return "No branches found in the repository."
            
        # Format branch information
        branch_list = []
        for branch in branches:
            branch_list.append(f"• {branch['name']} ({branch['commit']['sha'][:7]})")
            
        return "Repository branches:\n" + "\n".join(branch_list)
        
    except requests.exceptions.RequestException as e:
        error_msg = f"❌ GitHub API error: {str(e)}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"❌ Error listing branches: {str(e)}"
        logger.error(error_msg)
        return error_msg
    try:
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        # Get the SHA of the main branch
        base_url = f"https://api.github.com/repos/{REPO_OWNER}/MetaGPT"
        logger.debug(f"Getting main branch SHA from: {base_url}")
        
        # First, try to get the SHA of the 'main' branch
        response = requests.get(f"{base_url}/git/refs/heads/main", headers=headers)
        
        # If main branch doesn't exist, try master
        if response.status_code == 404:
            response = requests.get(f"{base_url}/git/refs/heads/master", headers=headers)
            if response.status_code == 404:
                return "❌ Could not find main or master branch. Please check your repository."
        
        response.raise_for_status()
        base_sha = response.json()["object"]["sha"]
        
        # Create new branch with full ref path
        data = {
            "ref": f"refs/heads/{branch_name}",
            "sha": base_sha
        }
        
        logger.debug(f"Creating branch with data: {data}")
        response = requests.post(f"{base_url}/git/refs", headers=headers, json=data)
        
        if response.status_code == 422:
            error_message = response.json().get("message", "Unknown error")
            logger.error(f"GitHub API error details: {error_message}")
            if "Reference already exists" in error_message:
                return f"❌ Branch '{branch_name}' already exists"
            return f"❌ Error creating branch: {error_message}"
            
        response.raise_for_status()
        return f"✅ Branch '{branch_name}' created successfully from SHA: {base_sha[:7]}"
        
    except requests.exceptions.RequestException as e:
        error_msg = f"❌ GitHub API error: {str(e)}"
        logger.error(error_msg)
        return error_msg
    except Exception as e:
        error_msg = f"❌ Error creating branch: {str(e)}"
        logger.error(error_msg)
        return error_msg

        # Create new branch
        data = {
            "ref": f"refs/heads/{branch_name}",
            "sha": base_sha
        }
        response = requests.post(f"{base_url}/git/refs", headers=headers, json=data)
        response.raise_for_status()
        
        return f"✅ Branch '{branch_name}' created successfully!"
    except requests.exceptions.RequestException as e:
        error_msg = f"❌ GitHub API error: {str(e)}"
        logger.error(error_msg)
        return error_msg

# Basic health check endpoint
@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "message": "Server is running"}), 200

# Handle both /slack and /slack/events endpoints
@app.route("/slack", methods=["POST"])
@app.route("/slack/events", methods=["POST"])
def slack_handler():
    logger.debug("Received Slack request")
    
    # Add detailed request logging
    logger.debug("Request Method: %s", request.method)
    logger.debug("Request Path: %s", request.path)
    logger.debug("Request Headers: %s", dict(request.headers))
    if request.is_json:
        logger.debug("JSON Data: %s", request.get_json())
    if request.form:
        logger.debug("Form Data: %s", dict(request.form))
    
    if not verify_slack_request(request):
        logger.error("Failed to verify Slack request")
        return jsonify({"error": "Invalid request signature"}), 403

    try:
        # Log the entire request for debugging
        logger.debug("Request Form: %s", request.form)
        logger.debug("Request JSON: %s", request.get_json(silent=True))
        
        # Handle URL verification
        if request.is_json and request.json.get('type') == 'url_verification':
            return jsonify({"challenge": request.json.get('challenge')})

        # Get command text and channel
        command_text = request.form.get('text', '').strip()
        channel_id = request.form.get('channel_id')
        
        logger.debug(f"Command text: {command_text}")
        logger.debug(f"Channel ID: {channel_id}")

        def process_command():
            try:
                # Ensure we have a channel_id
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
                
                # Log the response attempt
                logger.debug(f"Attempting to send message to channel {channel_id}: {response_text}")

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
    # Set development mode
    os.environ['DEVELOPMENT_MODE'] = 'true'
    
    # Verify environment variables are set
    required_vars = ['SLACK_BOT_TOKEN', 'SLACK_SIGNING_SECRET', 'GITHUB_TOKEN', 'REPO_OWNER', 'REPO_NAME']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"Missing required environment variables: {', '.join(missing_vars)}")
        exit(1)
        
    logger.info("Starting server in development mode...")
    app.run(host='0.0.0.0', port=5000, debug=True)