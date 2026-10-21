import os

from fastapi import APIRouter, Response
from fastapi.responses import HTMLResponse

from src.core.config import settings

router = APIRouter(tags=["app"])

ANTI_CACHE_HEADERS = {
    "Cache-Control": "no-cache, no-store, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
}


def apply_anti_cache_headers(response: Response) -> None:
    """Applies strict anti-cache headers to prevent TMA white-screen/stale cache bugs."""
    for header, value in ANTI_CACHE_HEADERS.items():
        response.headers[header] = value


INDEX_HTML_PATH = os.path.join("frontend", "dist", "index.html")


@router.get("/", response_class=HTMLResponse)
@router.get("/app", response_class=HTMLResponse)
async def serve_mini_app(response: Response) -> HTMLResponse:
    """Serves the Telegram Mini App shell with anti-cache headers and static versioning."""
    apply_anti_cache_headers(response)

    if os.path.exists(INDEX_HTML_PATH):
        with open(INDEX_HTML_PATH, "r", encoding="utf-8") as f:
            content = f.read()
        return HTMLResponse(content=content, headers=ANTI_CACHE_HEADERS)

    version = settings.APP_VERSION
    html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
    <meta http-equiv="Cache-Control" content="no-cache, no-store, must-revalidate">
    <meta http-equiv="Pragma" content="no-cache">
    <meta http-equiv="Expires" content="0">
    <title>Client Portal &amp; Milestone Desk</title>
    <script src="https://telegram.org/js/telegram-web-app.js?v={version}"></script>
    <link rel="stylesheet" href="/static/css/app.css?v={version}">
</head>
<body>
    <div id="root">
        <div style="font-family: sans-serif; padding: 24px; text-align: center;">
            <h2>Client Portal &amp; Milestone Desk</h2>
            <p>Version: <strong>{version}</strong></p>
            <p>Backend &amp; Database Initialized. Telegram Mini App shell ready.</p>
        </div>
    </div>
    <script src="/static/js/app.js?v={version}"></script>
</body>
</html>
"""
    return HTMLResponse(content=html_content, headers=ANTI_CACHE_HEADERS)


@router.get("/api/health")
async def health_check(response: Response) -> dict[str, str]:
    """Health check endpoint confirming API status and active version."""
    apply_anti_cache_headers(response)
    return {
        "status": "ok",
        "app_version": settings.APP_VERSION,
    }


@router.get("/api/config")
async def app_config(response: Response) -> dict[str, str | bool]:
    """Provides public configuration to TMA client."""
    apply_anti_cache_headers(response)
    return {
        "app_version": settings.APP_VERSION,
        "debug": settings.DEBUG,
    }
