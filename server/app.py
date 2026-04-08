import uvicorn
from main import app


def main() -> None:
    """Run the FastAPI app using Uvicorn."""
    uvicorn.run(app, host="0.0.0.0", port=8000)
