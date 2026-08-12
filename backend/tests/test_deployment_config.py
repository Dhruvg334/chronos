from pathlib import Path
import os
import tomllib

from fastapi.testclient import TestClient

from app.core.config import Settings
from app.main import app


ROOT = Path(__file__).resolve().parents[2]


def test_netlify_monorepo_build_and_spa_fallback():
    config = tomllib.loads((ROOT / "netlify.toml").read_text(encoding="utf-8"))
    assert {key: config["build"][key] for key in ("base", "command", "publish")} == {
        "base": "frontend", "command": "npm run build", "publish": "dist"
    }
    assert config["build"]["environment"]["NODE_VERSION"] == "22.12.0"
    assert Path(config["build"]["base"]) / config["build"]["publish"] == Path("frontend/dist")
    assert config["redirects"] == [{"from": "/*", "to": "/index.html", "status": 200}]


def test_production_cors_is_environment_configurable():
    configured = Settings(
        _env_file=None,
        BACKEND_CORS_ORIGINS=["http://localhost:5173", "https://chronos-example.netlify.app"],
        BACKEND_CORS_ORIGIN_REGEX=r"^https://deploy-preview-[0-9]+--chronos-example\.netlify\.app$",
    )
    assert configured.BACKEND_CORS_ORIGINS[-1] == "https://chronos-example.netlify.app"
    assert configured.BACKEND_CORS_ORIGIN_REGEX.startswith("^https://deploy-preview-")


def test_backend_start_command_and_dependency_free_liveness():
    command = (ROOT / "backend" / "Procfile").read_text(encoding="utf-8").strip()
    assert command == "web: uvicorn app.main:app --host 0.0.0.0 --port $PORT"
    response = TestClient(app).get("/api/v1/health/live")
    assert response.status_code == 200
    assert response.json() == {"status": "alive"}


def test_adaptive_plan_hardening_is_forward_only_and_restricts_execution():
    migration = (ROOT / "supabase" / "migrations" / "023_harden_adaptive_plan_approval_rpc.sql").read_text(encoding="utf-8")
    normalized = " ".join(migration.split())
    assert "SET search_path = pg_catalog" in migration
    assert "pg_catalog, public" not in migration
    assert "public.agent_proposed_actions" in migration and "auth.uid()" in migration and "auth.role()" in migration
    assert "REVOKE ALL ON FUNCTION public.approve_adaptive_plan_transaction" in normalized
    assert "FROM PUBLIC, anon" in normalized
    assert "TO authenticated, service_role" in normalized

def test_render_hostname_can_be_trusted(monkeypatch):
    monkeypatch.setenv("RENDER_EXTERNAL_HOSTNAME", "chronos-test.onrender.com")

    configured = ["localhost", "127.0.0.1"]
    render_hostname = os.getenv("RENDER_EXTERNAL_HOSTNAME", "").strip()

    allowed_hosts = list(configured)
    if render_hostname and render_hostname not in allowed_hosts:
        allowed_hosts.append(render_hostname)

    assert "chronos-test.onrender.com" in allowed_hosts