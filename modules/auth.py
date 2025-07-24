# modules/auth.py

import streamlit as st
import os
import json
from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials

CLIENT_SECRETS_FILE = "client_secrets.json"
SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/forms.body", "https://www.googleapis.com/auth/spreadsheets.readonly"]
REDIRECT_URI = os.getenv("STREAMLIT_SERVER_BASE_URL", "http://localhost:8501")


def get_google_auth_flow():
    """Erstellt und konfiguriert das Google OAuth Flow-Objekt."""
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
    creds = get_credentials()
    if creds and creds.valid:
        return creds

    auth_code = st.query_params.get("code")
    if auth_code:
        try:
            flow = get_google_auth_flow()
            flow.fetch_token(code=str(auth_code))
            
            creds_json_str = flow.credentials.to_json()
            st.session_state['google_credentials'] = json.loads(creds_json_str)
            
            st.query_params.clear()
            st.rerun()

        except Exception as e:
            st.error(f"Fehler bei der Authentifizierung: {e}")
            st.session_state['google_credentials'] = None
            return None

    else:
        if 'google_credentials' not in st.session_state:
            st.session_state['google_credentials'] = None
            
        flow = get_google_auth_flow()
        authorization_url, _ = flow.authorization_url(prompt='consent')
        
        st.info("Um auf Google-Funktionen zuzugreifen, müssen Sie sich anmelden.")
        st.link_button("Mit Google anmelden", authorization_url)
        return None