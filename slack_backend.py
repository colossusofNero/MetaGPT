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

# Load environment variables (will silently fail if no .env file exists)
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
    level=logging.INFO,  # Set to INFO for production
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Your existing functions here (verify_slack_request, etc.)...

# Basic health check endpoint
@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "message": "Server is running"}), 200

# Handle both /slack and /slack/events endpoints
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