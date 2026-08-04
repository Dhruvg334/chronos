import pytest
from app.core.errors import ChronosError
from app.mcp.client import McpClientFoundation, McpRemoteTool, McpServerConfig, validate_mcp_endpoint
from app.workflows.tools import PermissionClass


def config(): return McpServerConfig("safe","https://mcp.example.com",("read_project","propose_plan"),(PermissionClass.READ_EXTERNAL,PermissionClass.PROPOSE_INTERNAL_WRITE))


def test_mcp_read_allowed_proposal_pending_and_undeclared_write_rejected():
    client = McpClientFoundation(allowed_hosts=("mcp.example.com",))
    read = McpRemoteTool(name="read_project",description="read",input_schema={"type":"object"},permission=PermissionClass.READ_EXTERNAL)
    proposal = McpRemoteTool(name="propose_plan",description="propose",input_schema={"type":"object"},permission=PermissionClass.PROPOSE_INTERNAL_WRITE)
    write = McpRemoteTool(name="delete_repo",description="write",input_schema={"type":"object"},permission=PermissionClass.APPROVED_EXTERNAL_WRITE)
    assert client.authorize(config(), read) == "allowed"
    assert client.authorize(config(), proposal) == "pending_approval"
    with pytest.raises(ChronosError): client.authorize(config(), write)


@pytest.mark.parametrize("url", ["http://mcp.example.com", "https://127.0.0.1", "https://user:pass@mcp.example.com", "https://not-allowed.example"])
def test_mcp_endpoint_ssrf_controls(url):
    with pytest.raises(ChronosError): validate_mcp_endpoint(url, ("mcp.example.com",))
