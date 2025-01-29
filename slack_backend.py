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

def handle_chat_command(user_message):
    """Processes a chat request using OpenAI"""
    try:
        logger.info(f"Processing chat command: {user_message}")
        client = openai.OpenAI()
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "user", "content": user_message}
            ]
        )
        
        return response.choices[0].message.content
    except Exception as e:
        logger.error(f"Error in chat command: {str(e)}")
        return f"❌ OpenAI Error: {str(e)}"

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
    """Refine the generated code using Claude"""
    try:
        logger.info("Refining code with Claude")
        
        if not CLAUDE_API_KEY:
            logger.error("CLAUDE_API_KEY is not set")
            raise ValueError("CLAUDE_API_KEY environment variable is not set")
        
        logger.info("Anthropic version: %s", anthropic.__version__)
        
        try:
            # Create base client with no additional configuration
            anthropic_client = anthropic.Anthropic(api_key=CLAUDE_API_KEY)
            logger.info("Successfully initialized Anthropic client")
        except TypeError as type_error:
            logger.error(f"TypeError during client initialization: {str(type_error)}")
            # Try alternate initialization
            try:
                logger.info("Attempting alternate client initialization")
                anthropic_client = anthropic.Client(api_key=CLAUDE_API_KEY)
                logger.info("Successfully initialized Anthropic client using alternate method")
            except Exception as alt_error:
                logger.error(f"Failed alternate initialization: {str(alt_error)}")
                raise
        except Exception as client_error:
            logger.error(f"Failed to initialize Anthropic client: {str(client_error)}")
            raise
        
        try:
            message = anthropic_client.messages.create(
                model="claude-3-opus-20240229",
                messages=[{
                    "role": "user", 
                    "content": f"""
                    Review and refine the following code for best practices and readability.
                    Ensure it is optimized and free of syntax errors.
                    Return each file's code separately and clearly labeled.
                    Code: {code}
                    """
                }]
            )
            logger.info("Successfully received response from Claude")
            
            if not message or not message.content:
                raise ValueError("Received empty response from Claude")
                
            return message.content[0].text
            
        except Exception as e:
            logger.error(f"Error during Claude API call: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            logger.error(f"Error args: {e.args}")
            raise
            
    except Exception as e:
        logger.error(f"Error refining code with Claude: {str(e)}")
        raise

def create_github_branch(branch_name):
    """Create a new branch in GitHub repository"""
    try:
        logger.info(f"Attempting to create branch: {branch_name}")
        
        headers = {
            "Authorization": f"token {GITHUB_TOKEN}",
            "Accept": "application/vnd.github.v3+json"
        }
        
        base_url = f"https://api.github.com/repos/{REPO_OWNER}/{REPO_NAME}"
        logger.info(f"Using base URL: {base_url}")
        
        # Get the SHA of the main branch
        logger.info("Fetching main branch SHA...")
        response = requests.get(f"{base_url}/git/refs/heads/main", headers=headers)
        
        if response.status_code == 404:
            logger.info("Main branch not found, trying master...")
            response = requests.get(f"{base_url}/git/refs/heads/master", headers=headers)
            if response.status_code == 404:
                logger.error("Neither main nor master branch found")
                return "❌ Could not find main or master branch"
        
        response.raise_for_status()
        base_sha = response.json()["object"]["sha"]
        logger.info(f"Got base SHA: {base_sha[:7]}")
        
        data = {
            "ref": f"refs/heads/{branch_name}",
            "sha": base_sha
        }
        
        logger.info("Creating new branch...")
        response = requests.post(f"{base_url}/git/refs", headers=headers, json=data)
        
        if response.status_code == 422:
            error_message = response.json().get("message", "Unknown error")
            logger.error(f"GitHub API error (422): {error_message}")
            if "Reference already exists" in error_message:
                return f"❌ Branch '{branch_name}' already exists"
            return f"❌ Error creating branch: {error_message}"
            
        response.raise_for_status()
        logger.info(f"Successfully created branch: {branch_name}")
        return f"✅ Branch '{branch_name}' created successfully"
        
    except requests.exceptions.RequestException as e:
        logger.error(f"GitHub API error: {str(e)}")
        return f"❌ GitHub API error: {str(e)}"
    except Exception as e:
        logger.error(f"Error creating branch: {str(e)}")
        return f"❌ Error: {str(e)}"

def create_stackblitz_project(project_name, template, description):
    """Creates a new project using AI collaboration and StackBlitz"""
    try:
        logger.info(f"Creating project: {project_name}")
        
        # Generate and refine code using AI
        generated_code = generate_code_with_chatgpt(project_name, template, description)
        logger.info("Code generated successfully")
        
        refined_code = refine_code_with_claude(generated_code)
        logger.info("Code refined successfully")
        
        # Parse the refined code to separate files (simple parsing)
        code_parts = refined_code.split("```")
        js_code = next((part for part in code_parts if "index.js" in part), "console.log('Hello World');")
        html_code = next((part for part in code_parts if "index.html" in part), "<h1>Hello World</h1>")
        css_code = next((part for part in code_parts if "style.css" in part), "body { font-family: sans-serif; }")
        
        # Create project on StackBlitz
        project_data = {
            "project[title]": project_name,
            "project[description]": description,
            "project[template]": template,
            "project[files][index.js]": js_code.strip(),
            "project[files][index.html]": html_code.strip(),
            "project[files][style.css]": css_code.strip()
        }
        
        logger.info("Sending project to StackBlitz...")
        response = requests.post("https://stackblitz.com/run", data=project_data)
        
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
@app.route("/slack/events", methods=["POST"])
def slack_handler():
    logger.info("Received Slack request")
    
    if not verify_slack_request(request):
        logger.error("Failed to verify Slack request")
        return jsonify({"error": "Invalid request signature"}), 403

    try:
        if request.is_json and request.json.get('type') == 'url_verification':
            challenge = request.json.get('challenge')
            logger.info(f"Handling URL verification. Challenge: {challenge}")
            return jsonify({"challenge": challenge})

        command_text = request.form.get('text', '').strip()
        channel_id = request.form.get('channel_id')

        logger.info(f"Processing command: {command_text}")
        logger.info(f"Channel ID: {channel_id}")

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
                elif command_text.startswith("create-project"):
                    try:
                        parts = command_text.split(maxsplit=3)
                        if len(parts) < 4:
                            response_text = (
                                "❌ Please provide all required details:\n"
                                "`/metagpt create-project <project-name> <template> <description>`\n"
                                "Templates: javascript, typescript"
                            )
                        else:
                            _, project_name, template, description = parts
                            response_text = create_stackblitz_project(project_name, template, description)
                    except Exception as e:
                        response_text = f"❌ Error creating project: {str(e)}"
                elif command_text.startswith("chat "):
                    user_message = command_text[5:]  # Remove "chat " prefix
                    response_text = handle_chat_command(user_message)
                else:
                    response_text = (
                        "❌ Unknown command. Available commands:\n"
                        "• create-branch <branch-name>\n"
                        "• create-project <project-name> <template> <description>\n"
                        "• chat <message>"
                    )

                logger.info(f"Sending response to Slack: {response_text}")
                slack_client.chat_postMessage(
                    channel=channel_id,
                    text=response_text
                )
                logger.info("Response sent successfully")
                
            except Exception as e:
                logger.error(f"Error processing command: {str(e)}")
                try:
                    slack_client.chat_postMessage(
                        channel=channel_id,
                        text=f"❌ Error: {str(e)}"
                    )
                except Exception as slack_error:
                    logger.error(f"Error sending error message to Slack: {str(slack_error)}")

        Thread(target=process_command).start()
        return jsonify({"message": "Processing request..."}), 200

    except Exception as e:
        logger.error(f"Error handling request: {str(e)}")
        return jsonify({"error": "Internal server error"}), 500

if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    app.run(host='0.0.0.0', port=port)