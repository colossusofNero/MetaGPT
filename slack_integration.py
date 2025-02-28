import os
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

# Slack Bot Token and Channel ID
SLACK_BOT_TOKEN = "place-holder"
CHANNEL_ID = "place-holder"               

# Create a Slack client
client = WebClient(token=SLACK_BOT_TOKEN)

# Function to send a message
def send_message(text):
    try:
        response = client.chat_postMessage(
            channel=CHANNEL_ID,
            text=text
        )
        print(f"Message sent: {response['message']['text']}")
    except SlackApiError as e:
        print(f"Error sending message: {e.response['error']}")

# Example usage
send_message("Hello from MetaGPT-Bot!")
