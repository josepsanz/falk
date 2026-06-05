"""FastAPI application factory and launcher.

In production the built React SPA is served from ``static/`` next to this
module; in development the Vite dev server proxies ``/api`` here, so the mount
is skipped when no build is present.
"""

import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .routers import meters, plugs

_STATIC_DIR = Path(__file__).parent / "static"
_DEV_ENV = "FALK_DEV"


def create_app() -> FastAPI:
    """Build the FastAPI application with API routers and the SPA mount."""
    app = FastAPI(title="Falk", description="Home electricity monitoring")

    if os.environ.get(_DEV_ENV):
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_methods=["*"],
            allow_headers=["*"],
        )

    app.include_router(meters.router, prefix="/api")
    app.include_router(plugs.router, prefix="/api")

    if _STATIC_DIR.is_dir():
        _mount_spa(app)

    return app


def _mount_spa(app: FastAPI) -> None:
    """Serve the built SPA, falling deep links back to index.html.

    Hashed asset files are served from disk; any other unmatched path returns
    index.html so client-side routing (BrowserRouter) works on refresh.
    """
    index_file = _STATIC_DIR / "index.html"
    app.mount(
        "/assets",
        StaticFiles(directory=_STATIC_DIR / "assets"),
        name="assets",
    )

    @app.get("/{full_path:path}", include_in_schema=False)
    def spa_fallback(full_path: str) -> FileResponse:
        # Unknown API paths must 404 as JSON, not fall back to the SPA shell.
        if full_path.startswith("api/"):
            raise HTTPException(status_code=404, detail="not found")
        candidate = _STATIC_DIR / full_path
        if full_path and candidate.is_file():
            return FileResponse(candidate)
        if not index_file.is_file():
            raise HTTPException(status_code=404, detail="SPA not built")
        return FileResponse(index_file)


app = create_app()


def run() -> None:
    """Console-script entry point: launch uvicorn."""
    import uvicorn

    host = os.environ.get("FALK_API_HOST", "127.0.0.1")
    port = int(os.environ.get("FALK_API_PORT", "8000"))
    uvicorn.run(app, host=host, port=port)
