from __future__ import annotations
from fastapi import FastAPI
import uvicorn
import gradio as gr
from app.core.config import get_settings
from app.bootstrap.container import get_container
from app.storage.db import init_db
from app.api.routes import router
from app.ui.gradio_app import build_ui


def startup():
    init_db()


def create_app() -> FastAPI:
    app = FastAPI(title="MeetLens API", version="0.1.0")
    app.include_router(router, prefix="/api")
    app.add_api_route("/health", lambda: {"ok": True, "app": get_settings().app_name}, methods=["GET"])
    async def readiness():
        llm = await get_container().llm.health()
        return {"ok": True, "app": get_settings().app_name, "degraded": not bool(llm.get("available")), "llm": llm}

    app.add_api_route("/ready", readiness, methods=["GET"])
    app.add_event_handler("startup", startup)
    demo = build_ui()
    return gr.mount_gradio_app(app, demo, path="/")


app = create_app()

if __name__ == "__main__":
    s = get_settings()
    uvicorn.run("app.main:app", host=s.host, port=s.port, reload=False)
