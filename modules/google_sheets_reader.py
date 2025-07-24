# modules/google_sheets_reader.py

from google.oauth2 import service_account
from googleapiclient.discovery import build
import pandas as pd
import re
import os
import streamlit as st

SERVICE_ACCOUNT_FILE = "service_account.json"
SCOPES = ["https://www.googleapis.com/auth/spreadsheets.readonly"]

def extract_sheet_id(sheet_url: str) -> str | None:
    """Extrahiert die Spreadsheet-ID aus einer Google Sheets URL."""
    if not isinstance(sheet_url, str):
        return None
    match = re.search(r"/spreadsheets/d/([a-zA-Z0-9-_]+)", sheet_url)
    if match:
        return match.group(1)
    return None

@st.cache_data(ttl=300)

def load_participants_from_google_sheet(sheet_url: str) -> pd.DataFrame:
    """
    Lädt Teilnehmerdaten aus dem ersten Tabellenblatt eines Google Sheets
    und gibt einen DataFrame mit den relevanten Spalten zurück.
    Die Funktion ist tolerant gegenüber kleineren Abweichungen in den Spaltennamen.
    """
    if not sheet_url:
        raise ValueError("Keine Google Sheet URL übergeben.")
    sheet_id = extract_sheet_id(sheet_url)
    if not sheet_id:
        raise ValueError(f"Ungültige Google Sheet URL, konnte keine ID extrahieren: {sheet_url}")

    try:
        creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    except FileNotFoundError:
        raise FileNotFoundError(f"Service Account Datei '{SERVICE_ACCOUNT_FILE}' nicht gefunden.")
    except Exception as e:
        raise ConnectionError(f"Authentifizierungsfehler mit Google Service Account: {e}") from e

    try:
        sheets_service = build('sheets', 'v4', credentials=creds)
        metadata = sheets_service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        
        if not metadata.get('sheets'):
            raise LookupError(f"Konnte keine Tabellenblätter im Google Sheet mit ID '{sheet_id}' finden.")
            
        first_sheet_title = metadata['sheets'][0]['properties']['title']
        
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=first_sheet_title
        ).execute()
    except Exception as e:
        raise ConnectionError(f"Fehler beim API-Zugriff auf Google Sheet ID '{sheet_id}': {e}\nDetails: {getattr(e, 'content', '')}") from e

    values = result.get('values', [])
    if not values or len(values) < 1:
        # Wenn das Sheet komplett leer ist, geben wir einen leeren DataFrame mit den erwarteten Spalten zurück
        return pd.DataFrame(columns=["First Name", "Last Name", "Phone Number", "Country of Origin", "Exchange Type", "E-Mail-Adresse"])

    header = values[0]
    rows = values[1:] if len(values) > 1 else []
    
    try:
        df = pd.DataFrame(rows, columns=header)
    except Exception as e:
        raise ValueError(f"Fehler beim Erstellen des DataFrame aus Google Sheet Daten: {e}") from e

    column_map = {
        'First Name': ['First Name'],
        'Last Name': ['Last Name'],
        'Phone Number': ['Phone Number', 'Mobile'],
        'Country of Origin': ['Country of Origin', 'Country'],
        'Exchange Type': ['Exchange Type', 'Type'],
        'E-Mail-Adresse': ['E-Mail-Adresse', 'Email']
    }

    df_selected = pd.DataFrame()
    
    df_cols_normalized = {col.strip().lower(): col for col in df.columns}

    for target_col, source_options in column_map.items():
        found = False
        for option in source_options:
            if option.lower() in df_cols_normalized:
                original_col_name = df_cols_normalized[option.lower()]
                df_selected[target_col] = df[original_col_name]
                found = True
                break
        if not found:
            df_selected[target_col] = ''

    try:
        os.makedirs("data", exist_ok=True)
        csv_path = os.path.join("data", "teilnehmer.csv")
        df_selected.to_csv(csv_path, index=False)
    except Exception as e:
        print(f"WARNUNG (google_sheets_reader): Fehler beim Speichern der CSV '{csv_path}': {e}")

    return df_selected
    """ 
    Lädt Teilnehmerdaten aus dem ersten Tabellenblatt eines Google Sheets
    und speichert eine Auswahl von Spalten als 'data/teilnehmer.csv'.
    Gibt einen DataFrame mit den ausgewählten Spalten zurück.
    Wirft Exceptions bei Fehlern.
    """
    if not sheet_url:
        raise ValueError("Keine Google Sheet URL übergeben.")
    sheet_id = extract_sheet_id(sheet_url)
    if not sheet_id:
        raise ValueError(f"Ungültige Google Sheet URL, konnte keine ID extrahieren: {sheet_url}")

    try:
        creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    except FileNotFoundError:
        raise FileNotFoundError(f"Service Account Datei '{SERVICE_ACCOUNT_FILE}' nicht gefunden.")
    except Exception as e:
        raise ConnectionError(f"Authentifizierungsfehler mit Google Service Account: {e}") from e

    try:
        sheets_service = build('sheets', 'v4', credentials=creds)
        metadata = sheets_service.spreadsheets().get(spreadsheetId=sheet_id).execute()
        
        if not metadata.get('sheets'):
            raise LookupError(f"Konnte keine Tabellenblätter im Google Sheet mit ID '{sheet_id}' finden.")
            
        first_sheet_title = metadata['sheets'][0]['properties']['title']
        
        result = sheets_service.spreadsheets().values().get(
            spreadsheetId=sheet_id,
            range=first_sheet_title
        ).execute()
    except Exception as e:
        raise ConnectionError(f"Fehler beim API-Zugriff auf Google Sheet ID '{sheet_id}': {e}\nDetails: {getattr(e, 'content', '')}") from e

    values = result.get('values', [])
    if not values or len(values) < 1:
        expected_cols_for_empty = ["First Name", "Last Name", "Phone Number", "Country of Origin", "Exchange Type", "E-Mail-Adresse"]
        return pd.DataFrame(columns=expected_cols_for_empty)

    header = values[0]
    rows = values[1:] if len(values) > 1 else []
    
    try:
        df = pd.DataFrame(rows, columns=header)
    except Exception as e:
        raise ValueError(f"Fehler beim Erstellen des DataFrame aus Google Sheet Daten: {e}") from e

    expected_columns_from_sheet = [
        "First Name", 
        "Last Name", 
        "Phone Number", 
        "Country of Origin", 
        "Exchange Type",
        "E-Mail-Adresse" 
    ]
    columns_to_select = [col for col in expected_columns_from_sheet if col in df.columns]
    
    if not columns_to_select and not df.empty:
        df_selected = pd.DataFrame(columns=expected_columns_from_sheet)
    elif df.empty: 
        df_selected = pd.DataFrame(columns=expected_columns_from_sheet)
    else: 
        df_selected = df[columns_to_select].copy()

    try:
        os.makedirs("data", exist_ok=True)
        csv_path = os.path.join("data", "teilnehmer.csv")
        df_selected.to_csv(csv_path, index=False)
    except Exception as e:
        print(f"WARNUNG (google_sheets_reader): Fehler beim Speichern der CSV '{csv_path}': {e}")

    return df_selected

if __name__ == "__main__":
    print("Starte Testlauf für modules/google_sheets_reader.py...")

    test_sheet_url = "https://docs.google.com/spreadsheets/d/1aOV1_UqtKVNEfH9oikzBYMtayPsIZHh8Hw4j-ZUCJfE/edit#gid=0" 
    
    print(f"\nTeste extract_sheet_id mit URL: {test_sheet_url}")
    extracted_id = extract_sheet_id(test_sheet_url)
    if extracted_id:
        print(f"  Erfolgreich extrahierte Sheet ID: {extracted_id}")
    else:
        print(f"  FEHLER: Konnte keine Sheet ID aus der URL extrahieren.")

    print(f"\nVersuche, Teilnehmerdaten von Google Sheet zu laden: {test_sheet_url}")
    print("Stelle sicher, dass 'service_account.json' vorhanden und korrekt konfiguriert ist,")
    print("und dass der Service Account Lesezugriff auf das oben genannte Test-Sheet hat.")

    try:
        participants_data = load_participants_from_google_sheet(test_sheet_url)
        
        if not participants_data.empty:
            print("\nTEST ERFOLGREICH: Daten von Google Sheet geladen.")
            print("Erste 5 Zeilen des geladenen DataFrames:")
            print(participants_data.head())
            print(f"\nDie Daten wurden auch versucht, in 'data/teilnehmer.csv' zu speichern.")
        elif isinstance(participants_data, pd.DataFrame): 
             print("\nINFO: Das Google Sheet ist leer oder enthielt keine der erwarteten Spalten (leerer DataFrame zurückgegeben).")
        else: 
            print("\nFEHLER im Test: load_participants_from_google_sheet hat ein unerwartetes Ergebnis zurückgegeben.")

    except ValueError as ve:
        print(f"\nVALIDIERUNGSFEHLER im Test: {ve}")
    except FileNotFoundError as fnfe:
        print(f"\nDATEI NICHT GEFUNDEN FEHLER im Test (wahrscheinlich service_account.json): {fnfe}")
    except ConnectionError as ce:
        print(f"\nVERBINDUNGSFEHLER im Test (Authentifizierung oder API-Zugriff): {ce}")
    except LookupError as le:
        print(f"\nLOOKUP FEHLER im Test (z.B. keine Tabellenblätter gefunden): {le}")
    except Exception as e_global:
        print(f"\nEIN UNERWARTETER FEHLER ist im Test aufgetreten: {type(e_global).__name__} - {e_global}")

    print("\nTestlauf für modules/google_sheets_reader.py beendet.")