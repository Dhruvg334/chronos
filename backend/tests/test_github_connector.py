from app.integrations.adapters import GitHubConnector


def test_github_only_normalizes_selected_repository_context():
    connector = GitHubConnector(is_configured=True, selected_resources=("chronos",)); connector.set_fixture_rows([{"id":"issue-7","title":"Fix refresh-token race","summary":"PR #9 is blocked by this issue","repository":"chronos","number":7,"milestone":"Friday","dependencies":["pr-9"]}])
    page = connector.sync("u", None)
    assert page.items[0].metadata["repository"] == "chronos"
    assert page.items[0].metadata["dependencies"] == ["pr-9"]
    assert all("write" not in scope for scope in connector.required_scopes)
