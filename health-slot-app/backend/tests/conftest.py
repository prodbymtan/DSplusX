import os
import sys
import tempfile
from pathlib import Path

# Fast timers and a throwaway database, set BEFORE the app is imported.
_tmp = Path(tempfile.mkdtemp())
# Override with e.g. TEST_DATABASE_URL=postgresql+psycopg://postgres@127.0.0.1:5432/health_test
os.environ["DATABASE_URL"] = os.environ.get("TEST_DATABASE_URL", f"sqlite:///{_tmp / 'test.db'}")
os.environ["OFFER_WINDOW_SECONDS"] = "1"
os.environ["RIPPLE_ROUNDS"] = "1"

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.main import app  # noqa: E402


@pytest.fixture()
def client():
    with TestClient(app) as c:
        c.post("/api/demo/reset")
        yield c
