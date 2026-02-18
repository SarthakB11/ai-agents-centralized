"""
Slack Integration — Start a Slack bot wired to any agent.
"""

import os
import logging

logger = logging.getLogger(__name__)


def create_slack_bot(agent):
    """
    Create and return a Slack Bolt app wired to the given agent.

    Usage:
        from agno_single_agent_framework.integrations.slack import create_slack_bot
        bot = create_slack_bot(my_agent)
        bot.start()  # Starts Socket Mode
    """
    try:
        from slack_bolt import App
        from slack_bolt.adapter.socket_mode import SocketModeHandler
    except ImportError:
        raise ImportError("slack_bolt not installed. Run: pip install slack_bolt")

    app = App(
        token=os.getenv("SLACK_BOT_TOKEN"),
        signing_secret=os.getenv("SLACK_SIGNING_SECRET"),
    )

    @app.event("app_mention")
    def handle_mention(event, say):
        user_input = event.get("text", "")
        user_id = event.get("user", "unknown")
        channel = event.get("channel", "unknown")
        response = agent.handle_request({
            "input": user_input, "request_id": f"slack-{event.get('ts', '')}",
            "session_id": f"slack-{channel}-{user_id}",
            "metadata": {"source": "slack", "channel": channel, "user": user_id},
        })
        say(response["output"])

    @app.event("message")
    def handle_dm(event, say):
        if event.get("bot_id"):
            return
        user_input = event.get("text", "")
        user_id = event.get("user", "unknown")
        response = agent.handle_request({
            "input": user_input, "request_id": f"slack-dm-{event.get('ts', '')}",
            "session_id": f"slack-dm-{user_id}",
            "metadata": {"source": "slack_dm", "user": user_id},
        })
        say(response["output"])

    class SlackBot:
        def __init__(self):
            self.app = app

        def start(self):
            token = os.getenv("SLACK_APP_TOKEN")
            if not token:
                raise ValueError("SLACK_APP_TOKEN not set for Socket Mode")
            handler = SocketModeHandler(app, token)
            logger.info("⚡ Slack bot started in Socket Mode")
            handler.start()

    return SlackBot()
