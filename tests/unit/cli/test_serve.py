from asyncio import TimeoutError, wait_for
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

from pytest import mark
from starlette.responses import HTMLResponse

from graphable.cli.commands.serve import Server, serve_command


class TestServer:
    def test_init(self):
        path = Path("test.json")
        server = Server(path, tag="v1")
        assert server.path == path
        assert server.tag == "v1"
        assert len(server.connections) == 0
        assert len(server.app.routes) == 2

    @mark.anyio
    @patch("graphable.cli.commands.serve.load_graph")
    @patch("graphable.cli.commands.serve.create_topology_html")
    async def test_index_success(self, mock_html, mock_load):
        mock_load.return_value = MagicMock()
        mock_html.return_value = "<html></html>"

        server = Server(Path("test.json"))
        request = MagicMock()
        response = await server.index(request)

        assert isinstance(response, HTMLResponse)
        assert response.body == b"<html></html>"
        assert response.status_code == 200

    @mark.anyio
    @patch("graphable.cli.commands.serve.load_graph")
    async def test_index_error(self, mock_load):
        mock_load.side_effect = Exception("Load error")

        server = Server(Path("test.json"))
        request = MagicMock()
        response = await server.index(request)

        assert isinstance(response, HTMLResponse)
        assert b"Error loading graph" in response.body
        assert b"Load error" in response.body
        assert response.status_code == 500

    @mark.anyio
    async def test_websocket_endpoint(self):
        server = Server(Path("test.json"))
        websocket = AsyncMock()

        # Simulate a single receive then disconnect
        websocket.receive_text.side_effect = ["ping", Exception("Disconnect")]

        await server.websocket_endpoint(websocket)

        websocket.accept.assert_called_once()
        assert websocket not in server.connections

    @mark.anyio
    @patch("graphable.cli.commands.serve.awatch")
    async def test_watch_file(self, mock_awatch):
        # Mock awatch to yield once then stop
        mock_changes = AsyncMock()
        mock_changes.__aiter__.return_value = [[(1, "test.json")]]
        mock_awatch.return_value = mock_changes

        server = Server(Path("test.json"))
        ws = AsyncMock()
        server.connections.add(ws)

        # Run watch_file in a way we can stop it
        try:
            await wait_for(server.watch_file(), timeout=0.1)
        except (
            TimeoutError,
            TypeError,
        ):  # TypeError might happen due to mock yielding
            pass

        ws.send_text.assert_called_with("reload")


@patch("graphable.cli.commands.serve.UvicornServer")
@patch("graphable.cli.commands.serve.Config")
@patch("graphable.cli.commands.serve.get_event_loop")
def test_serve_command(mock_loop, mock_config, mock_uv_server):
    mock_loop_instance = MagicMock()
    mock_loop.return_value = mock_loop_instance

    serve_command(Path("test.json"), port=1234, tag="v2")

    mock_config.assert_called_once()
    args, kwargs = mock_config.call_args
    assert kwargs["port"] == 1234

    assert mock_loop_instance.create_task.called
    assert mock_loop_instance.run_until_complete.called
