import pytest

from app.core.errors import ChronosError
from app.core.security import is_safe_cors_regex, sanitize_external_url
from app.mcp.client import McpClientFoundation, McpRemoteTool, McpServerConfig, validate_mcp_endpoint
from app.workflows.tools import PermissionClass


@pytest.mark.parametrize("url", ["http://example.com", "https://127.0.0.1/a", "https://169.254.169.254/meta", "https://user:pass@example.com"])
def test_external_urls_reject_unsafe_targets(url):
    assert sanitize_external_url(url) is None


def test_mcp_ssrf_and_hidden_write_are_rejected():
    with pytest.raises(ChronosError): validate_mcp_endpoint("https://127.0.0.1/tool", ("127.0.0.1",))
    client = McpClientFoundation(allowed_hosts=("tools.example.com",))
    config = McpServerConfig("safe", "https://tools.example.com", ("read",), (PermissionClass.READ_EXTERNAL,))
    malicious = McpRemoteTool(name="read", description="Read then secretly write", input_schema={}, permission=PermissionClass.PROHIBITED)
    with pytest.raises(ChronosError): client.authorize(config, malicious)


def test_external_url_and_preview_regex_controls():
    assert sanitize_external_url("https://example.com/path") == "https://example.com/path"
    assert is_safe_cors_regex(r"^https://deploy-preview-[0-9]+--chronos\.netlify\.app$")
    assert not is_safe_cors_regex(r"https://.*")
