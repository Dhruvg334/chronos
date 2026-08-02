import os

import pytest


@pytest.mark.integration
def test_integration_configuration_is_explicit():
    if not os.environ.get("SUPABASE_URL"):
        pytest.skip("SUPABASE_URL is not configured; integration suite is opt-in.")
    assert os.environ.get("SUPABASE_SERVICE_ROLE_KEY"), "SUPABASE_SERVICE_ROLE_KEY is required for integration tests."
