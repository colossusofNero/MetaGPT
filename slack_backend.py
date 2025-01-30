from flask import Flask, request, jsonify
from slack_sdk.web import WebClient
from slack_sdk.errors import SlackApiError
import requests
import os
import hmac
import hashlib
import time
import json
import openai
import anthropic
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
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
CLAUDE_API_KEY = os.getenv("CLAUDE_API_KEY")

# Initialize clients
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
        
        signing_secret = os.getenv('SLACK_SIGNING_SECRET')
        if not signing_secret:
            logger.error("No signing secret found in environment variables")
            return False
            
        my_signature = 'v0=' + hmac.new(
            signing_secret.encode('utf-8'),
            sig_basestring.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(my_signature, slack_signature)
    except Exception as e:
        logger.error(f"Error in verify_slack_request: {str(e)}")
        return False

def generate_code_with_chatgpt(project_name, template, description):
    """Generate initial code using ChatGPT"""
    try:
        logger.info(f"Generating code with ChatGPT for project: {project_name}")
        client = openai.OpenAI()
        
        prompt = f"""
        Create a new {template} project named "{project_name}".
        Include a basic index.js, index.html, and style.css file.
        Add comments explaining the code.
        Project Description: {description}
        Return the code for each file separately, clearly labeled.
        """
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert software engineer."},
                {"role": "user", "content": prompt}
            ]
        )
        
        logger.info("Successfully generated code with ChatGPT")
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error generating code with ChatGPT: {str(e)}")
        raise

def refine_code_with_claude(code):
    """Refine the generated code using Claude via direct API call"""
    try:
        logger.info("Refining code with Claude")
        
        if not CLAUDE_API_KEY:
            logger.error("CLAUDE_API_KEY is not set")
            raise ValueError("CLAUDE_API_KEY environment variable is not set")
        
        headers = {
            "x-api-key": CLAUDE_API_KEY,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }
        
        data = {
            "model": "claude-3-opus-20240229",
            "max_tokens": 1000,  # Ensures response length is properly set
            "messages": [
                {
                    "role": "user",
                    "content": f"""
                    Review and refine the following code for best practices and readability.
                    Ensure it is optimized and free of syntax errors.
                    Return each file's code separately and clearly labeled.
                    Code: {code}
                    """
                }
            ]
        }
        
        logger.info("Making request to Claude API")
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers,
            json=data
        )
        
        if response.status_code != 200:
            logger.error(f"Claude API error: {response.status_code} - {response.text}")
            raise Exception(f"Claude API returned status code {response.status_code}")
            
        response_data = response.json()
        logger.info("Successfully received response from Claude")
        
        if not response_data or 'content' not in response_data or not response_data['content']:
            raise ValueError("Received empty response from Claude")
            
        return response_data['content'][0]['text']
    except Exception as e:
        logger.error(f"Error refining code with Claude: {str(e)}")
        raise

def create_stackblitz_project(project_name, template, description):
    """Creates a new project using AI collaboration and StackBlitz"""
    try:
        logger.info(f"Creating project: {project_name}")
        
        # Generate and refine code using AI
        generated_code = generate_code_with_chatgpt(project_name, template, description)
        logger.info("Code generated successfully")
        
        refined_code = refine_code_with_claude(generated_code)
        logger.info("Code refined successfully")
        
        # Create project on StackBlitz
        stackblitz_url = f"https://run.stackblitz.com/api/github/{REPO_OWNER}/{REPO_NAME}"
        response = requests.post(stackblitz_url)
        
        if response.status_code == 200:
            project_url = response.url
            logger.info(f"Project created successfully at: {project_url}")
            return f"✅ Project '{project_name}' created successfully! Open it here: {project_url}"
        else:
            error_msg = f"Failed to create project. Status: {response.status_code}"
            logger.error(error_msg)
            return f"❌ {error_msg}"
            
    except Exception as e:
        logger.error(f"Error creating project: {str(e)}")
        return f"❌ Error: {str(e)}"

@app.route("/", methods=["GET"])
def health_check():
    return jsonify({"status": "healthy", "message": "Server is running"}), 200

@app.route("/slack", methods=["POST"])
def slack_handler():
    logger.info("Received Slack request")
    
    if not verify_slack_request(request):
        logger.error("Failed to verify Slack request")
        return jsonify({"error": "Invalid request signature"}), 403

    try:
        command_text = request.form.get('text', '').strip()
        channel_id = request.form.get('channel_id')

        logger.info(f"Processing command: {command_text}")
        logger.info(f"Channel ID: {channel_id}")

        if command_text.startswith("create-project"):
            parts = command_text.split(maxsplit=3)
            if len(parts) < 4:
                response_text = "❌ Please provide all required details: `/metagpt create-project <project-name> <template> <description>`"
            else:
                _, project_name, template, description = parts
                response_text = create_stackblitz_project(project_name, template, description)

        slack_client.chat_postMessage(channel=channel_id, text=response_text)
        return jsonify({"message": "Processing request..."}), 200

    except Exception as e:
        logger.error(f"Error handling request: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
