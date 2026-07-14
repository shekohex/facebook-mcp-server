from typing import Any
from facebook_api import FacebookAPI


REACTION_METRICS = {
    "like": "post_reactions_like_total",
    "love": "post_reactions_love_total",
    "wow": "post_reactions_wow_total",
    "haha": "post_reactions_haha_total",
    "sad": "post_reactions_sorry_total",
    "angry": "post_reactions_anger_total",
}


class Manager:
    def __init__(self):
        self.api = FacebookAPI()

    def post_to_facebook(self, message: str) -> dict[str, Any]:
        return self.api.post_message(message)

    def reply_to_comment(self, post_id: str, comment_id: str, message: str) -> dict[str, Any]:
        return self.api.reply_to_comment(comment_id, message)

    def get_page_posts(self, include_attachments: bool = False) -> dict[str, Any]:
        return self.api.get_posts(include_attachments)

    def get_post_info(self, post_id: str, include_attachments: bool = False) -> dict[str, Any]:
        return self.api.get_post_info(post_id, include_attachments)

    def get_post_comments(self, post_id: str) -> dict[str, Any]:
        return self.api.get_comments(post_id)

    def delete_post(self, post_id: str) -> dict[str, Any]:
        return self.api.delete_post(post_id)

    def delete_comment(self, comment_id: str) -> dict[str, Any]:
        return self.api.delete_comment(comment_id)

    def hide_comment(self, comment_id: str) -> dict[str, Any]:
        return self.api.hide_comment(comment_id)

    def unhide_comment(self, comment_id: str) -> dict[str, Any]:
        return self.api.unhide_comment(comment_id)

    def delete_comment_from_post(self, post_id: str, comment_id: str) -> dict[str, Any]:
        return self.api.delete_comment(comment_id)

    def filter_negative_comments(self, comments: dict[str, Any]) -> list[dict[str, Any]]:
        keywords = ["bad", "terrible", "awful", "hate", "dislike", "problem", "issue"]
        return [c for c in comments.get("data", []) if any(k in c.get("message", "").lower() for k in keywords)]

    def get_number_of_comments(self, post_id: str) -> int:
        return self.api.get_comment_count(post_id)

    def get_number_of_likes(self, post_id: str) -> int:
        return self.api._request("GET", post_id, {"fields": "likes.summary(true)"}).get("likes", {}).get("summary", {}).get("total_count", 0)

    def get_post_insights(self, post_id: str) -> dict[str, Any]:
        metrics = [
            "post_impressions", "post_impressions_unique", "post_impressions_paid",
            "post_impressions_organic", "post_clicks",
            "post_reactions_like_total", "post_reactions_love_total", "post_reactions_wow_total",
            "post_reactions_haha_total", "post_reactions_sorry_total", "post_reactions_anger_total",
        ]
        return self.api.get_bulk_insights(post_id, metrics)
    
    def get_post_impressions(self, post_id: str) -> dict[str, Any]:
        return self.api.get_insights(post_id, "post_impressions")

    def get_post_impressions_unique(self, post_id: str) -> dict[str, Any]:
        return self.api.get_insights(post_id, "post_impressions_unique")

    def get_post_impressions_paid(self, post_id: str) -> dict[str, Any]:
        return self.api.get_insights(post_id, "post_impressions_paid")

    def get_post_impressions_organic(self, post_id: str) -> dict[str, Any]:
        return self.api.get_insights(post_id, "post_impressions_organic")

    def get_post_clicks(self, post_id: str) -> dict[str, Any]:
        return self.api.get_insights(post_id, "post_clicks")

    def get_post_media_views(self, post_id: str) -> dict[str, Any]:
        return self.api.get_insights(post_id, "post_media_view")

    def get_post_unique_media_viewers(self, post_id: str) -> dict[str, Any]:
        return self.api.get_insights(post_id, "post_total_media_view_unique")

    def get_post_metrics(self, post_id: str) -> dict[str, Any]:
        reaction_response = self.api.get_bulk_insights(post_id, list(REACTION_METRICS.values()))
        insight_responses = {
            "clicks": self.get_post_clicks(post_id),
            "media_views": self.get_post_media_views(post_id),
            "unique_media_viewers": self.get_post_unique_media_viewers(post_id),
        }

        result: dict[str, Any] = {
            "post_id": post_id,
            "reactions": None if "error" in reaction_response else self._normalize_reactions(reaction_response),
            "comments": self.get_number_of_comments(post_id),
            "shares": self.get_post_share_count(post_id),
        }
        errors: dict[str, Any] = {}
        for name, response in insight_responses.items():
            value, error = self._extract_insight_value(response)
            result[name] = value
            if error:
                errors[name] = error
        if "error" in reaction_response:
            errors["reactions"] = reaction_response["error"]
        if errors:
            result["errors"] = errors
        return result

    @staticmethod
    def _extract_insight_value(response: dict[str, Any]) -> tuple[Any, dict[str, Any] | None]:
        if "error" in response:
            return None, response["error"]
        data = response.get("data", [])
        if not data:
            return 0, None
        return data[0].get("values", [{}])[0].get("value", 0), None

    @classmethod
    def _normalize_reactions(cls, response: dict[str, Any]) -> dict[str, Any]:
        values_by_metric = {
            item.get("name"): item.get("values", [{}])[0].get("value", 0)
            for item in response.get("data", [])
        }
        reactions = {
            name: values_by_metric.get(metric, 0)
            for name, metric in REACTION_METRICS.items()
        }
        reactions["total"] = sum(value for value in reactions.values() if isinstance(value, (int, float)))
        return reactions

    def get_post_reactions_like_total(self, post_id: str) -> dict[str, Any]:
        return self.api.get_insights(post_id, "post_reactions_like_total")

    def get_post_reactions_love_total(self, post_id: str) -> dict[str, Any]:
        return self.api.get_insights(post_id, "post_reactions_love_total")

    def get_post_reactions_wow_total(self, post_id: str) -> dict[str, Any]:
        return self.api.get_insights(post_id, "post_reactions_wow_total")

    def get_post_reactions_haha_total(self, post_id: str) -> dict[str, Any]:
        return self.api.get_insights(post_id, "post_reactions_haha_total")

    def get_post_reactions_sorry_total(self, post_id: str) -> dict[str, Any]:
        return self.api.get_insights(post_id, "post_reactions_sorry_total")

    def get_post_reactions_anger_total(self, post_id: str) -> dict[str, Any]:
        return self.api.get_insights(post_id, "post_reactions_anger_total")

    def get_post_top_commenters(self, post_id: str) -> list[dict[str, Any]]:
        comments = self.get_post_comments(post_id).get("data", [])
        counter = {}
        for comment in comments:
            user_id = comment.get("from", {}).get("id")
            if user_id:
                counter[user_id] = counter.get(user_id, 0) + 1
        return sorted([{"user_id": k, "count": v} for k, v in counter.items()], key=lambda x: x["count"], reverse=True)

    def post_image_to_facebook(self, image_url: str, caption: str) -> dict[str, Any]:
        return self.api.post_image_to_facebook(image_url, caption)

    def send_dm_to_user(self, user_id: str, message: str, messaging_type: str = "RESPONSE", message_tag: str | None = None) -> dict[str, Any]:
        return self.api.send_dm_to_user(user_id, message, messaging_type, message_tag)
    
    def update_post(self, post_id: str, new_message: str) -> dict[str, Any]:
        return self.api.update_post(post_id, new_message)

    def schedule_post(self, message: str, publish_time: int) -> dict[str, Any]:
        return self.api.schedule_post(message, publish_time)

    def get_page_fan_count(self) -> int:
        return self.api.get_page_fan_count()

    def get_post_share_count(self, post_id: str) -> int:
        return self.api.get_post_share_count(post_id)

    def get_post_reactions_breakdown(self, post_id: str) -> dict[str, Any]:
        """Return counts for all reaction types on a post."""
        raw = self.api.get_bulk_insights(post_id, list(REACTION_METRICS.values()))
        if "error" in raw:
            return raw
        results: dict[str, Any] = {}
        for item in raw.get("data", []):
            name = item.get("name")
            value = item.get("values", [{}])[0].get("value")
            results[name] = value
        return results

    def bulk_delete_comments(self, comment_ids: list[str]) -> list[dict[str, Any]]:
        """Delete multiple comments and return their results."""
        results = []
        for cid in comment_ids:
            res = self.api.delete_comment(cid)
            results.append({"comment_id": cid, "result": res})
        return results

    def bulk_hide_comments(self, comment_ids: list[str]) -> list[dict[str, Any]]:
        """Hide multiple comments and return their results."""
        results = []
        for cid in comment_ids:
            res = self.api.hide_comment(cid)
            results.append({"comment_id": cid, "result": res})
        return results

    def bulk_unhide_comments(self, comment_ids: list[str]) -> list[dict[str, Any]]:
        """Unhide multiple comments and return their results."""
        results = []
        for cid in comment_ids:
            res = self.api.unhide_comment(cid)
            results.append({"comment_id": cid, "result": res})
        return results

    def get_comment_replies(self, comment_id: str) -> dict[str, Any]:
        return self.api.get_comment_replies(comment_id)

    def get_post_permalink(self, post_id: str) -> dict[str, Any]:
        return self.api.get_post_permalink(post_id)

    def get_scheduled_posts(self) -> dict[str, Any]:
        return self.api.get_scheduled_posts()

    def get_page_info(self) -> dict[str, Any]:
        return self.api.get_page_info()
