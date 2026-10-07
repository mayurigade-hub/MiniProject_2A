"""Compatibility entry point for local runs and existing integrations."""

from backend.main import app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("backend.main:app", host="0.0.0.0", port=8000)
