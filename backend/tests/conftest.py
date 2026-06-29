import os
import pytest

@pytest.fixture(autouse=True)
def setup_test_env():
    os.environ["DEV_MODE"] = "true"
