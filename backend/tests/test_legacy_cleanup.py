from app.main import app


def test_obsolete_routes_are_not_mounted():
    paths = set()
    for route in app.routes:
        if hasattr(route, "path"):
            paths.add(route.path)
        elif hasattr(route, "original_router"):
            prefix = route.include_context.prefix
            paths.update(prefix + child.path for child in route.original_router.routes if hasattr(child, "path"))
    assert not any(path.startswith(("/api/v1/command", "/api/v1/scheduling", "/api/v1/drift", "/api/v1/agent", "/api/v1/demo")) for path in paths)
    assert "/api/v1/today" in paths
    assert "/api/v1/operations/data/export" in paths
    assert "/api/v1/workflows/{run_id}/trace" in paths
