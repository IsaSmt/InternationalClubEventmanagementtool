# modules/auth.py (Finale Version mit json-Import)

import streamlit as st
import os
import json  # <-- DIESE ZEILE HINZUFÜGEN
from google.oauth2.credentials import Credentials
from google.auth.transport.requests import Request

TOKEN_FILE = "token.json"
SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/forms.body", "https://www.googleapis.com/auth/spreadsheets.readonly"]

def get_credentials():
    creds = None
    
    # Prüft, ob die TOKEN-Variable in den Secrets existiert (Cloud-Umgebung)
    if "GOOGLE_CREDENTIALS_JSON" in st.secrets:
        creds_info = json.loads(st.secrets["GOOGLE_CREDENTIALS_JSON"])
        creds = Credentials.from_authorized_user_info(creds_info, SCOPES)
    
    # Fallback für die lokale Entwicklung
    elif os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
        
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        if os.path.exists(TOKEN_FILE):
             with open(TOKEN_FILE, 'w') as token:
                token.write(creds.to_json())

    return creds

def authenticate_google():
    """
    Prüft, ob die token.json vorhanden ist.
    """
    creds = get_credentials()
    if creds and creds.valid:
        return creds
    else:
        st.error("Anmeldung fehlgeschlagen: 'token.json' nicht gefunden oder ungültig.")
        st.info("Bitte führe `python generate_token.py` im Terminal aus, um dich anzumelden.")
        return None