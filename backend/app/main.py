"""Entry point for the FastAPI server. No CLI."""

import sys
from pathlib import Path

# Ensure backend root is on path when running as script
if __name__ == "__main__":
    backend_root = Path(__file__).resolve().parent.parent
    if str(backend_root) not in sys.path:
        sys.path.insert(0, str(backend_root))

from dotenv import load_dotenv

# Load .env from project root (parent of backend)
root = Path(__file__).resolve().parent.parent.parent
load_dotenv(root / ".env")

from app.api import create_app
from app.logging_config import configure_root_logging, set_log_dir
from app.settings import get_settings

if __name__ == "__main__":
    settings = get_settings()
    settings.ensure_dirs()
    set_log_dir(settings.log_path)
    configure_root_logging(settings.log_level)
    app = create_app()
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
