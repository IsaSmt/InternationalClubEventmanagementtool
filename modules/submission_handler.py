# modules/submission_handler.py
import streamlit as st 
import zipfile
import os
from datetime import datetime
from io import BytesIO 

from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload 

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from fpdf import FPDF 

SERVICE_ACCOUNT_FILE_DRIVE = "service_account.json" 
SCOPES_DRIVE_UPLOAD = ["https://www.googleapis.com/auth/drive.file"] 
TARGET_DRIVE_FOLDER_ID = "1dVWzdM35SKt2l967SAFhVEGgMpyI61IW" 

SMTP_SERVER = "smtp.gmail.com"
SMTP_PORT = 587 

def _is_streamlit_running():
    try:
        return hasattr(st, 'secrets') and callable(st.secrets.get)
    except Exception:
        return False

def create_submission_zip(event_name: str, 
                          participant_list_file, 
                          invoice_files: list, 
                          settlement_form_file,
                          experience_report_content: bytes, 
                          experience_report_filename: str = "Erfahrungsbericht.docx"
                          ) -> str | None:
    safe_event_name = "".join(x for x in event_name if x.isalnum() or x in " _-").strip().replace(" ", "_")
    if not safe_event_name: safe_event_name = "Abrechnung"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    zip_filename_base = f"Abrechnung_{safe_event_name}_{timestamp}.zip"
    zip_filepath = os.path.join("output", zip_filename_base) 
    os.makedirs("output", exist_ok=True)
    try:
        with zipfile.ZipFile(zip_filepath, 'w', zipfile.ZIP_DEFLATED) as zipf:
            if participant_list_file:
                name_to_write = getattr(participant_list_file, 'name', 'Teilnehmerliste.dat')
                content_to_write = getattr(participant_list_file, 'getvalue', lambda: participant_list_file.content_bytes)()
                zipf.writestr(name_to_write, content_to_write)
            if settlement_form_file: 
                name_to_write = getattr(settlement_form_file, 'name', 'Abrechnungsformular.dat')
                content_to_write = getattr(settlement_form_file, 'getvalue', lambda: settlement_form_file.content_bytes)()
                zipf.writestr(name_to_write, content_to_write)
            if experience_report_content: 
                zipf.writestr(experience_report_filename, experience_report_content)
            if invoice_files: 
                for i, invoice_file in enumerate(invoice_files):
                    name_to_write = getattr(invoice_file, 'name', f'Rechnung_{i+1}.dat')
                    content_to_write = getattr(invoice_file, 'getvalue', lambda: invoice_file.content_bytes)()
                    zipf.writestr(f"Rechnungen/Rechnung_{i+1}_{name_to_write}", content_to_write)
        return zip_filepath
    except Exception as e:
        msg = f"Fehler beim Erstellen der ZIP-Datei: {e}"
        if _is_streamlit_running(): st.error(msg)
        else: print(f"FEHLER (create_submission_zip): {msg}")
        return None

def upload_zip_to_drive(zip_filepath: str, event_name_for_filename: str) -> str | None:
    if not os.path.exists(zip_filepath):
        msg = f"Fehler: ZIP-Datei '{zip_filepath}' für Upload nicht gefunden."
        if _is_streamlit_running(): st.error(msg)
        else: print(f"FEHLER (upload_zip_to_drive): {msg}")
        return None
    try:
        creds = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE_DRIVE, scopes=SCOPES_DRIVE_UPLOAD)
        service = build('drive', 'v3', credentials=creds)
        drive_filename = os.path.basename(zip_filepath) 
        file_metadata = {'name': drive_filename, 'parents': [TARGET_DRIVE_FOLDER_ID]}
        media = MediaFileUpload(zip_filepath, mimetype='application/zip', resumable=True)
        file = service.files().create(body=file_metadata, media_body=media, fields='id, name, webViewLink').execute()
        return file.get('webViewLink')
    except FileNotFoundError:
        msg = f"FEHLER: Service Account Datei '{SERVICE_ACCOUNT_FILE_DRIVE}' für Google Drive nicht gefunden."
        if _is_streamlit_running(): st.error(msg)
        else: print(f"FEHLER (upload_zip_to_drive): {msg}")
        return None
    except Exception as e:
        msg = f"Fehler beim Google Drive Upload: {type(e).__name__} - {e}"
        if _is_streamlit_running(): st.error(msg)
        else: print(f"FEHLER (upload_zip_to_drive): {msg}. Details: {getattr(e, 'content', 'Keine weiteren Details')}")
        return None

def send_email_notification(recipient_email: str, event_name: str, drive_link: str | None) -> bool:
    sender_email_val = os.environ.get("GMAIL_APP_SENDER_EMAIL")
    sender_password_val = os.environ.get("GMAIL_APP_PASSWORD")
    if not sender_email_val or not sender_password_val:
        msg = "FEHLER: Absender-E-Mail oder App-Passwort nicht in Umgebungsvariablen gefunden."
        if _is_streamlit_running(): st.error(msg)
        else: print(msg)
        return False
    subject = f"Abrechnungsunterlagen für Event '{event_name}' wurden hochgeladen"
    if drive_link: body = f"Hallo,\n\ndie Abrechnungsunterlagen für '{event_name}' wurden hochgeladen:\n{drive_link}\n\nVG,\nEventtool"
    else: body = f"Hallo,\n\ndie Abrechnungsunterlagen für '{event_name}' wurden als ZIP erstellt, aber der Drive-Upload schlug fehl.\n\nVG,\nEventtool"
    try:
        msg = MIMEMultipart(); msg['From'] = sender_email_val; msg['To'] = recipient_email; msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain', 'utf-8')); server = smtplib.SMTP(SMTP_SERVER, SMTP_PORT)
        server.starttls(); server.login(sender_email_val, sender_password_val)
        server.sendmail(sender_email_val, recipient_email, msg.as_string()); server.quit()
        return True
    except Exception as e:
        m = f"E-Mail Fehler: {type(e).__name__} - {e}"; print(m); st.error(m) if _is_streamlit_running() else None
        return False

if __name__ == "__main__":
    print("Starte Testlauf für modules/submission_handler.py...")
    from dotenv import load_dotenv
    load_dotenv() 

    class DummyUploadedFileFromPath:
        def __init__(self, filepath):
            self.filepath = filepath
            self.name = os.path.basename(filepath)
            self._content_bytes = None
        
        def getvalue(self):
            if self._content_bytes is None:
                try:
                    with open(self.filepath, "rb") as f:
                        self._content_bytes = f.read()
                except FileNotFoundError:
                    print(f"  FEHLER: Datei '{self.filepath}' NICHT GEFUNDEN für Test.")
                    self._content_bytes = b"" 
                except Exception as e:
                    print(f"  FEHLER beim Lesen von '{self.filepath}': {e}")
                    self._content_bytes = b""
            return self._content_bytes

    test_event_name_main = "Canyoning_Event_SS25_Test" 
    output_dir = "output" 
    os.makedirs(output_dir, exist_ok=True)

    path_participant_list = os.path.join(output_dir, "temp_test_participants_for_sheet_loader.csv") 
    
    path_settlement_form = os.path.join(output_dir, "TEST_CLI_Abrechnungsformular.pdf") 
    
    report_event_title_slug = "Canyoning_International_Club_SS25"
    path_experience_report = os.path.join(output_dir, f"TEST_CLI_Erfahrungsbericht_{report_event_title_slug}.docx")

    dummy_invoice_paths = []
    for i in range(1, 3): 
        invoice_name = f"Dummy_Test_Rechnung_{i}.pdf"
        invoice_path = os.path.join(output_dir, invoice_name)
        if not os.path.exists(invoice_path):
            try:
                pdf = FPDF(); pdf.add_page(); pdf.set_font("Arial", "B", 12)
                pdf.cell(0, 10, f"Dummy Rechnung {i} für {test_event_name_main}", 0, 1, 'C')
                pdf.output(invoice_path, "F")
                print(f"  INFO: Dummy-Rechnung '{invoice_path}' für Test erstellt.")
            except Exception as e_pdf:
                print(f"  FEHLER beim Erstellen der Dummy-Rechnung '{invoice_path}': {e_pdf}")
        if os.path.exists(invoice_path): 
             dummy_invoice_paths.append(invoice_path)
    
    print("\nFolgende Dateien werden für das Test-ZIP verwendet:")
    print(f"  Teilnehmerliste: {path_participant_list} {'(OK)' if os.path.exists(path_participant_list) else '(FEHLT!)'}")
    print(f"  Abrechnungsformular: {path_settlement_form} {'(OK)' if os.path.exists(path_settlement_form) else '(FEHLT!)'}")
    print(f"  Erfahrungsbericht: {path_experience_report} {'(OK)' if os.path.exists(path_experience_report) else '(FEHLT!)'}")
    for p in dummy_invoice_paths:
        print(f"  Rechnung (Dummy): {p} {'(OK)' if os.path.exists(p) else ''}")
    
    input("\nÜberprüfe die Existenz der oben gelisteten Dateien. Drücke Enter zum Fortfahren...")

    participants_file_obj = DummyUploadedFileFromPath(path_participant_list) if os.path.exists(path_participant_list) else None
    settlement_file_obj = DummyUploadedFileFromPath(path_settlement_form) if os.path.exists(path_settlement_form) else None
    
    experience_report_bytes_content = b""
    experience_report_final_name = os.path.basename(path_experience_report)
    if os.path.exists(path_experience_report):
        with open(path_experience_report, "rb") as f_report:
            experience_report_bytes_content = f_report.read()
    else:
        print(f"WARNUNG: Erfahrungsbericht '{path_experience_report}' nicht gefunden. ZIP enthält keinen Bericht.")
        experience_report_final_name = f"Erfahrungsbericht_{test_event_name_main.replace(' ','_')}_FEHLT.docx" 

    test_invoices_list_obj = [DummyUploadedFileFromPath(p) for p in dummy_invoice_paths if os.path.exists(p)]

    print(f"\nSchritt 1: Erstelle Test-ZIP-Datei für Event: '{test_event_name_main}'")
    if not participants_file_obj: print("  WARNUNG: Teilnehmerliste für ZIP wird fehlen.")
    if not settlement_file_obj: print("  WARNUNG: Abrechnungsformular für ZIP wird fehlen.")
    if not experience_report_bytes_content: print(" WARNUNG: Erfahrungsbericht für ZIP wird fehlen.")
    
    generated_zip_path = create_submission_zip(
        event_name=test_event_name_main,
        participant_list_file=participants_file_obj,
        invoice_files=test_invoices_list_obj,
        settlement_form_file=settlement_file_obj,
        experience_report_content=experience_report_bytes_content,
        experience_report_filename=experience_report_final_name
    )

    if generated_zip_path and os.path.exists(generated_zip_path):
        print(f"  ERFOLG: ZIP-Datei erstellt: {generated_zip_path}")
        print(f"  Die ZIP-Datei '{os.path.basename(generated_zip_path)}' bleibt im '{output_dir}'-Ordner erhalten.")
        
        drive_link_result = None
        if input("\nSoll das ZIP nach Google Drive hochgeladen werden? (ja/nein): ").strip().lower() == 'ja':
            print(f"  Lade ZIP '{os.path.basename(generated_zip_path)}' nach Google Drive hoch...")
            drive_link_result = upload_zip_to_drive(generated_zip_path, test_event_name_main)
            if drive_link_result: print(f"  ERFOLG: Drive Upload. Link: {drive_link_result}")
            else: print("  FEHLER: Drive Upload fehlgeschlagen.")
        
        recipient = input("\nEmpfänger-E-Mail für Test-Benachrichtigung (Enter zum Überspringen): ").strip()
        if recipient:
            print(f"  Sende E-Mail an {recipient}...")
            email_success = send_email_notification(recipient, test_event_name_main, drive_link_result)
            if email_success: print(f"  ERFOLG: E-Mail gesendet.")
            else: print(f"  FEHLER: E-Mail nicht gesendet.")
        else: print("  E-Mail-Versand übersprungen.")
    else:
        print("  FEHLER: ZIP-Datei konnte nicht erstellt werden oder wurde nicht gefunden.")

    print("\nTestlauf für modules/submission_handler.py beendet.")