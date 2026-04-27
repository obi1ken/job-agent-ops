import base64
import email as email_lib
import os
import re
from pathlib import Path
from typing import Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


class GmailClient:
    def __init__(self, credentials_path: str, token_path: str):
        self._credentials_path = credentials_path
        self._token_path = token_path
        self._service = None

    def authenticate(self) -> None:
        creds: Optional[Credentials] = None
        token_file = Path(self._token_path)
        if token_file.exists():
            creds = Credentials.from_authorized_user_file(str(token_file), SCOPES)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(
                    self._credentials_path, SCOPES
                )
                creds = flow.run_local_server(port=0)
            token_file.write_text(creds.to_json())
        self._service = build("gmail", "v1", credentials=creds)

    def list_unread_messages(self, max_results: int = 50, label: str = "") -> list[dict]:
        self._require_auth()
        query = f"is:unread label:{label}" if label else "is:unread in:inbox"
        resp = (
            self._service.users()
            .messages()
            .list(userId="me", q=query, maxResults=max_results)
            .execute()
        )
        return resp.get("messages", [])

    def get_message(self, message_id: str) -> dict:
        self._require_auth()
        raw = (
            self._service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )
        headers = {h["name"].lower(): h["value"] for h in raw["payload"]["headers"]}
        plain, html = self._decode_body(raw["payload"])
        return {
            "id": raw["id"],
            "thread_id": raw["threadId"],
            "subject": headers.get("subject", ""),
            "sender": headers.get("from", ""),
            "date": headers.get("date", ""),
            "body_text": plain or _strip_html(html) or raw.get("snippet", ""),
            "snippet": raw.get("snippet", ""),
        }

    def mark_as_read(self, message_id: str) -> None:
        self._require_auth()
        self._service.users().messages().modify(
            userId="me",
            id=message_id,
            body={"removeLabelIds": ["UNREAD"]},
        ).execute()

    def _decode_body(self, payload: dict) -> tuple[str, str]:
        mime = payload.get("mimeType", "")
        if mime == "text/plain":
            return _b64decode(payload.get("body", {}).get("data", "")), ""
        if mime == "text/html":
            return "", _b64decode(payload.get("body", {}).get("data", ""))
        plain, html = "", ""
        for part in payload.get("parts", []):
            p, h = self._decode_body(part)
            plain = plain or p
            html = html or h
        return plain, html

    def _require_auth(self) -> None:
        if self._service is None:
            raise RuntimeError("Call authenticate() before using GmailClient.")


def _b64decode(data: str) -> str:
    if not data:
        return ""
    try:
        return base64.urlsafe_b64decode(data + "==").decode("utf-8", errors="replace")
    except Exception:
        return ""


def _strip_html(html: str) -> str:
    return re.sub(r"<[^>]+>", " ", html).strip() if html else ""
