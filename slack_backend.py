from flask import Flask, request, jsonify
from slack_sdk.web import WebClient
from slack_sdk.errors import SlackApiError
import requests
import os
import hmac
import hashlib
import time
import logging
from dotenv import load_dotenv
from threading import Thread

# Load environment variables
load_dotenv()

app = Flask(__name__)

# Configuration from environment variables
SLACK_BOT_TOKEN = os.getenv('SLACK_BOT_TOKEN')
SLACK_SIGNING_SECRET = os.getenv('SLACK_SIGNING_SECRET')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
REPO_OWNER = os.getenv('REPO_OWNER')
REPO_NAME = os.getenv('REPO_NAME')
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

# Initialize Slack client
slack_client = WebClient(token=SLACK_BOT_TOKEN)

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def verify_slack_request(request):
    """Verify that the request actually came from Slack"""
    try:
        if os.getenv('DEVELOPMENT_MODE') == 'true':
            logger.warning("Development mode enabled - skipping signature verification")
            return True

        timestamp = request.headers.get('X-Slack-Request-Timestamp')
        slack_signature = request.headers.get('X-Slack-Signature')

        if not timestamp or not slack_signature:
            logger.error("Missing timestamp or Slack signature in headers")
            return False

        if abs(time.time() - int(timestamp)) > 60 * 5:
            logger.error("Invalid timestamp - request too old")
            return False

        request_body = request.get_data().decode('utf-8')
        sig_basestring = f"v0:{timestamp}:{request_body}"

        if not SLACK_SIGNING_SECRET:
            logger.error("SLACK_SIGNING_SECRET is not set")
            return False

        my_signature = 'v0=' + hmac.new(
            SLACK_SIGNING_SECRET.encode('utf-8'),
            sig_basestring.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()

        return hmac.compare_digest(my_signature, slack_signature)
    except Exception as e:
        logger.error(f"Error verifying Slack request: {str(e)}")
        return False

def handle_chat_command(user_message):
    """Processes a chat request using OpenAI"""
    try:
        logger.info(f"Processing chat command: {user_message}")
        response = requests.post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
            json={
                "model": "gpt-4",
                "messages": [{"role": "user", "content": user_message}]
            }
        )
        response_data = response.json()
        return response_data.get("choices", [{}])[0].get("message", {}).get("content", "❌ OpenAI Error: No valid response received")
    except Exception as e:
        logger.error(f"Error in chat command: {str(e)}")
        return f"❌ OpenAI Error: {str(e)}"

def refine_code_with_claude(code):
    """Refine the generated code using Claude API"""
    try:
        logger.info("Refining code with Claude")

        if not CLAUDE_API_KEY:
            raise ValueError("CLAUDE_API_KEY environment variable is not set")

        headers = {
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json"
        }

        data = {
            "model": "claude-3-opus-20240229",
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": f"Refine this code:\n{code}"}]
        }

        response = requests.post("https://api.anthropic.com/v1/messages", headers=headers, json=data)
        response.raise_for_status()

        response_data = response.json()
        return response_data.get("content", [{}])[0].get("text", "❌ Claude API Error: No valid response")
    except Exception as e:
        logger.error(f"Error refining code with Claude: {str(e)}")
        return f"❌ Claude API Error: {str(e)}"

def create_stackblitz_project(project_name, template, description):
    """Creates a new project on StackBlitz using AI-generated code."""
    try:
        logger.info(f"Creating project: {project_name}")

        generated_code = handle_chat_command(f"Generate a {template} project named '{project_name}'. Description: {description}")
        refined_code = refine_code_with_claude(generated_code)

        stackblitz_api_url = f"https://stackblitz.com/github/{REPO_OWNER}/{REPO_NAME}?file=index.js"

        response = requests.get(stackblitz_api_url)

        if response.status_code == 200:
            logger.info(f"Project created successfully: {stackblitz_api_url}")
            return f"✅ Project '{project_name}' created successfully! Open it here: {stackblitz_api_url}"
        else:
            logger.error(f"StackBlitz API error {response.status_code}: {response.text}")
            return f"❌ StackBlitz API Error: {response.status_code}"
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        return f"❌ Error: {str(e)}"

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "message": "Server is running"}), 200

@app.route("/slack", methods=["POST"])
def slack_handler():
    """Handles Slack events"""
    logger.info("Received Slack request")

    if not verify_slack_request(request):
        return jsonify({"error": "Invalid request signature"}), 403

    try:
        if request.is_json and request.json.get('type') == 'url_verification':
            return jsonify({"challenge": request.json.get('challenge')})

        command_text = request.form.get('text', '').strip()
        channel_id = request.form.get('channel_id')

        def process_command():
            try:
                if not channel_id:
                    return
                
                if command_text.startswith("create-project"):
                    parts = command_text.split(maxsplit=3)
                    if len(parts) < 4:
                        response_text = "❌ Usage: `/metagpt create-project <name> <template> <description>`"
                    else:
                        _, project_name, template, description = parts
                        response_text = create_stackblitz_project(project_name, template, description)
                elif command_text.startswith("chat "):
                    user_message = command_text[5:]
                    response_text = handle_chat_command(user_message)
                else:
                    response_text = "❌ Unknown command. Use `/metagpt create-project` or `/metagpt chat`"

                slack_client.chat_postMessage(channel=channel_id, text=response_text)
            except Exception as e:
                slack_client.chat_postMessage(channel=channel_id, text=f"❌ Error: {str(e)}")

        Thread(target=process_command).start()
        return jsonify({"message": "Processing request..."}), 200

    except Exception as e:
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
