# main.py

import streamlit as st
import os 
import pandas as pd 
from dotenv import load_dotenv
import time
from PIL import Image
from modules.auth import authenticate_google

# --- HILFSFUNKTION ZUM LADEN VON CSS ---
def local_css(file_name):
    """Liest eine lokale CSS-Datei und injiziert sie in die Streamlit-App."""
    try:
        with open(file_name) as f:
            st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
    except FileNotFoundError:
        st.warning(f"Warnung: CSS-Datei '{file_name}' nicht gefunden. Das Design wird nicht angewendet.")

# --- SEITENKONFIGURATION ---
st.set_page_config(
    page_title="International Club - Eventtool", 
    page_icon="🎓", 
    layout="wide"
)

# --- LADE GLOBALES STYLING ---
local_css("style.css")

# --- Lade Umgebungsvariablen und Module ---
load_dotenv() 

from modules.signature_capture import capture_signature 
from modules.pdf_generator import generate_participant_pdf 
from modules.sheet_loader import load_participants_from_csv, process_dataframe_for_display 
from modules.qr_generator import generate_custom_qr_code_base64
from modules.google_sheets_reader import load_participants_from_google_sheet, extract_sheet_id
from modules.form_creator import create_form_final_version_with_drive_title
from modules.submission_handler import create_submission_zip, upload_zip_to_drive, send_email_notification 
from modules.report_ai_generator import generate_experience_report_docx 


# --- URL-Parameter auslesen ---
query_params = st.query_params 
page_param = query_params.get("page") 
if page_param is None: page_param = ""
sheet_id_param = query_params.get("sheet_id") 

# --- Spezialbehandlung für Kiosk-Modus ---
if page_param == "sign":
    st.markdown("""
        <style>
            /* Blende Sidebar und Hauptmenü im Kiosk-Modus aus */
            div[data-testid="stSidebarNav"] { display: none; }
            div[data-testid="stSidebar"] { display: none; }
            
            /* Zentriere den Inhalt im Kiosk-Modus noch stärker */
            .main .block-container { 
                max-width: 700px !important; 
                padding-left: 1rem !important;
                padding-right: 1rem !important;
            }
        </style>
    """, unsafe_allow_html=True)

# --- Restliche Initialisierungen und Debug-Ausgaben ---
print(f"DEBUG (main.py - TOP): Roh-Query-Parameter-Objekt: {query_params}") 
print(f"DEBUG (main.py - TOP): Verarbeitete URL-Parameter: page_param='{page_param}', sheet_id_param='{sheet_id_param}'")

BASE_URL = os.getenv("STREAMLIT_SERVER_BASE_URL", "http://10.137.31.126:8501")
print(f"DEBUG (main.py): Verwendete BASE_URL: {BASE_URL}")

# Session State Initialisierungen
if 'participants_df' not in st.session_state: st.session_state.participants_df = pd.DataFrame() 
if 'participants_df_for_sign' not in st.session_state: st.session_state.participants_df_for_sign = pd.DataFrame()
if 'current_loaded_sheet_id_for_sign' not in st.session_state: st.session_state.current_loaded_sheet_id_for_sign = None
if 'generated_report_for_submission' not in st.session_state: st.session_state.generated_report_for_submission = None
if 'generated_zip_path' not in st.session_state: st.session_state.generated_zip_path = None
if "pdf_event_name_val" not in st.session_state: st.session_state.pdf_event_name_val = ""
if "pdf_event_date_val" not in st.session_state: st.session_state.pdf_event_date_val = ""
if "pdf_tutors_val" not in st.session_state: st.session_state.pdf_tutors_val = ""
if "pdf_price_val" not in st.session_state: st.session_state.pdf_price_val = ""


# --- Logik für das Laden der Daten beim Aufruf über QR-Code / ?page=sign ---
if page_param == "sign":
    st.image(os.path.join("data", "I-CLUB_LOGO.png"), width=100) 
    st.title("Digitale Unterschrift")
    st.markdown("---")
    
    if sheet_id_param:
        if st.session_state.current_loaded_sheet_id_for_sign != sheet_id_param or st.session_state.participants_df_for_sign.empty:
            st.session_state.current_loaded_sheet_id_for_sign = sheet_id_param
            print(f"DEBUG (main.py - Sign Page): Lade Daten für sheet_id '{sheet_id_param}'.")
            sheet_url = f"https://docs.google.com/spreadsheets/d/{sheet_id_param}/edit"
            with st.spinner("Lade Teilnehmerdaten von Google Sheets..."):
                temp_df_google = load_participants_from_google_sheet(sheet_url) 
            
            if not temp_df_google.empty:
                with st.spinner("Verarbeite Teilnehmerdaten..."):
                    st.session_state.participants_df_for_sign = process_dataframe_for_display(temp_df_google)
                if not st.session_state.participants_df_for_sign.empty:
                    st.success("Teilnehmerliste geladen!")
                    time.sleep(1.5) 
                    st.rerun() 
                else: 
                    st.warning("Teilnehmerdaten konnten nicht aufbereitet werden.")
                    st.stop()
            else: 
                st.error(f"Fehler: Konnte keine Daten von Google Sheet ID '{sheet_id_param}' laden oder das Sheet ist leer.")
                st.stop() 
        
        if not st.session_state.participants_df_for_sign.empty:
            capture_signature(st.session_state.participants_df_for_sign)
        else:
            st.info("Warte auf Teilnehmerdaten...") 
    else:
        st.error("Keine Sheet ID in der URL gefunden. Diese Seite bitte über den QR-Code aufrufen.")
    st.stop() 

# --- Normaler App-Aufbau ---
logo_path = os.path.join("data", "I-CLUB_LOGO_Sidebar.png")
if os.path.exists(logo_path):
    st.sidebar.image(logo_path, use_container_width=True)
else:
    st.sidebar.warning("Logo-Datei 'data/I-CLUB_LOGO.png' nicht gefunden.")

st.title("International Club - Eventtool")
st.subheader("Organisiere Events, Teilnehmer und Abrechnungen")

menu_options = [  
    "🏠 Start", 
    "📝 Einladung erstellen",  
    "✍️ Unterschriften sammeln & QR", 
    "📄 Teilnehmerliste & PDF Management", 
    "🧾 Abrechnung & Bericht einreichen",
]
default_menu_index = 0 
menu_selection = st.sidebar.selectbox("Navigation", menu_options, index=default_menu_index, key="main_menu_v11_kiosk")

if menu_selection == "🏠 Start":
    st.write("Willkommen im Event-Management-Tool für den International Club! 🎓")
    st.info("Bitte wähle links im Menü aus, was du tun möchtest.")
    st.markdown("---")
    st.write("Aktuell geladene Teilnehmer (Vorschau aus Haupt-DataFrame):")
    if not st.session_state.participants_df.empty:
        st.dataframe(st.session_state.participants_df.head())
    else:
        st.write("Noch keine Teilnehmerliste global geladen.")

elif menu_selection == "📝 Einladung erstellen": 
    st.subheader("📝 Google Formular erstellen")
    
    creds = authenticate_google()
    if not creds:
        st.stop()
    st.subheader("📝 Google Formular erstellen")
    event_title = st.text_input("📌 Event-Titel", key="form_event_title_sl") 
    event_specific_text_input = st.text_area("📝 Event-spezifischer Info-Text",key="form_event_specific_text_sl")
    event_date_time_input = st.text_input("📅 Event Datum & Uhrzeit", key="form_event_datetime_sl")
    event_price_input = st.text_input("💵 Preis (€)", key="form_event_price_sl")
    event_location_input = st.text_input("🏡 Ort", key="form_event_location_sl")
    
    if st.button("Google Formular erstellen", key="btn_create_form_sl"):
        if not all([event_title, event_specific_text_input, event_date_time_input, event_price_input, event_location_input]):
            st.warning("Bitte alle Event-Infos ausfüllen!")
        else:
            full_form_description = f"""Please fill out the form to sign up for the event. Only after your payment you are fully signed up!

ONLY HOCHSCHULE MÜNCHEN INTERNATIONAL STUDENTS CAN REGISTER (Also if you study full-time at MUAS)!
Only after your payment you are fully signed up!
Payment by Credit Card is not possible. If you wish to pay in cash, please text the tutor that posted the event and something can be arranged.
Unfortunately we can not offer you any refund if you don't participate in the event.

EVENT INFORMATION:
{event_specific_text_input}

📅 Event date: {event_date_time_input}
💵 Price: {event_price_input}
🏡 Location: {event_location_input}

DATA PRIVACY NOTICE:
By submitting this form, you agree that we process the data you provide for the purpose of event planning. This includes storing and using your personal information for communication related to the event. Your data will only be accessible to the event organizers for this purpose.

Please confirm your consent to this processing by checking the box below.

(If you do not agree to this processing, please inform the event organiser (the person who posted the event text in the WhatsApp group) and you can still sign up for the event in another way.)
"""
            try:
                with st.spinner("Formular wird erstellt..."):
                    form_edit_url = create_form_final_version_with_drive_title(
                        event_title=event_title,
                        event_price_for_form_question=event_price_input, 
                        form_description_text=full_form_description,
                        credentials=creds
                    )
                st.success(f"✅ Formular '{event_title}' erstellt!")
                st.markdown(f"👉 [Formular bearbeiten]({form_edit_url})")
                
                form_view_url = form_edit_url.replace('/edit', '/viewform') if form_edit_url else "FEHLER"
                whatsapp_message = f"""🚀 *{event_title}* 🚀
{event_specific_text_input}
📅 *Event-Date:* {event_date_time_input}
💵 *Price:* {event_price_input} 
🏡 *Location:* {event_location_input}
Register here: {form_view_url} 
See you there! ✨
Your International Club Team"""
                st.write("---"); st.subheader("📣 Invitation for WhatsApp:"); st.code(whatsapp_message, language="markdown")
            except ValueError as ve: st.error(f"Fehler: {ve}")
            except Exception as e: st.error(f"Unerwarteter Fehler: {type(e).__name__} - {e}")


elif menu_selection == "✍️ Unterschriften sammeln & QR": 
    st.subheader("✍️ Unterschriften Management & QR-Code")
    tab_qr, tab_sign_admin_view = st.tabs(["🔲 QR-Code für Event erstellen", "✍️ Unterschriften verwalten (Admin)"])

    with tab_qr:
        st.markdown("#### QR-Code für Unterschriftenseite generieren")
        st.info("Teilnehmer scannen diesen Code, um direkt zur Unterschriftenseite zu gelangen (ohne Menü).")
        sheet_link_qr = st.text_input(
            "📌 Link zum Google Sheet der Formularantworten", 
            placeholder="https://docs.google.com/spreadsheets/d/ID/edit", 
            key="qr_sheet_link_qr_v11"
        )
        if st.button("QR-Code generieren", key="btn_generate_qr_qr_v11"):
            if sheet_link_qr:
                extracted_id = extract_sheet_id(sheet_link_qr) 
                if not extracted_id: st.error("❌ Ungültiger Google Sheet Link!")
                else:
                    try:
                        img_base64 = generate_custom_qr_code_base64(extracted_id, BASE_URL) 
                        st.success("✅ QR-Code generiert!")
                        st.image(f"data:image/png;base64,{img_base64}", caption="QR-Code für Unterschriftenseite")
                        st.markdown(f"Der QR-Code verlinkt auf: `{BASE_URL}?page=sign&sheet_id={extracted_id}`")
                    except Exception as e: st.error(f"Fehler QR: {e}")
            else: st.warning("Bitte Link zum Google Sheet eingeben!")

    with tab_sign_admin_view:
        st.markdown("#### Unterschriften erfassen/verwalten (Admin-Ansicht)")
        st.info("Diese Ansicht ist für Organisatoren gedacht und zeigt das normale App-Layout.")
        
        if 'participants_df' not in st.session_state or st.session_state.participants_df.empty:
            st.markdown("##### Teilnehmerliste für Admin-Ansicht laden:")
            st.caption("Lade hier die Liste, wenn sie nicht bereits über den QR-Code-Workflow oder 'Teilnehmerliste & PDF Management' geladen wurde.")
            admin_sheet_link = st.text_input("Link zum Google Sheet (für Admin-Ansicht)", key="admin_sign_sheet_link_v11")
            if st.button("Liste für Admin-Ansicht laden", key="admin_sign_load_btn_v11"):
                if admin_sheet_link:
                    admin_sheet_id = extract_sheet_id(admin_sheet_link)
                    if admin_sheet_id:
                        admin_sheet_url = f"https://docs.google.com/spreadsheets/d/{admin_sheet_id}/edit"
                        with st.spinner("Lade Teilnehmer..."):
                            df_temp = load_participants_from_google_sheet(admin_sheet_url)
                            if not df_temp.empty:
                                st.session_state.participants_df = process_dataframe_for_display(df_temp)
                                st.success("Teilnehmerliste für Admin-Ansicht geladen.")
                                st.rerun()
                            else: st.error("Konnte keine Daten laden.")
                    else: st.error("Ungültiger Link.")
                else: st.warning("Bitte Link eingeben.")
        
        if 'participants_df' in st.session_state and not st.session_state.participants_df.empty:
            capture_signature(st.session_state.participants_df) 
        else:
            st.info("Bitte Teilnehmerliste laden, um Unterschriften zu erfassen/verwalten.")

# Ersetzen Sie den kompletten elif-Block in Ihrer main.py

elif menu_selection == "📄 Teilnehmerliste & PDF Management":
    st.subheader("📄 Teilnehmerliste laden, anzeigen und als PDF exportieren")

    st.markdown("#### Schritt 1: Teilnehmerliste laden oder aktualisieren")
    
    col1_load, col2_load = st.columns(2)
    with col1_load:
        st.markdown("##### Option A: Von Google Sheet laden")
        sheet_link_import = st.text_input(
            "Link zum Google Sheet der Formularantworten", 
            placeholder="https://docs.google.com/spreadsheets/d/ID/edit", 
            key="tl_sheet_link_import_tlpdfm_v1" 
        )
        if st.button("Von Google Sheet laden", key="btn_tl_load_gsheet_tlpdfm_v1"): 
            if sheet_link_import:
                with st.spinner("Lade und verarbeite Daten von Google Sheets..."):
                    try:
                        temp_df_google = load_participants_from_google_sheet(sheet_link_import) 
                        if not temp_df_google.empty:
                            st.session_state.participants_df = process_dataframe_for_display(temp_df_google)
                            st.success("✅ Teilnehmerliste erfolgreich geladen!")
                            st.rerun()
                        else:
                            st.warning("Google Sheet ist leer oder enthält keine relevanten Daten.")
                    except Exception as e:
                        st.error(f"Fehler beim Laden von Google Sheet: {e}")
            else:
                st.warning("Bitte einen Google Sheet Link eingeben.")
    
    with col2_load:
        st.markdown("##### Option B: Aus CSV-Datei hochladen")
        uploaded_csv_file = st.file_uploader(
            "Eigene Teilnehmer-CSV-Datei hochladen", 
            type=["csv"],
            key="tl_csv_uploader_tlpdfm_v1" 
        )
        if uploaded_csv_file is not None:
            try:
                with st.spinner("Verarbeite hochgeladene CSV..."):
                    df_from_upload = pd.read_csv(uploaded_csv_file, dtype=str).fillna('')
                    st.session_state.participants_df = process_dataframe_for_display(df_from_upload)
                    st.success("✅ Teilnehmerliste erfolgreich aus CSV verarbeitet!")
                    st.rerun()
            except Exception as e:
                st.error(f"Fehler beim Verarbeiten der CSV: {e}")

    st.markdown("---")

    # --- ANZEIGE UND PDF-LOGIK BEGINNT HIER ---
    if 'participants_df' in st.session_state and not st.session_state.participants_df.empty:
        st.subheader("Aktuell geladene Teilnehmerliste:")
        st.dataframe(st.session_state.participants_df)
        st.metric("Anzahl Teilnehmer in aktueller Liste", len(st.session_state.participants_df))
        
        st.markdown("---")
        st.subheader("Schritt 2: PDF Teilnehmerliste erstellen")

        df_for_pdf = st.session_state.participants_df.copy()
        
        # Duplikatentfernung
        num_before = len(df_for_pdf)
        df_for_pdf.drop_duplicates(subset=['Name', 'Email'], keep='first', inplace=True)
        num_after = len(df_for_pdf)
        if num_before > num_after:
            st.info(f"{num_before - num_after} Duplikat(e) entfernt. PDF wird mit {num_after} eindeutigen Teilnehmern erstellt.")

        # === Logik für die "Paid"-Liste ===
        unpaid_list = [
            "Ginny Lin", "YunYen Chang", "Matteo Paladini", "Max Theriot", 
            "Juan Esteban Alvarez Garcia", "Hoang Ha Luong", "Tara Ivers", 
            "Thomas Knörzer", "Federico  Tovoli", "Mingyu Kim", "Alberto Dávila Rodríguez", 
            "Julius Krüger", "Lucía Núñez", "Donovan Mougenot", "Tobias Billow", 
            "Zhibek Abdykalykova", "Anthony Dulon", "Cemre Saltan", "Carolina  Ahrens ", 
            "süeda barut", "Grace O Connor", "Jordan Benefield", "Anastasiia Burdym", 
            "Moritz Kraus", "Alexandra Lapunova", "Anika Hochreiter", "Hugo Talens", 
            "Barbara Borsini", "Jimmy Tan", "Adrià Ferrer Casamayor", "Paula Lorente", "Matteo  Paladini"
        ]
        normalized_unpaid_set = {name.strip().lower() for name in unpaid_list}
        all_participant_names = df_for_pdf['Name'].tolist()
        paid_list = [
            name for name in all_participant_names 
            if name.strip().lower() not in normalized_unpaid_set
        ]
        
        # UI für PDF-Details
        col_pdf1, col_pdf2 = st.columns(2)
        with col_pdf1:
            pdf_event_name = st.text_input("Event-Name für PDF", st.session_state.get("pdf_event_name_val", ""))
            pdf_event_date = st.text_input("Datum für PDF", st.session_state.get("pdf_event_date_val", ""))
        with col_pdf2:
            default_tutors = ", ".join(df_for_pdf[df_for_pdf['Type'].str.upper() == 'TUTOR']['Name'].unique())
            pdf_tutors = st.text_input("Tutoren für PDF", st.session_state.get("pdf_tutors_val", default_tutors))
            pdf_price = st.text_input("Preis für PDF", st.session_state.get("pdf_price_val", ""))
            
        if st.button("PDF generieren", key="btn_create_pdf_with_paid_logic"):
            try:
                participants_list_for_pdf = df_for_pdf.to_dict(orient="records")
                pdf_filename = os.path.join("output", f"Teilnehmerliste_{pd.Timestamp.now().strftime('%Y%m%d%H%M')}.pdf")
                
                generate_participant_pdf(
                    participants=participants_list_for_pdf, 
                    filename=pdf_filename, 
                    event_name=pdf_event_name,
                    event_date=pdf_event_date, 
                    event_tutors=pdf_tutors, 
                    event_price=pdf_price,
                    paid_list=paid_list 
                )
                st.success(f"✅ PDF '{os.path.basename(pdf_filename)}' erstellt!")
                with open(pdf_filename, "rb") as fp:
                    st.download_button("Download PDF", fp, os.path.basename(pdf_filename), "application/pdf")
            except Exception as e:
                st.error(f"PDF Fehler: {type(e).__name__} - {e}")
    else:
        st.info("Die Teilnehmerliste ist leer. Bitte lade zuerst eine Liste.")

        df_for_pdf_display = st.session_state.participants_df.copy()
        
        # --- DUPLIKATENTFERNUNG FÜR DIE ANZEIGE UND PDF ---
        num_before_dedup = len(df_for_pdf_display)
        if 'Name' in df_for_pdf_display.columns and 'Email' in df_for_pdf_display.columns:
            print(f"DEBUG (PDF): Entferne Duplikate basierend auf Name und Email. Vorher: {num_before_dedup} Zeilen")
            df_for_pdf_display.drop_duplicates(subset=['Name', 'Email'], keep='first', inplace=True)
            num_after_dedup = len(df_for_pdf_display)
            if num_before_dedup > num_after_dedup:
                 st.info(f"{num_before_dedup - num_after_dedup} Duplikat(e) entfernt. Finale PDF mit {num_after_dedup} eindeutigen Teilnehmern (basierend auf Name & Email).")
            else:
                st.info(f"Keine Duplikate (basierend auf Name & Email) gefunden. PDF mit {num_after_dedup} Teilnehmern.")
            print(f"DEBUG (PDF): Nach Duplikatentfernung (Name & Email): {num_after_dedup} Zeilen")
        elif 'Name' in df_for_pdf_display.columns: # Fallback, falls 'Email' nicht da ist
            print(f"WARNUNG (PDF): Email-Spalte nicht im DataFrame. Duplikate nur nach Name entfernt (potenziell ungenau).")
            df_for_pdf_display.drop_duplicates(subset=['Name'], keep='first', inplace=True)
            num_after_dedup = len(df_for_pdf_display)
            if num_before_dedup > num_after_dedup:
                st.info(f"{num_before_dedup - num_after_dedup} Duplikat(e) (nur nach Name) entfernt. Finale PDF mit {num_after_dedup} Teilnehmern.")
            else:
                 st.info(f"Keine Duplikate (nur nach Name) gefunden. PDF mit {num_after_dedup} Teilnehmern.")
            print(f"DEBUG (PDF): Nach Duplikatentfernung (nur Name): {num_after_dedup} Zeilen")

        st.info(f"PDF wird für {len(df_for_pdf_display)} eindeutige(n) Teilnehmer erstellt.")
        
        # UI für PDF-Details
        pdf_event_name = st.text_input("Event-Name für PDF", st.session_state.get("pdf_event_name_val", ""), key="pdf_event_name_dedup_v1")
        pdf_event_date = st.text_input("Datum für PDF", st.session_state.get("pdf_event_date_val", ""), key="pdf_event_date_dedup_v1")
        
        # Tutoren-String aus dem DataFrame generieren, wenn nicht manuell eingegeben
        default_tutors_list = []
        if 'Name' in df_for_pdf_display.columns and 'Type' in df_for_pdf_display.columns:
            default_tutors_list = df_for_pdf_display[df_for_pdf_display['Type'].str.upper() == 'TUTOR']['Name'].tolist()
        default_tutors_str = ", ".join(filter(None, default_tutors_list))
        
        pdf_event_tutors = st.text_input("Tutoren für PDF", st.session_state.get("pdf_tutors_val", default_tutors_str), key="pdf_event_tutors_dedup_v1")
        pdf_event_price = st.text_input("Preis für PDF", st.session_state.get("pdf_price_val", ""), key="pdf_event_price_dedup_v1")
        
        st.session_state.pdf_event_name_val = pdf_event_name
        st.session_state.pdf_event_date_val = pdf_event_date
        st.session_state.pdf_tutors_val = pdf_event_tutors
        st.session_state.pdf_price_val = pdf_event_price

        if st.button("PDF erstellen mit eindeutigen Teilnehmern", key="btn_create_pdf_dedup_v1"):
            try:
                participants_list = df_for_pdf_display.to_dict(orient="records")
                
                event_prefix = "".join(filter(str.isalnum, pdf_event_name or "Event"))
                pdf_filename = os.path.join("output", f"Teilnehmerliste_{event_prefix}_{pd.Timestamp.now().strftime('%Y%m%d%H%M')}.pdf")
                
                generate_participant_pdf(
                    participants_list, filename=pdf_filename, event_name=pdf_event_name,
                    event_date=pdf_event_date, event_tutors=pdf_event_tutors, event_price=pdf_event_price
                )
                st.success(f"✅ PDF: '{pdf_filename}' erstellt!");
                with open(pdf_filename, "rb") as fp_pdf:
                    st.download_button("Download PDF", fp_pdf, os.path.basename(pdf_filename), "application/pdf", key="dl_pdf_dedup_v1")
            except Exception as e: 
                st.error(f"PDF Fehler: {type(e).__name__} - {e}")
                print(f"FEHLER (PDF Erstellung): {e}")

elif menu_selection == "🧾 Abrechnung & Bericht einreichen":
    st.subheader("🧾 Bericht generieren & Abrechnnung einreichen")
    st.markdown("Bitte lade hier alle notwendigen Dokumente für die Event-Abrechnung hoch und erstelle/lade den Erfahrungsbericht hoch.")

    submission_event_name = st.text_input(
        "Event-Name (für Dateinamen der Abrechnung)", 
        placeholder="z.B. Ausflug_Allianz_Arena_Mai2025",
        key="sub_event_name_v8"
    )
    st.caption("Wird für die Benennung des ZIPs und des Erfahrungsberichts verwendet.")

    st.markdown("---")
    st.markdown("#### 1. Erforderliche Dokumente hochladen:")
    uploaded_participant_list = st.file_uploader("Teilnehmerliste...", key="sub_participants_v8")
    uploaded_settlement_form = st.file_uploader("Abrechnungsformular (PDF)", key="sub_settlement_v8")
    uploaded_invoice_files = st.file_uploader("Rechnungsbelege...", accept_multiple_files=True, key="sub_invoices_v8")


    st.markdown("---")
    st.markdown("#### 2. Erfahrungsbericht:")
    
    report_option = st.radio(
        "Wie möchtest du den Erfahrungsbericht bereitstellen?",
        ("KI-Bericht generieren lassen", "Eigenen Bericht hochladen (.docx, .pdf, .txt)"),
        key="sub_report_option_v8"
    )

    if report_option == "KI-Bericht generieren lassen":
        tutor_freitext = st.text_area(
            "Dein Freitext für den Erfahrungsbericht:", 
            height=200, 
            key="sub_freitext_ki_v8",
            placeholder="Beschreibe hier den Ablauf des Events..."
        )
        if st.button("Erfahrungsbericht erstellen", key="btn_gen_exp_report_ki_v8"):
            if tutor_freitext and submission_event_name:
                with st.spinner("Generiere Erfahrungsbericht..."):
                    report_filename_in_zip = f"Erfahrungsbericht_{submission_event_name.replace(' ','_')}.docx"
                    report_bytes = generate_experience_report_docx(tutor_freitext, submission_event_name)
                    if report_bytes:
                        st.session_state.final_report_data_for_zip = {"name": report_filename_in_zip, "bytes": report_bytes}
                        st.session_state.uploaded_experience_report_file = None
                        st.success(f"Bericht generiert!")
                        st.download_button("Bericht herunterladen", report_bytes, report_filename_in_zip, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")
                    else:
                        st.error("KI-Bericht konnte nicht generiert werden.")
            else:
                st.warning("Bitte Event-Namen und Freitext eingeben.")
    
    elif report_option == "Eigenen Bericht hochladen (.docx, .pdf, .txt)":
        uploaded_manual_report = st.file_uploader(
            "Deinen fertigen Erfahrungsbericht hochladen",
            type=['docx', 'pdf', 'txt'],
            key="sub_manual_report_upload_v8"
        )
        if uploaded_manual_report is not None:
            safe_report_name = "".join(x for x in uploaded_manual_report.name if x.isalnum() or x in " ._-").strip()
            final_report_name = f"Erfahrungsbericht_{safe_report_name}"

            st.session_state.final_report_data_for_zip = {"name": final_report_name, "bytes": uploaded_manual_report.getvalue()}
            st.session_state.uploaded_experience_report_file = uploaded_manual_report
            st.success(f"Manueller Bericht '{uploaded_manual_report.name}' wurde hochgeladen und für das ZIP vorgemerkt als '{final_report_name}'.")
            st.session_state.generated_report_for_submission = None

    if st.session_state.get('final_report_data_for_zip'):
        st.info(f"Für das ZIP-Archiv wird der Bericht '{st.session_state.final_report_data_for_zip['name']}' verwendet.")


    st.markdown("---")
    st.markdown("#### 3. Abrechnung finalisieren & abschicken:")
    if st.button("Alle Unterlagen als ZIP packen", key="btn_create_submission_zip_v8"):
        report_to_zip = st.session_state.get('final_report_data_for_zip')
        if not submission_event_name: st.warning("Event-Name fehlt.")
        elif not uploaded_participant_list: st.warning("Teilnehmerliste fehlt.")
        elif not uploaded_settlement_form: st.warning("Abrechnungsformular fehlt.")
        elif not report_to_zip: st.warning("Erfahrungsbericht fehlt (bitte generieren oder hochladen).")
        else:
            with st.spinner("Erstelle ZIP-Datei..."):
                zip_path = create_submission_zip(
                    event_name=submission_event_name,
                    participant_list_file=uploaded_participant_list,
                    invoice_files=uploaded_invoice_files if uploaded_invoice_files else [],
                    settlement_form_file=uploaded_settlement_form,
                    experience_report_content=report_to_zip["bytes"],
                    experience_report_filename=report_to_zip["name"] 
                )
                if zip_path:
                    st.session_state.generated_zip_path = zip_path
                    st.success(f"ZIP-Datei '{os.path.basename(zip_path)}' erstellt!")
                else: st.error("ZIP konnte nicht erstellt werden.")
    
    if st.session_state.get('generated_zip_path') is not None: 
        st.markdown("---")
        st.markdown(f"Die ZIP-Datei **'{os.path.basename(st.session_state.generated_zip_path)}'** ist bereit für den Upload.")
        
        if st.button("ZIP nach Google Drive hochladen & E-Mail senden", key="btn_upload_notify_final_submit"):
            current_submission_event_name = submission_event_name

            if not current_submission_event_name:
                st.error("Event-Name für den Upload fehlt. Bitte oben eingeben.")
            else:
                with st.spinner("Lade ZIP hoch und sende E-Mail..."):
                    drive_file_link = upload_zip_to_drive(st.session_state.generated_zip_path, current_submission_event_name)
                    if drive_file_link: 
                        email_sent = send_email_notification(
                            recipient_email="isa.simmet@gmx.de", 
                            event_name=current_submission_event_name,
                            drive_link=drive_file_link
                        )
                        if email_sent:
                            st.balloons()
                            st.success("Abrechnungspaket erfolgreich hochgeladen und E-Mail Benachrichtigung gesendet!")
                            st.session_state.generated_zip_path = None 
                            st.session_state.final_report_data_for_zip = None
                            st.rerun()
                        else:
                            st.error("E-Mail Benachrichtigung konnte nicht gesendet werden (Upload zu Drive war ggf. erfolgreich).")
                    else:
                        st.error("Fehler beim Upload der ZIP-Datei nach Google Drive.")