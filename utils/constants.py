"""
Constants for pytest framework.
Only essential paths - AI agents handle everything else.
"""

import os

# Storage paths
STORAGE_PATH = "storage_state.json"
SESSION_EXPIRY_SECONDS = 3600  # 1 hour

# Directories (auto-created by pytest)
SCREENSHOTS_DIR = "screenshots"
REPORTS_DIR = "reports"
DOWNLOADS_DIR = "downloads"
VIDEOS_DIR = "videos"

# MCP Server
MCP_SERVER_URL = "http://localhost:8080"

# Create directories if needed
for directory in [SCREENSHOTS_DIR, REPORTS_DIR, DOWNLOADS_DIR, VIDEOS_DIR]:
    os.makedirs(directory, exist_ok=True)
