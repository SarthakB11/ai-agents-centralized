"""
Slack Integration for AI Agents.

This module provides a ready-to-use Slack bot integration using
the Bolt framework. It connects incoming Slack messages to the
agent's handle_request() method and posts the response back.

Setup:
  1. Create a Slack App at https://api.slack.com/apps
  2. Enable "Socket Mode" or set up Event Subscriptions
  3. Add Bot Token Scopes: chat:write, app_mentions:read, im:history
  4. Set SLACK_BOT_TOKEN and SLACK_SIGNING_SECRET in .env
  5. Subscribe to events: app_mention, message.im

Usage:
  from app.integrations.slack_integration import start_slack_bot
  start_slack_bot()
"""

import os
import logging
from app.agent import Agent

try:
    from slack_bolt import App
    from slack_bolt.adapter.socket_mode import SocketModeHandler
except ImportError:
    App = None
    SocketModeHandler = None

logger = logging.getLogger(__name__)

# Initialize agent
agent = Agent()


def create_slack_app() -> "App":
    """Create and configure the Slack Bolt app."""
    if App is None:
        raise ImportError(
            "slack_bolt not installed. Run: pip install slack_bolt"
        )

    app = App(
        token=os.getenv("SLACK_BOT_TOKEN"),
        signing_secret=os.getenv("SLACK_SIGNING_SECRET"),
    )

    @app.event("app_mention")
    def handle_mention(event, say):
        """Respond when the bot is @mentioned in a channel."""
        user_input = event.get("text", "")
        user_id = event.get("user", "unknown")
        channel = event.get("channel", "unknown")

        logger.info(f"Slack mention from {user_id} in {channel}: {user_input}")

        response = agent.handle_request({
            "input": user_input,
            "request_id": f"slack-{event.get('ts', '')}",
            "session_id": f"slack-{channel}-{user_id}",
            "metadata": {"source": "slack", "channel": channel, "user": user_id},
        })

        say(response["output"])

    @app.event("message")
    def handle_direct_message(event, say):
        """Respond to direct messages."""
        # Ignore bot's own messages
        if event.get("bot_id"):
            return

        user_input = event.get("text", "")
        user_id = event.get("user", "unknown")
        channel = event.get("channel", "unknown")

        logger.info(f"Slack DM from {user_id}: {user_input}")

        response = agent.handle_request({
            "input": user_input,
            "request_id": f"slack-dm-{event.get('ts', '')}",
            "session_id": f"slack-dm-{user_id}",
            "metadata": {"source": "slack_dm", "user": user_id},
        })

        say(response["output"])

    return app


def start_slack_bot():
    """Start the Slack bot in Socket Mode."""
    app = create_slack_app()
    socket_token = os.getenv("SLACK_APP_TOKEN")  # xapp-... token for socket mode
    if not socket_token:
        raise ValueError("SLACK_APP_TOKEN not set. Required for Socket Mode.")

    handler = SocketModeHandler(app, socket_token)
    logger.info("⚡ Slack bot started in Socket Mode")
    handler.start()


if __name__ == "__main__":
    start_slack_bot()
