import os
import requests
from .events import JobEvent, URGENT_EVENTS
from .embeds import build_embed

_API = "https://discord.com/api/v10"


class DiscordNotifier:
    def __init__(self):
        self.token = os.environ["DISCORD_BOT_TOKEN"]
        self.channel_id = os.environ["DISCORD_CHANNEL_ID"]
        self.charles_id = os.environ.get("DISCORD_USER_ID", "1379195691624038440")
        self._headers = {
            "Authorization": f"Bot {self.token}",
            "Content-Type": "application/json",
        }

    def send(self, event: JobEvent, **kwargs) -> dict:
        embed = build_embed(event, **kwargs)
        payload: dict = {"embeds": [embed]}
        if event in URGENT_EVENTS:
            payload["content"] = f"<@{self.charles_id}>"
        resp = requests.post(
            f"{_API}/channels/{self.channel_id}/messages",
            headers=self._headers,
            json=payload,
            timeout=10,
        )
        resp.raise_for_status()
        return resp.json()
