import os
from dotenv import load_dotenv

load_dotenv()

# Facebook Graph API setup
GRAPH_API_VERSION = "v22.0"
PAGE_ACCESS_TOKEN = os.getenv("FACEBOOK_ACCESS_TOKEN")
PAGE_ID = os.getenv("FACEBOOK_PAGE_ID")
GRAPH_API_BASE_URL = f"https://graph.facebook.com/{GRAPH_API_VERSION}"

MCP_HOST = os.getenv("MCP_HOST", "127.0.0.1")
MCP_PORT = int(os.getenv("MCP_PORT", "8000"))
MCP_ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv(
        "MCP_ALLOWED_HOSTS",
        "127.0.0.1:*,localhost:*,[::1]:*",
    ).split(",")
    if host.strip()
]
