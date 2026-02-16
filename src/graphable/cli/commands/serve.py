from asyncio import get_event_loop
from logging import getLogger
from pathlib import Path

from starlette.applications import Starlette
from starlette.responses import HTMLResponse
from starlette.routing import Route, WebSocketRoute
from starlette.websockets import WebSocket
from uvicorn import Config
from uvicorn import Server as UvicornServer
from watchfiles import awatch

from ...views.html import create_topology_html
from .core import load_graph

logger = getLogger(__name__)


class Server:
    def __init__(self, path: Path, tag: str | None = None):
        self.path = path
        self.tag = tag
        self.connections: set[WebSocket] = set()
        self.app = Starlette(
            routes=[
                Route("/", self.index),
                WebSocketRoute("/ws", self.websocket_endpoint),
            ]
        )

    async def index(self, request):
        try:
            g = load_graph(self.path, tag=self.tag)
            html = create_topology_html(g)
            return HTMLResponse(html)
        except Exception as e:
            return HTMLResponse(
                f"<h1>Error loading graph</h1><pre>{e}</pre>", status_code=500
            )

    async def websocket_endpoint(self, websocket: WebSocket):
        await websocket.accept()
        self.connections.add(websocket)
        try:
            while True:
                await websocket.receive_text()
        except Exception:
            self.connections.remove(websocket)

    async def watch_file(self):
        async for changes in awatch(self.path):
            logger.info(f"File {self.path} changed, reloading...")
            for ws in self.connections:
                await ws.send_text("reload")


def serve_command(path: Path, port: int = 8000, tag: str | None = None):
    server = Server(path, tag=tag)

    config = Config(server.app, host="127.0.0.1", port=port, log_level="info")
    uv_server = UvicornServer(config)

    loop = get_event_loop()
    loop.create_task(server.watch_file())
    loop.run_until_complete(uv_server.serve())
