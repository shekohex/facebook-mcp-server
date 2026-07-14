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


class EngagedUsersTests(unittest.TestCase):
    def test_returns_clear_unsupported_response_without_api_request(self) -> None:
        manager = Manager()

        with patch.object(manager.api, "get_insights") as get_insights:
            result = manager.get_post_engaged_users("page_post")

        get_insights.assert_not_called()
        self.assertEqual(result["status"], "unsupported")
        self.assertEqual(result["metric"], "post_engaged_users")
        self.assertEqual(result["post_id"], "page_post")


if __name__ == "__main__":
    unittest.main()
