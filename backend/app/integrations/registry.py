from __future__ import annotations

from app.core.config import Settings
from app.integrations.adapters import GmailConnector, GitHubConnector, GoogleCalendarConnector, MicrosoftPlannerConnector, NotionConnector, OutlookCalendarConnector
from app.integrations.contracts import ExternalConnector


class ConnectorRegistry:
    def __init__(self, connectors: list[ExternalConnector] | None = None) -> None:
        self._connectors = {connector.provider: connector for connector in connectors or []}

    def get(self, provider: str) -> ExternalConnector:
        if provider not in self._connectors: raise ValueError("Integration provider is unavailable.")
        return self._connectors[provider]

    def all(self) -> tuple[ExternalConnector, ...]:
        return tuple(self._connectors.values())


def build_connector_registry(settings: Settings, *, google_auth_url=None, google_revoke=None, google_credentials=None) -> ConnectorRegistry:
    google_configured = bool(settings.GOOGLE_CLIENT_ID and settings.GOOGLE_CLIENT_SECRET)
    microsoft_configured = bool(settings.MICROSOFT_CLIENT_ID and settings.MICROSOFT_CLIENT_SECRET)
    return ConnectorRegistry([
        GoogleCalendarConnector(is_configured=google_configured, auth_url=google_auth_url, revoke=google_revoke, credential_loader=google_credentials),
        GmailConnector(is_configured=bool(settings.GMAIL_CLIENT_ID and settings.GMAIL_CLIENT_SECRET)),
        GitHubConnector(is_configured=bool(settings.GITHUB_CLIENT_ID and settings.GITHUB_CLIENT_SECRET)),
        NotionConnector(is_configured=bool(settings.NOTION_CLIENT_ID and settings.NOTION_CLIENT_SECRET)),
        OutlookCalendarConnector(is_configured=microsoft_configured),
        MicrosoftPlannerConnector(is_configured=microsoft_configured),
    ])
