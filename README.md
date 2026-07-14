# Facebook MCP Server

This project is a **MCP server** for managing a Facebook Page using the Facebook Graph API. It exposes a focused set of tools for reading, publishing, moderating, and measuring Page content.

[![Trust Score](https://archestra.ai/mcp-catalog/api/badge/quality/HagaiHen/facebook-mcp-server)](https://archestra.ai/mcp-catalog/hagaihen__facebook-mcp-server)
<a href="https://glama.ai/mcp/servers/@HagaiHen/facebook-mcp-server">
  <img width="380" height="200" src="https://glama.ai/mcp/servers/@HagaiHen/facebook-mcp-server/badge" />
</a>

---

## 🤖 What Is This?

This MCP provides a suite of AI-callable tools that connect directly to a Facebook Page, abstracting common API operations as LLM-friendly functions.

### ✅ Benefits

- Empowers **social media managers** to automate moderation and analytics.
- Seamlessly integrates with **Claude Desktop or any Agent client**.
- Enables fine-grained control over Facebook content from natural language.

---

## 📦 Features

| Tool                             | Description                                                         |
|----------------------------------|---------------------------------------------------------------------|
| `get_page_posts`                 | Retrieve recent posts, optionally with attachment media metadata.   |
| `get_post_info`                  | Retrieve one post, optionally with attachment media metadata.       |
| `get_post_comments`              | Fetch comments on a given post.                                     |
| `delete_post`                    | Delete a specific post by ID.                                       |
| `delete_comment`                 | Delete a specific comment by ID.                                    |
| `get_number_of_comments`         | Count all comments and replies on a post.                           |
| `get_post_clicks`                | Get number of clicks on the post.                                   |
| `get_post_media_views`           | Get total media views for a post.                                   |
| `get_post_unique_media_viewers`  | Get unique media viewers for a post.                                |
| `get_post_metrics`               | Get reactions, comments, shares, clicks, views, and unique viewers. |
| `post_image_to_facebook`         | Post an image with a caption to the Facebook page.                  |
| `update_post`                    | Updates an existing post's message.                                 |
| `schedule_post`                  | Schedule a post for future publication.                             |
| `get_post_share_count`           | Get the number of shares on a post.                                 |
| `get_post_reactions_breakdown`   | Get all reaction counts for a post in one call.                     |
| `get_comment_replies`            | Get all replies to a specific comment.                              |
| `get_post_permalink`             | Get the permalink URL of a post.                                    |
| `get_scheduled_posts`            | List all scheduled unpublished posts on the Page.                   |
| `get_page_info`                  | Get extended Page details.                                          |

`get_post_metrics` reports interaction counts and media audience metrics separately. Unique media viewers are not equivalent to the deprecated unique engaged-users metric.

---

## Reliability & Account Safety

- Requests send the Page access token in the `Authorization` header, never in the URL.
- Graph API usage headers trigger proactive cooldowns near Meta's limits.
- Throttled and transient requests retry with capped backoff and honor Meta's reported regain time.

---

## 🚀 Setup & Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/facebook-mcp-server.git
cd facebook-mcp-server
```

### 2. 🛠️ Installation

Install dependencies using uv, a fast Python package manager:
If uv is not already installed, run:
```bash
curl -Ls https://astral.sh/uv/install.sh | bash
```

Once uv is installed, install the locked project dependencies:
```bash
uv sync --locked
```

### 3. Set Up Environment

Create a .env file in the root directory and add your Facebook Page credentials. 
You can obtain these from  https://developers.facebook.com/tools/explorer

```bash
FACEBOOK_ACCESS_TOKEN=your_facebook_page_access_token
FACEBOOK_PAGE_ID=your_page_id
```

## Running the Server

The server uses MCP Streamable HTTP and listens on `http://127.0.0.1:8000/mcp` by default.

```bash
uv run python server.py
```

To accept connections from another machine, bind to all interfaces and explicitly allow the hostname or IP clients use:

```bash
MCP_HOST=0.0.0.0 \
MCP_PORT=8000 \
MCP_ALLOWED_HOSTS='facebook-mcp.example.com:*,192.168.1.20:*' \
uv run python server.py
```

Connect MCP clients to `http://facebook-mcp.example.com:8000/mcp`.

`MCP_ALLOWED_HOSTS` is a comma-separated Host-header allowlist. Keep this server behind a firewall, VPN, or authenticated reverse proxy because exposed tools can update and delete Page content.

## Docker Compose

Create local configuration from the provided example:

```bash
cp .env.example .env
```

Set `FACEBOOK_ACCESS_TOKEN`, `FACEBOOK_PAGE_ID`, and `MCP_ALLOWED_HOSTS` in `.env`, then build and start:

```bash
docker compose up --build -d
```

The MCP endpoint is available at `http://localhost:8000/mcp` by default.

Useful commands:

```bash
docker compose logs -f facebook-mcp
docker compose ps
docker compose down
```

The image uses an official `uv` Alpine builder and a separate non-root Python Alpine runtime. Compose runs it with a read-only filesystem, no Linux capabilities, and `no-new-privileges`.

---

## ✅ You’re Ready to Go!

That’s it — your Facebook MCP server is now fully configured and ready to power Claude Desktop. You can now post, moderate, and measure engagement all through natural language prompts!

---

## 🤝 Contributing

Contributions, issues, and feature requests are welcome!  
Feel free to fork the repo and submit a pull request.

- Create a branch: `git checkout -b feature/YourFeature`
- Commit your changes: `git commit -m 'feat: add new feature'`
- Push to the branch: `git push origin feature/YourFeature`
- Open a pull request 🎉
