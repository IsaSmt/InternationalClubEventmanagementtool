# modules/auth.py (FINAL, mit robuster Umgebungsprüfung)

import streamlit as st
import os
import json
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

# --- KONFIGURATION ---
CLIENT_SECRETS_FILE = "client_secrets.json"
SCOPES = [
    "https://www.googleapis.com/auth/drive",
    "https://www.googleapis.com/auth/forms.body",
    "https://www.googleapis.com/auth/spreadsheets.readonly"
]
# Die REDIRECT_URI muss in den Secrets für die Cloud-Version hinterlegt sein.
# Lokal wird der Fallback verwendet.
REDIRECT_URI = st.secrets.get("REDIRECT_URI") or os.getenv("STREAMLIT_SERVER_BASE_URL", "http://localhost:8501")


def get_google_auth_flow():
    """
    Erstellt und konfiguriert das Google OAuth Flow-Objekt.
    Liest die Konfiguration flexibel aus st.secrets oder einer lokalen Datei.
    """
    # 1. Prüfen, ob der Secret-Key "google_oauth" in der Streamlit Cloud-Konfiguration existiert.
    if "google_oauth" in st.secrets:
        try:
            client_config = st.secrets["google_oauth"]
            # Umwandeln, falls das Secret als String und nicht als Dictionary geladen wird
            if isinstance(client_config, str):
                client_config = json.loads(client_config)

            return Flow.from_client_config(
                client_config,
                scopes=SCOPES,
                redirect_uri=REDIRECT_URI
            )
        except Exception as e:
            st.error(f"Google OAuth Secrets konnten nicht verarbeitet werden: {e}")
            return None
    
    # 2. Fallback für die lokale Entwicklung: Lade die lokale Datei.
    else:
        if not os.path.exists(CLIENT_SECRETS_FILE):
            st.error(f"FEHLER: Die Konfigurationsdatei '{CLIENT_SECRETS_FILE}' wurde nicht gefunden. "
                     "Bitte folgen Sie der Anleitung in der README.md, um sie zu erstellen und zu platzieren.")
            return None
            
        return Flow.from_client_secrets_file(
            CLIENT_SECRETS_FILE,
            scopes=SCOPES,
            redirect_uri=REDIRECT_URI
        )

def get_credentials():
    """
    Holt die Anmeldedaten aus dem Session State. Gibt None zurück, wenn nicht vorhanden.
    """
    if 'google_credentials' in st.session_state and st.session_state['google_credentials']:
        creds_dict = st.session_state['google_credentials']
        return Credentials.from_authorized_user_info(creds_dict, SCOPES)
    return None

def authenticate_google():
    """
    Haupt-Authentifizierungsfunktion für die Streamlit-App.
    Gibt die Credentials zurück, wenn der Nutzer angemeldet ist.
    Zeigt einen Anmelde-Button an und stoppt die App, wenn nicht.
    """
    # Initialisiere den Session State, falls er noch nicht existiert
    if 'google_credentials' not in st.session_state:
        st.session_state['google_credentials'] = None

    # Prüfen, ob der Nutzer bereits gültige Anmeldedaten in der Session hat
    creds = get_credentials()
    if creds and creds.valid:
        # Erneuere das Token, falls es abgelaufen ist
        if creds.expired and creds.refresh_token:
            creds.refresh(Request())
            st.session_state['google_credentials'] = json.loads(creds.to_json())
        return creds

    # Prüfen, ob der Nutzer gerade von der Google-Anmeldung zurückkehrt
    auth_code = st.query_params.get("code")
    if auth_code:
        try:
            flow = get_google_auth_flow()
            if flow is None: return None

            flow.fetch_token(code=str(auth_code))
            
            # Die neuen Credentials als Dictionary im Session State speichern
            creds_json_str = flow.credentials.to_json()
            st.session_state['google_credentials'] = json.loads(creds_json_str)
            
            # Bereinige die URL und lade die App neu
            st.query_params.clear()
            st.rerun()

        except Exception as e:
            st.error(f"Fehler bei der Authentifizierung: {e}")
            st.session_state['google_credentials'] = None
            return None

    # Wenn weder angemeldet noch ein Code vorhanden ist -> Anmelde-Button anzeigen
    else:
        flow = get_google_auth_flow()
        if flow is None: return None

        authorization_url, _ = flow.authorization_url(
            access_type='offline',  # Wichtig für Refresh-Tokens
            prompt='consent'        # Zwingt den Nutzer, die Berechtigungen immer zu bestätigen
        )
        
        st.info("Um auf Google-Funktionen zuzugreifen, müssen Sie sich anmelden.")
        st.link_button("Mit Google anmelden", authorization_url)
        return None