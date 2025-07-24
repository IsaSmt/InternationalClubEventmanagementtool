# modules/google_sheets_reader.py (FINALE, KORRIGIERTE VERSION)

import pandas as pd
import re
import os
import streamlit as st
from googleapiclient.discovery import build

def extract_sheet_id(sheet_url: str) -> str | None:
    """Extrahiert die Spreadsheet-ID aus einer Google Sheets URL."""
    if not isinstance(sheet_url, str):
        return None
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_url)
    return match.group(1) if match else None

#@st.cache_data(ttl=300)
def load_participants_from_google_sheet(sheet_url: str, credentials=None) -> pd.DataFrame:
    """
    Lädt Teilnehmerdaten aus einem Google Sheet.
    Verwendet übergebene Credentials für private Sheets (Haupt-App).
    Versucht anonymen Zugriff für den Kiosk-Modus (erfordert öffentlich lesbares Sheet).
    """
    if not sheet_url:
        raise ValueError("Keine Google Sheet URL übergeben.")
    sheet_id = extract_sheet_id(sheet_url)
    if not sheet_id:
        raise ValueError(f"Ungültige Google Sheet URL: {sheet_url}")

    try:
        # Verwende die übergebenen OAuth2-Credentials
        if credentials:
            sheets_service = build('sheets', 'v4', credentials=credentials)
        else:
            # Fallback für den Kiosk-Modus (erfordert öffentlich lesbares Sheet oder API Key)
            # Für ein öffentliches Sheet wird kein API-Key benötigt, wir übergeben None.
            sheets_service = build('sheets', 'v4')

        metadata = sheets_service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        
        if not metadata.get('sheets'):
            return pd.DataFrame() # Leeres Sheet, kein Fehler
            
        first_sheet_title = metadata['sheets'][0]['properties']['title']
        
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=first_sheet_title
        ).execute()

    except Exception as e:
        # Gib eine verständlichere Fehlermeldung aus
        if "service_account.json" in str(e):
             raise ConnectionError(f"Fehler bei der Authentifizierung: Das Modul 'google_sheets_reader' scheint eine veraltete Service-Account-Logik zu verwenden.")
        raise ConnectionError(f"Fehler beim API-Zugriff auf Google Sheet ID '{sheet_id}': {e}") from e

    values = result.get('values', [])
    if not values or len(values) < 1:
        return pd.DataFrame()

    header = values[0]
    # Fülle fehlende Spalten in Datenzeilen mit leeren Strings, um Längenkonflikte zu vermeiden
    num_columns = len(header)
    rows = [row + [''] * (num_columns - len(row)) for row in values[1:]]
    
    df = pd.DataFrame(rows, columns=header)
    
    # Der Rest der Logik (Spaltenauswahl, Speichern) ist nicht mehr nötig,
    # da process_dataframe_for_display das übernimmt. Wir geben den rohen DF zurück.
    return df