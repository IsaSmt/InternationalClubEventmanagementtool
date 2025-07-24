# modules/form_creator.py

from google.oauth2 import service_account
from googleapiclient.discovery import build
import os 
import streamlit as st
from google.oauth2.credentials import Credentials

SERVICE_ACCOUNT_FILE = "service_account.json" 
GOOGLE_DRIVE_FOLDER_ID = "1r5KpH6eV41ZfaaLqGDaB4mg52h-FC5H0"
CLIENT_SECRETS_FILE = "client_secrets.json"
TOKEN_FILE = "token.json"
SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/forms.body"]

def create_form_final_version_with_drive_title( 
    event_title: str, 
    event_price_for_form_question: str,
    form_description_text: str,
    credentials
    ): 
    """
    Erstellt ein Google Formular unter Verwendung der übergebenen Anmeldedaten.
    """
    if not event_title: raise ValueError("Event-Titel ist erforderlich.")
    if not event_price_for_form_question: raise ValueError("Preis für die Formularfrage ist erforderlich.")
    if not form_description_text: raise ValueError("Formularbeschreibung ist erforderlich.")
    
    form_service = build('forms', 'v1', credentials=credentials)
    drive_service = build('drive', 'v3', credentials=credentials)

    form_id = None
    edit_url = None
    form_body_initial = {"info": {"title": event_title}}
    try:
        form_response = form_service.forms().create(body=form_body_initial).execute() 
        form_id = form_response["formId"]
        edit_url = f"https://docs.google.com/forms/d/{form_id}/edit"
    except Exception as e:
        raise RuntimeError(f"Fehler beim initialen Erstellen des Google Formulars: {e}\nDetails: {getattr(e, 'content', '')}") from e

    if form_id:
        description_request = [{"updateFormInfo": {"info": {"description": form_description_text}, "updateMask": "description"}}]
        try:
            form_service.forms().batchUpdate(formId=form_id, body={"requests": description_request}).execute()
        except Exception as e:
            raise RuntimeError(f"Fehler beim Setzen der Beschreibung für Formular {form_id}: {e}\nDetails: {getattr(e, 'content', '')}") from e

    if form_id:
        questions_requests = [
            { "createItem": { "item": { "title": f"This event will cost you {event_price_for_form_question}", "questionItem": { "question": { "required": True, "choiceQuestion": { "type": "RADIO", "options": [{"value": f"Okay - {event_price_for_form_question}"}] }}}}, "location": {"index": 0} }},
            { "createItem": { "item": { "title": "First Name", "questionItem": { "question": { "required": True, "textQuestion": {}}}}, "location": {"index": 1} }},
            { "createItem": { "item": { "title": "Last Name", "questionItem": { "question": { "required": True, "textQuestion": {}}}}, "location": {"index": 2} }},
            { "createItem": { "item": { "title": "Country of Origin", "description": "Please start with a capital letter (e.g. Germany)", "questionItem": { "question": { "required": True, "textQuestion": {}}}}, "location": {"index": 3} }},
            { "createItem": { "item": { "title": "Phone Number", "description": "Please follow the pattern (e.g. +49 ..., +38....)", "questionItem": { "question": { "required": True, "textQuestion": {}}}}, "location": {"index": 4} }},
            { "createItem": { "item": { "title": "Do you have a Deutschlandticket for the month the event takes place?", "questionItem": { "question": { "required": True, "choiceQuestion": { "type": "RADIO", "options": [{"value": "Yes"}, {"value": "No"}] }}}}, "location": {"index": 5} }},
            { "createItem": { "item": { "title": "Exchange Type", "questionItem": { "question": { "required": True, "choiceQuestion": { "type": "RADIO", "options": [ {"value": "Erasmus (Hochschule München!)"}, {"value": "Other (Hochschule München!)"}, {"value": "Tutor"} ]}}}}, "location": {"index": 6} }}
        ]
        try:
            form_service.forms().batchUpdate(formId=form_id, body={"requests": questions_requests}).execute()
        except Exception as e:
            raise RuntimeError(f"Fehler beim Hinzufügen der Fragen für Formular {form_id}: {e}\nDetails: {getattr(e, 'content', '')}") from e

    if form_id: 
        try:
            file_metadata_body = {'name': event_title} 
            drive_service.files().update(fileId=form_id, body=file_metadata_body, fields='id, name').execute()
        except Exception as e:
            print(f"WARNUNG (form_creator): Konnte Dateinamen in Google Drive nicht setzen für Formular {form_id}: {e}\nDetails: {getattr(e, 'content', '')}")


    if form_id: 
        try:
            file_metadata_parents = drive_service.files().get(fileId=form_id, fields='parents').execute()
            current_parents = file_metadata_parents.get('parents', [])
            drive_service.files().update(
                fileId=form_id, addParents=GOOGLE_DRIVE_FOLDER_ID,
                removeParents=','.join(current_parents), fields="id, parents"
            ).execute()
        except Exception as e:
            print(f"WARNUNG (form_creator): Konnte Formular {form_id} nicht in Zielordner verschieben: {e}\nDetails: {getattr(e, 'content', '')}")
    
    return edit_url

if __name__ == "__main__":
    
    print("Starte Testlauf für modules/form_creator.py...")
    
    # Testdaten
    test_title = "Testformular"
    test_price_for_q = "9.99€"
    test_desc = """Dies ist die Beschreibung für das Testformular.
Details zum Event:
- xx
- yy
- zz

Datenschutzhinweis: xy."""

    print(f"\nVersuche, ein Formular zu erstellen mit Titel: '{test_title}'")
   
    try:
        form_link = create_form_final_version_with_drive_title(
            event_title=test_title,
            event_price_for_form_question=test_price_for_q,
            form_description_text=test_desc
        )
        print(f"\nTEST ERFOLGREICH!")
        print(f"Formular wurde erstellt/aktualisiert.")
        print(f"Link zum Bearbeiten des Formulars: {form_link}")
        print(f"Bitte überprüfe das Formular in deinem Google Drive Ordner (ID: {GOOGLE_DRIVE_FOLDER_ID})")
        print(f"  und stelle sicher, dass Titel, Beschreibung und Fragen korrekt sind.")
        print(f"  Der Dateiname in Drive sollte auch '{test_title}' sein.")

    except ValueError as ve:
        print(f"\nVALIDIERUNGSFEHLER im Test: {ve}")
    except ConnectionError as ce:
        print(f"\nVERBINDUNGSFEHLER im Test (wahrscheinlich service_account.json): {ce}")
    except RuntimeError as rte:
        print(f"\nAPI-FEHLER im Test während der Formularerstellung: {rte}")
    except Exception as e_global:
        print(f"\nEIN UNERWARTETER FEHLER ist im Test aufgetreten: {type(e_global).__name__} - {e_global}")

    print("\nTestlauf für modules/form_creator.py beendet.")