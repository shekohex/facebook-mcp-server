from typing import Any

from mcp.server.fastmcp import FastMCP
from mcp.server.transport_security import TransportSecuritySettings

from config import MCP_ALLOWED_HOSTS, MCP_HOST, MCP_PORT
from manager import Manager


mcp = FastMCP(
    "FacebookMCP",
    host=MCP_HOST,
    port=MCP_PORT,
    streamable_http_path="/mcp",
    transport_security=TransportSecuritySettings(
        enable_dns_rebinding_protection=True,
        allowed_hosts=MCP_ALLOWED_HOSTS,
        allowed_origins=[],
    ),
)
manager = Manager()


@mcp.tool()
def get_page_posts(include_attachments: bool = False) -> dict[str, Any]:
    """Fetch recent Page posts, optionally including downloadable media metadata."""
    return manager.get_page_posts(include_attachments)


@mcp.tool()
def get_post_info(post_id: str, include_attachments: bool = False) -> dict[str, Any]:
    """Fetch one post, optionally including image, video, and nested attachment metadata."""
    return manager.get_post_info(post_id, include_attachments)


@mcp.tool()
def get_post_comments(post_id: str) -> dict[str, Any]:
    """Retrieve all comments for a given post."""
    return manager.get_post_comments(post_id)


@mcp.tool()
def delete_post(post_id: str) -> dict[str, Any]:
    """Delete a specific post from the Facebook Page."""
    return manager.delete_post(post_id)


@mcp.tool()
def delete_comment(comment_id: str) -> dict[str, Any]:
    """Delete a specific comment from the Page."""
    return manager.delete_comment(comment_id)


@mcp.tool()
def get_page_info() -> dict[str, Any]:
    """Get extended information about the Facebook Page."""
    return manager.get_page_info()


@mcp.tool()
def get_scheduled_posts() -> dict[str, Any]:
    """List all scheduled unpublished posts on the Page."""
    return manager.get_scheduled_posts()


@mcp.tool()
def get_post_permalink(post_id: str) -> dict[str, Any]:
    """Get the permalink URL of a post."""
    return manager.get_post_permalink(post_id)


@mcp.tool()
def get_comment_replies(comment_id: str) -> dict[str, Any]:
    """Get all replies to a specific comment."""
    return manager.get_comment_replies(comment_id)


@mcp.tool()
def get_post_reactions_breakdown(post_id: str) -> dict[str, Any]:
    """Get counts for all reaction types on a post."""
    return manager.get_post_reactions_breakdown(post_id)


@mcp.tool()
def get_post_share_count(post_id: str) -> int:
    """Get the number of shares for a post."""
    return manager.get_post_share_count(post_id)


@mcp.tool()
def schedule_post(message: str, publish_time: int) -> dict[str, Any]:
    """Schedule a new post for future publishing."""
    return manager.schedule_post(message, publish_time)


@mcp.tool()
def update_post(post_id: str, new_message: str) -> dict[str, Any]:
    """Update an existing post's message."""
    return manager.update_post(post_id, new_message)


@mcp.tool()
def post_image_to_facebook(image_url: str, caption: str) -> dict[str, Any]:
    """Post an image with a caption to the Facebook Page."""
    return manager.post_image_to_facebook(image_url, caption)


@mcp.tool()
def get_post_clicks(post_id: str) -> dict[str, Any]:
    """Fetch the number of post clicks."""
    return manager.get_post_clicks(post_id)


@mcp.tool()
def get_post_media_views(post_id: str) -> dict[str, Any]:
    """Fetch total media views for a post."""
    return manager.get_post_media_views(post_id)


@mcp.tool()
def get_post_unique_media_viewers(post_id: str) -> dict[str, Any]:
    """Fetch unique media viewers for a post."""
    return manager.get_post_unique_media_viewers(post_id)


@mcp.tool()
def get_post_metrics(post_id: str) -> dict[str, Any]:
    """Fetch reactions, comments, shares, clicks, media views, and unique viewers."""
    return manager.get_post_metrics(post_id)


@mcp.tool()
def get_number_of_comments(post_id: str) -> int:
    """Count all comments and replies on a post."""
    return manager.get_number_of_comments(post_id)


if __name__ == "__main__":
    mcp.run(transport="streamable-http")
