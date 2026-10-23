from aiohttp import web
from config.settings import PORT


async def handle_health_check(request: web.Request) -> web.Response:
    """Returns a simple OK response for Render health checks."""
    return web.Response(text="Telegram Bot is running!")


async def start_web_server() -> web.AppRunner:
    """Starts the aiohttp web server on the port provided by Render."""
    app = web.Application()
    app.router.add_get("/", handle_health_check)
    app.router.add_get("/health", handle_health_check)

    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, host="0.0.0.0", port=PORT)
    await site.start()
    print(f"[web_server] Health check server listening on port {PORT}")
    return runner
