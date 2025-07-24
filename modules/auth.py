# modules/auth.py (FINAL, mit Desktop-Flow für lokale Entwicklung)

import streamlit as st
import os
import json
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# --- KONFIGURATION ---
CLIENT_SECRETS_WEB_FILE = "client_secrets.json" # Für Streamlit Cloud
CLIENT_SECRETS_DESKTOP_FILE = "client_secrets_desktop.json" # Für lokale Tests
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/spreadsheets.readonly"
]

def get_google_auth_flow():
    """
    Erstellt das passende Google OAuth Flow-Objekt je nach Umgebung.
    """
    # Fall 1: Läuft auf Streamlit Cloud -> Web Flow mit Secrets
    if "google_oauth" in st.secrets:
        try:
            client_config = st.secrets["google_oauth"]
            redirect_uri = st.secrets.get("REDIRECT_URI", "https://DEINE-APP-URL.streamlit.app")
            return Flow.from_client_config(
                client_config, scopes=SCOPES, redirect_uri=redirect_uri
            )
        except Exception as e:
            st.error(f"Google OAuth Secrets konnten nicht verarbeitet werden: {e}")
            return None
            
    # Fall 2: Läuft lokal -> Desktop Flow mit lokaler Datei
    else:
        if not os.path.exists(CLIENT_SECRETS_DESKTOP_FILE):
            st.error(f"Für die lokale Entwicklung wird die '{CLIENT_SECRETS_DESKTOP_FILE}' benötigt.")
            return None
        return InstalledAppFlow.from_client_secrets_file(
            CLIENT_SECRETS_DESKTOP_FILE, scopes=SCOPES
        )

def authenticate_google():
    """
    Haupt-Authentifizierungsfunktion.
    """
    if 'google_credentials' not in st.session_state:
        st.session_state['google_credentials'] = None

    if st.session_state['google_credentials']:
        creds = Credentials.from_authorized_user_info(st.session_state['google_credentials'], SCOPES)
        if creds.valid:
            if creds.expired and creds.refresh_token:
                creds.refresh(Request())
                st.session_state['google_credentials'] = json.loads(creds.to_json())
            return creds

    # Prüfen, ob der Nutzer gerade von der Web-Flow-Anmeldung zurückkehrt
    auth_code = st.query_params.get("code")
    if auth_code:
        try:
            flow = get_google_auth_flow()
            flow.fetch_token(code=str(auth_code))
            creds_json = json.loads(flow.credentials.to_json())
            st.session_state['google_credentials'] = creds_json
            st.query_params.clear()
            st.rerun()
        except Exception as e:
            st.error(f"Fehler bei der Authentifizierung: {e}")
            return None
    
    # Wenn keine Credentials vorhanden sind, zeige den Anmelde-Button
    else:
        if "google_oauth" in st.secrets: # Web Flow
            flow = get_google_auth_flow()
            authorization_url, _ = flow.authorization_url(prompt='consent', access_type='offline')
            st.info("Bitte melden Sie sich an, um fortzufahren.")
            st.link_button("Mit Google anmelden", authorization_url)
        else: # Desktop Flow für lokal
            if st.button("Mit Google anmelden"):
                flow = get_google_auth_flow()
                # Dieser Flow blockiert die App, startet einen lokalen Server und öffnet den Browser.
                # Nach Erfolg wird der Browser-Tab geschlossen und die Credentials sind da.
                creds = flow.run_local_server(port=0)
                creds_json = json.loads(creds.to_json())
                st.session_state['google_credentials'] = creds_json
                st.rerun() # Lade die Seite neu, jetzt mit Credentials

        return None