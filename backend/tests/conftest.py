import os
import pytest

os.environ["ENV"] = "test"
os.environ["DEV_MODE"] = "true"
os.environ["DEV_USER_ID"] = "00000000-0000-0000-0000-000000000001"
if os.environ.get("RUN_SUPABASE_INTEGRATION") != "1" and os.environ.get("RUN_GOOGLE_INTEGRATION") != "1":
    os.environ["SUPABASE_URL"] = ""
    os.environ["SUPABASE_ANON_KEY"] = ""
    os.environ["SUPABASE_SERVICE_ROLE_KEY"] = ""
if os.environ.get("RUN_GROQ_INTEGRATION") != "1":
    os.environ["GROQ_API_KEY"] = ""
if os.environ.get("RUN_GOOGLE_INTEGRATION") != "1":
    os.environ["GOOGLE_CLIENT_ID"] = ""
    os.environ["GOOGLE_CLIENT_SECRET"] = ""

@pytest.fixture
def anyio_backend():
    return "asyncio"

@pytest.fixture(autouse=True)
def setup_test_env():
    from app.main import app
    from app.core.container import container

    app.dependency_overrides.clear()
    container.reset_for_tests()
    yield
    app.dependency_overrides.clear()
    container.reset_for_tests()
