from app.integrations.adapters import NotionConnector


def test_notion_uses_only_selected_pages_and_marks_content_untrusted():
    connector = NotionConnector(is_configured=True, selected_resources=("page-1",)); connector.set_fixture_rows([{"id":"page-1","title":"Release criteria","summary":"Authentication stable, rollback verified, deployment guide approved.","page_id":"page-1"}])
    item = connector.sync("u", None).items[0]
    assert item.metadata == {"page_id":"page-1","untrusted_content":True}
    assert connector.selected_resources == ("page-1",)
