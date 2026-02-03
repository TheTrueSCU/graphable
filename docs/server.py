from pathlib import Path

from starlette.applications import Starlette
from starlette.staticfiles import StaticFiles

# Path to the built documentation
build_dir = Path(__file__).parent / "_build" / "html"

app = Starlette()
if build_dir.exists():
    app.mount("/", StaticFiles(directory=str(build_dir), html=True), name="static")
else:
    # Fallback if docs aren't built yet
    from starlette.responses import HTMLResponse

    @app.route("/")
    async def homepage(request):
        return HTMLResponse("<h1>Documentation not found. Run 'just docs' first.</h1>")
