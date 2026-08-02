import os
import pytest

os.environ["ENV"] = "test"
os.environ["DEV_MODE"] = "true"
os.environ["DEV_USER_ID"] = "00000000-0000-0000-0000-000000000001"
os.environ["SUPABASE_URL"] = ""
os.environ["SUPABASE_ANON_KEY"] = ""
os.environ["SUPABASE_SERVICE_ROLE_KEY"] = ""
os.environ["GROQ_API_KEY"] = ""
os.environ["GOOGLE_CLIENT_ID"] = ""
os.environ["GOOGLE_CLIENT_SECRET"] = ""

@pytest.fixture(autouse=True)
def setup_test_env():
    from app.main import app
    from app.core.container import container

    app.dependency_overrides.clear()
    container.reset_for_tests()
    yield
    app.dependency_overrides.clear()
    container.reset_for_tests()
