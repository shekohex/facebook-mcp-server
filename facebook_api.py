import json as _json
import random
import time
import requests
from typing import Any
from config import GRAPH_API_BASE_URL, PAGE_ID, PAGE_ACCESS_TOKEN

MAX_RETRIES = 5
BASE_DELAY = 1.0
MAX_SLEEP = 60.0
USAGE_THRESHOLD = 90
PROACTIVE_COOLDOWN = 60.0
THROTTLE_CODES = {4, 17, 32, 613}

ALLOWED_MESSAGING_TYPES = {"RESPONSE", "UPDATE", "MESSAGE_TAG"}
ALLOWED_MESSAGE_TAGS = {"HUMAN_AGENT"}

POST_FIELDS = "id,message,created_time"
POST_ATTACHMENT_FIELDS = (
    "description,media,media_type,target,title,type,url,"
    "subattachments.limit(25){description,media,media_type,target,title,type,url}"
)


class FacebookAPI:
    def __init__(self) -> None:
        self._next_allowed_call = 0.0

    # Generic Graph API request method
    def _request(self, method: str, endpoint: str, params: dict[str, Any], json: dict[str, Any] = None) -> dict[str, Any]:
        url = f"{GRAPH_API_BASE_URL}/{endpoint}"
        headers = {"Authorization": f"Bearer {PAGE_ACCESS_TOKEN}"}

        body: dict[str, Any] = {}
        for attempt in range(MAX_RETRIES + 1):
            wait = self._next_allowed_call - time.monotonic()
            if wait > 0:
                time.sleep(min(wait, MAX_SLEEP))

            response = requests.request(method, url, params=params, json=json, headers=headers)
            self._update_throttle_state(response)
            body = response.json() if response.content else {}

            if self._is_throttled(response, body) and attempt < MAX_RETRIES:
                time.sleep(self._retry_delay(response, attempt))
                continue
            return body
        return body

    @staticmethod
    def _is_throttled(response: requests.Response, body: dict[str, Any]) -> bool:
        if response.status_code == 429 or 500 <= response.status_code < 600:
            return True
        code = (body.get("error") or {}).get("code") if isinstance(body, dict) else None
        return code in THROTTLE_CODES

    def _retry_delay(self, response: requests.Response, attempt: int) -> float:
        """Prefer Facebook's reported wait; otherwise use exponential backoff."""
        regain = self._estimated_time_to_regain_access(response)
        if regain is not None:
            return min(regain, MAX_SLEEP)
        delay = BASE_DELAY * (2 ** attempt) + random.uniform(0, BASE_DELAY)
        return min(delay, MAX_SLEEP)

    def _update_throttle_state(self, response: requests.Response) -> None:
        """Set next-call cooldown from Graph API usage headers."""
        regain = self._estimated_time_to_regain_access(response)
        if regain is not None:
            self._next_allowed_call = time.monotonic() + min(regain, MAX_SLEEP)
            return
        if self._max_usage_percent(response) >= USAGE_THRESHOLD:
            self._next_allowed_call = time.monotonic() + PROACTIVE_COOLDOWN

    @staticmethod
    def _parse_usage_headers(response: requests.Response) -> list[dict[str, Any]]:
        entries: list[dict[str, Any]] = []
        for header in ("x-business-use-case-usage", "x-app-usage"):
            raw = response.headers.get(header)
            if not raw:
                continue
            try:
                parsed = _json.loads(raw)
            except (ValueError, TypeError):
                continue
            if isinstance(parsed, dict) and "call_count" in parsed:
                entries.append(parsed)
            elif isinstance(parsed, dict):
                for value in parsed.values():
                    if isinstance(value, list):
                        entries.extend(item for item in value if isinstance(item, dict))
        return entries

    @classmethod
    def _max_usage_percent(cls, response: requests.Response) -> float:
        usages = [
            entry.get(metric, 0) or 0
            for entry in cls._parse_usage_headers(response)
            for metric in ("call_count", "total_cputime", "total_time")
        ]
        return max(usages) if usages else 0.0

    @classmethod
    def _estimated_time_to_regain_access(cls, response: requests.Response) -> float | None:
        """Return reported regain time in seconds; header values use minutes."""
        minutes = [
            entry["estimated_time_to_regain_access"]
            for entry in cls._parse_usage_headers(response)
            if entry.get("estimated_time_to_regain_access")
        ]
        return max(minutes) * 60.0 if minutes else None

    def post_message(self, message: str) -> dict[str, Any]:
        return self._request("POST", f"{PAGE_ID}/feed", {"message": message})

    def reply_to_comment(self, comment_id: str, message: str) -> dict[str, Any]:
        return self._request("POST", f"{comment_id}/comments", {"message": message})

    def get_posts(self, include_attachments: bool = False) -> dict[str, Any]:
        posts = self._request("GET", f"{PAGE_ID}/posts", {"fields": POST_FIELDS})
        if include_attachments:
            for post in posts.get("data", []):
                post_id = post.get("id")
                if post_id:
                    post["attachments"] = self.get_post_attachments(post_id)
        return posts

    def get_post_info(self, post_id: str, include_attachments: bool = False) -> dict[str, Any]:
        fields = f"{POST_FIELDS},updated_time,permalink_url"
        post = self._request("GET", post_id, {"fields": fields})
        if include_attachments:
            post["attachments"] = self.get_post_attachments(post_id)
        return post

    def get_post_attachments(self, post_id: str) -> dict[str, Any]:
        return self._request("GET", f"{post_id}/attachments", {"fields": POST_ATTACHMENT_FIELDS, "limit": 25})

    def get_comments(self, post_id: str) -> dict[str, Any]:
        return self._request("GET", f"{post_id}/comments", {"fields": "id,message,from,created_time"})

    def get_comment_count(self, post_id: str) -> int:
        data = self._request(
            "GET",
            f"{post_id}/comments",
            {"limit": 0, "summary": "true", "filter": "stream"},
        )
        return data.get("summary", {}).get("total_count", 0)

    def delete_post(self, post_id: str) -> dict[str, Any]:
        return self._request("DELETE", f"{post_id}", {})

    def delete_comment(self, comment_id: str) -> dict[str, Any]:
        return self._request("DELETE", f"{comment_id}", {})

    def hide_comment(self, comment_id: str) -> dict[str, Any]:
        """Hide a comment from the Page."""
        return self._request("POST", f"{comment_id}", {"is_hidden": True})

    def unhide_comment(self, comment_id: str) -> dict[str, Any]:
        """Unhide a previously hidden comment."""
        return self._request("POST", f"{comment_id}", {"is_hidden": False})

    def get_insights(self, post_id: str, metric: str, period: str = "lifetime") -> dict[str, Any]:
        return self._request("GET", f"{post_id}/insights", {"metric": metric, "period": period})

    def get_bulk_insights(self, post_id: str, metrics: list[str], period: str = "lifetime") -> dict[str, Any]:
        metric_str = ",".join(metrics)
        return self.get_insights(post_id, metric_str, period)

    def post_image_to_facebook(self, image_url: str, caption: str) -> dict[str, Any]:
        params = {
            "url": image_url,
            "caption": caption
        }
        return self._request("POST", f"{PAGE_ID}/photos", params)
    
    def send_dm_to_user(self, user_id: str, message: str, messaging_type: str = "RESPONSE", message_tag: str | None = None) -> dict[str, Any]:
        if messaging_type not in ALLOWED_MESSAGING_TYPES:
            raise ValueError(f"messaging_type {messaging_type!r} not allowed; use one of {sorted(ALLOWED_MESSAGING_TYPES)}")
        if messaging_type == "MESSAGE_TAG":
            if message_tag not in ALLOWED_MESSAGE_TAGS:
                raise ValueError(f"message_tag {message_tag!r} not allowed; use one of {sorted(ALLOWED_MESSAGE_TAGS)}")
        elif message_tag is not None:
            raise ValueError("message_tag is only valid with messaging_type='MESSAGE_TAG'")

        payload: dict[str, Any] = {
            "recipient": {"id": user_id},
            "message": {"text": message},
            "messaging_type": messaging_type,
        }
        if message_tag:
            payload["tag"] = message_tag
        return self._request("POST", "me/messages", {}, json=payload)
    
    def update_post(self, post_id: str, new_message: str) -> dict[str, Any]:
        return self._request("POST", f"{post_id}", {"message": new_message})

    def schedule_post(self, message: str, publish_time: int) -> dict[str, Any]:
        params = {
            "message": message,
            "published": False,
            "scheduled_publish_time": publish_time,
        }
        return self._request("POST", f"{PAGE_ID}/feed", params)

    def get_page_fan_count(self) -> int:
        data = self._request("GET", f"{PAGE_ID}", {"fields": "fan_count"})
        return data.get("fan_count", 0)

    def get_post_share_count(self, post_id: str) -> int:
        data = self._request("GET", f"{post_id}", {"fields": "shares"})
        return data.get("shares", {}).get("count", 0)

    def get_comment_replies(self, comment_id: str) -> dict[str, Any]:
        return self._request("GET", f"{comment_id}/comments", {"fields": "id,message,from,created_time"})

    def get_post_permalink(self, post_id: str) -> dict[str, Any]:
        return self._request("GET", f"{post_id}", {"fields": "permalink_url"})

    def get_scheduled_posts(self) -> dict[str, Any]:
        return self._request("GET", f"{PAGE_ID}/scheduled_posts", {"fields": "id,message,scheduled_publish_time"})

    def get_page_info(self) -> dict[str, Any]:
        fields = "name,about,category,website,emails,phone,description,location"
        return self._request("GET", f"{PAGE_ID}", {"fields": fields})
