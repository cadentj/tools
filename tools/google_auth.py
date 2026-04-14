"""Google OAuth credentials: shared by all Google API tool modules."""

from __future__ import annotations

import os

from google.auth.exceptions import RefreshError
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = [
    "https://www.googleapis.com/auth/documents",
    "https://www.googleapis.com/auth/tasks",
    "https://www.googleapis.com/auth/calendar.readonly",
]


def get_credentials() -> Credentials:
    """Return valid OAuth credentials, refreshing or re-authing as needed.

    Reads GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET, and GOOGLE_REFRESH_TOKEN
    from the environment. On a successful browser flow the new refresh token
    is saved to token.json in the repo root.
    """
    client_id = os.environ.get("GOOGLE_CLIENT_ID", "")
    client_secret = os.environ.get("GOOGLE_CLIENT_SECRET", "")
    refresh_token = os.environ.get("GOOGLE_REFRESH_TOKEN", "")

    if not all([client_id, client_secret]):
        raise RuntimeError(
            "GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set in the environment."
        )

    if refresh_token:
        creds = Credentials(
            token=None,
            refresh_token=refresh_token,
            token_uri="https://oauth2.googleapis.com/token",
            client_id=client_id,
            client_secret=client_secret,
            scopes=SCOPES,
        )

        try:
            creds.refresh(Request())
        except RefreshError:
            pass

        if creds.valid:
            return creds

    client_config = {
        "installed": {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uris": ["http://localhost"],
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
        }
    }
    flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
    creds = flow.run_local_server(port=0)
    token_path = os.path.join(os.path.dirname(__file__), "..", "token.json")
    with open(token_path, "w") as f:
        f.write(creds.refresh_token)
    print("New refresh token saved to token.json — update GOOGLE_REFRESH_TOKEN in 1Password.")
    return creds
