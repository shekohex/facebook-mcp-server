import unittest
from unittest.mock import patch

from facebook_api import FacebookAPI
from manager import Manager


class PostAttachmentTests(unittest.TestCase):
    def test_get_post_info_fetches_attachments_from_edge(self) -> None:
        api = FacebookAPI()
        post = {"id": "page_post", "message": "hello"}
        attachments = {"data": [{"media_type": "photo"}]}

        with patch.object(api, "_request", side_effect=[post, attachments]) as request:
            result = api.get_post_info("page_post", include_attachments=True)

        self.assertEqual(result["attachments"], attachments)
        post_request, attachment_request = request.call_args_list
        self.assertEqual(post_request.args[1], "page_post")
        self.assertNotIn("attachments", post_request.args[2]["fields"])
        self.assertNotIn("full_picture", post_request.args[2]["fields"])
        self.assertNotIn("source", post_request.args[2]["fields"])
        self.assertEqual(attachment_request.args[1], "page_post/attachments")
        self.assertIn("media", attachment_request.args[2]["fields"])
        self.assertIn("subattachments.limit(25)", attachment_request.args[2]["fields"])

    def test_get_posts_fetches_attachments_for_each_post(self) -> None:
        api = FacebookAPI()
        posts = {"data": [{"id": "post_1"}, {"id": "post_2"}]}

        with patch.object(
            api,
            "_request",
            side_effect=[posts, {"data": [{"type": "photo"}]}, {"data": [{"type": "video"}]}],
        ):
            result = api.get_posts(include_attachments=True)

        self.assertEqual(result["data"][0]["attachments"]["data"][0]["type"], "photo")
        self.assertEqual(result["data"][1]["attachments"]["data"][0]["type"], "video")

    def test_get_post_info_preserves_post_when_attachment_edge_fails(self) -> None:
        api = FacebookAPI()
        post = {"id": "page_post", "message": "hello"}
        attachment_error = {"error": {"code": 100, "message": "unsupported attachment field"}}

        with patch.object(api, "_request", side_effect=[post, attachment_error]):
            result = api.get_post_info("page_post", include_attachments=True)

        self.assertEqual(result["id"], "page_post")
        self.assertEqual(result["message"], "hello")
        self.assertEqual(result["attachments"], attachment_error)


class PostMetricsTests(unittest.TestCase):
    def test_comment_count_uses_summary_including_replies(self) -> None:
        api = FacebookAPI()

        with patch.object(api, "_request", return_value={"summary": {"total_count": 42}}) as request:
            result = api.get_comment_count("page_post")

        self.assertEqual(result, 42)
        self.assertEqual(
            request.call_args.args,
            ("GET", "page_post/comments", {"limit": 0, "summary": "true", "filter": "stream"}),
        )

    def test_combines_post_metrics(self) -> None:
        manager = Manager()
        reactions = {
            "data": [
                {"name": "post_reactions_like_total", "values": [{"value": 1}]},
                {"name": "post_reactions_love_total", "values": [{"value": 2}]},
            ]
        }
        clicks = {"data": [{"name": "post_clicks", "values": [{"value": 3}]}]}
        views = {"data": [{"name": "post_media_view", "values": [{"value": 20}]}]}
        viewers = {"data": [{"name": "post_total_media_view_unique", "values": [{"value": 15}]}]}

        with (
            patch.object(manager.api, "get_bulk_insights", return_value=reactions),
            patch.object(manager, "get_post_clicks", return_value=clicks),
            patch.object(manager, "get_post_media_views", return_value=views),
            patch.object(manager, "get_post_unique_media_viewers", return_value=viewers),
            patch.object(manager, "get_number_of_comments", return_value=4),
            patch.object(manager, "get_post_share_count", return_value=5),
        ):
            result = manager.get_post_metrics("page_post")

        self.assertEqual(result["reactions"]["total"], 3)
        self.assertEqual(result["comments"], 4)
        self.assertEqual(result["shares"], 5)
        self.assertEqual(result["clicks"], 3)
        self.assertEqual(result["media_views"], 20)
        self.assertEqual(result["unique_media_viewers"], 15)
        self.assertNotIn("errors", result)

    def test_preserves_partial_metrics_when_insight_fails(self) -> None:
        manager = Manager()
        error = {"code": 100, "message": "invalid metric"}

        with (
            patch.object(manager.api, "get_bulk_insights", return_value={"data": []}),
            patch.object(manager, "get_post_clicks", return_value={"data": []}),
            patch.object(manager, "get_post_media_views", return_value={"error": error}),
            patch.object(manager, "get_post_unique_media_viewers", return_value={"data": []}),
            patch.object(manager, "get_number_of_comments", return_value=4),
            patch.object(manager, "get_post_share_count", return_value=5),
        ):
            result = manager.get_post_metrics("page_post")

        self.assertIsNone(result["media_views"])
        self.assertEqual(result["errors"]["media_views"], error)
        self.assertEqual(result["comments"], 4)

    def test_reaction_failure_does_not_report_false_zero_counts(self) -> None:
        manager = Manager()
        error = {"code": 100, "message": "invalid reaction metric"}

        with (
            patch.object(manager.api, "get_bulk_insights", return_value={"error": error}),
            patch.object(manager, "get_post_clicks", return_value={"data": []}),
            patch.object(manager, "get_post_media_views", return_value={"data": []}),
            patch.object(manager, "get_post_unique_media_viewers", return_value={"data": []}),
            patch.object(manager, "get_number_of_comments", return_value=0),
            patch.object(manager, "get_post_share_count", return_value=0),
        ):
            result = manager.get_post_metrics("page_post")

        self.assertIsNone(result["reactions"])
        self.assertEqual(result["errors"]["reactions"], error)


if __name__ == "__main__":
    unittest.main()
