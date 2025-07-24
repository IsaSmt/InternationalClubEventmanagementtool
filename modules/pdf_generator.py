from fpdf import FPDF
import os
import pandas as pd

def sanitize_string_for_pdf(text: str, font_encoding: str = 'latin-1') -> str:
    """
    Entfernt oder ersetzt Zeichen in einem String, die von einer bestimmten
    Schriftart-Kodierung (wie FPDFs Standard 'latin-1') nicht unterstützt werden.
    Gibt einen "sicheren" String zurück.
    """
    if not isinstance(text, str):
        return ""
    return text.encode(font_encoding, 'replace').decode(font_encoding)

# Layout-Konstanten
COL_WIDTHS = {
    "nr": 8, "name": 60, "mobile": 35, "country": 30, "erasmus": 22,
    "other_exch": 22, "tutor": 15, "signature": 40, "paid": 12,
    "present": 14, "absent": 12,
}
ROW_HEIGHT_PARTICIPANT = 8 
DEFAULT_FONT_SIZE_TABLE = 7 
DEFAULT_FONT_SIZE_HEADER_DETAILS = 10
DEFAULT_FONT_SIZE_TITLE = 16
DEFAULT_FONT_SIZE_INFOTEXT = 7
PARTICIPANTS_PER_PAGE = 15 
FONT_NAME = "DejaVu"  # Standard-Schriftart für FPDF
FALLBACK_FONT_NAME = "Arial"

class TeilnehmerlistePDF(FPDF):

    # Konstruktor
    def __init__(self, event_name=None, event_date=None, event_tutors=None, event_price=None):
        super().__init__('L', 'mm', 'A4')
        self.event_name_val = str(event_name) if event_name else "" 
        self.event_date_val = str(event_date) if event_date else ""
        self.event_tutors_val = str(event_tutors) if event_tutors else ""
        self.event_price_val = str(event_price) if event_price else ""
        self.page_margin = 10
        self.set_margins(self.page_margin, self.page_margin, self.page_margin)
        
        font_dir = "fonts"; font_file_regular = "DejaVuSans.ttf"; font_file_bold = "DejaVuSans-Bold.ttf"
        font_path_regular = os.path.join(font_dir, font_file_regular)
        font_path_bold = os.path.join(font_dir, font_file_bold)
        font_loaded = False
        try:
            if os.path.exists(font_path_regular) and os.path.exists(font_path_bold):
                self.add_font(FONT_NAME, '', font_path_regular, uni=True)
                self.add_font(FONT_NAME, 'B', font_path_bold, uni=True) 
                self.current_font_family = FONT_NAME
                font_loaded = True
        except RuntimeError as e: print(f"WARNUNG (PDF): Konnte Schriftart nicht laden: {e}.")
        
        if not font_loaded:
            print(f"INFO (PDF): Verwende Fallback-Schriftart '{FALLBACK_FONT_NAME}'. Unicode-Zeichen werden ggf. nicht korrekt dargestellt.")
            self.current_font_family = FALLBACK_FONT_NAME
        
        self.set_font(self.current_font_family, '', 10)
        self.set_auto_page_break(auto=True, margin=self.page_margin + 5) 
        self.alias_nb_pages() 
        self.current_y_after_header_block = 0

    # Header-Methode.
    def header(self):
        prev_font_family = self.font_family
        prev_font_style = self.font_style
        prev_font_size = self.font_size

        data_dir = "data"; logo_file = "I-CLUB_LOGO.png"; logo_path = os.path.join(data_dir, logo_file)
        logo_x = self.page_margin; logo_y = self.page_margin - 2; logo_w = 25 
        if os.path.exists(logo_path):
            try: self.image(logo_path, logo_x, logo_y, logo_w)
            except Exception:
                self.set_xy(logo_x, logo_y); self.set_font(self.current_font_family, 'B', 8); self.cell(logo_w, 10, '[Logo Fehler]', 0, 0, 'C')
        else: 
            self.set_xy(logo_x, logo_y); self.set_font(self.current_font_family, 'B', 8); self.cell(logo_w, 10, '[Logo fehlt]', 0, 0, 'C')
        
        self.set_font(self.current_font_family, 'B', DEFAULT_FONT_SIZE_TITLE); self.set_y(logo_y) 
        self.cell(0, 10, 'Participant List / Teilnehmerliste', 0, 1, 'C') 
        
        self.set_font(self.current_font_family, '', DEFAULT_FONT_SIZE_HEADER_DETAILS)
        current_y_after_title = self.get_y(); event_details_x_start = logo_x + logo_w + 5 
        
        header_field_height = 7; label_width = 20 
        event_name_value_width = 100; date_value_width = 70; tutors_value_width = 100
        price_label_w = 15; price_value_w = 25 

        self.set_xy(event_details_x_start, current_y_after_title)
        self.cell(label_width, header_field_height, 'Event:', 0, 0, 'L') 
        self.cell(event_name_value_width, header_field_height, self.event_name_val, 'B', 0, 'L') 
        self.set_x(self.w - self.page_margin - price_value_w - price_label_w) 
        self.cell(price_label_w, header_field_height, 'Price:', 0, 0, 'R') 
        self.cell(price_value_w, header_field_height, self.event_price_val, 'B', 1, 'L') 

        self.set_x(event_details_x_start) 
        self.cell(label_width, header_field_height, 'Date:', 0, 0, 'L')
        self.cell(date_value_width, header_field_height, self.event_date_val, 'B', 1, 'L') 

        self.set_x(event_details_x_start)
        self.cell(label_width, header_field_height, 'Tutors:', 0, 0, 'L')
        self.cell(tutors_value_width, header_field_height, self.event_tutors_val, 'B', 1, 'L') 
        self.ln(3) 

        self.set_font(self.current_font_family, '', DEFAULT_FONT_SIZE_INFOTEXT)
        infotext = (
            "People who signed up and paid do not get their money back. You are responsible for selling the ticket yourself.\n\n"
            "With your signature you confirm that you approve of the International Club publishing fotos and videos of you or with you on them on social media and tag you.\n"
            "If you do not agree, let one of the organizers know and we will note it on this list. The International Club commits on its part to use the fotos and videos purely "
            "for marketing purposes that do not violate a person's privacy and dignity."
        )
        self.set_x(self.page_margin); self.multi_cell(0, 3.5, infotext, 0, 'L'); self.ln(2) 
        self.current_y_after_header_block = self.get_y()
        self.add_table_header()
        
        self.set_font(prev_font_family, prev_font_style, prev_font_size)

    # Footer-Methode.
    def footer(self):
        self.set_y(-(self.page_margin + 5))
        self.set_font(self.current_font_family, '', 10)
        self.cell(0, 10, 'Unterschrift organisierender Tutor: ___________________________', 0, 0, 'L')
        self.set_font(self.current_font_family, '', 8)
        self.cell(0, 10, f'Seite {self.page_no()}/{{nb}}', 0, 0, 'R') 

    # Tabellen-Methode:
    def add_table_header(self):
        self.set_y(self.current_y_after_header_block) 
        self.set_x(self.page_margin)
        self.set_font(self.current_font_family, 'B', DEFAULT_FONT_SIZE_TABLE + 1) 
        self.set_fill_color(220, 220, 220); self.set_line_width(0.2)
        headers = ["Nr.", "Name", "Mobile", "Country", "ERASMUS", "Other Exch.", "Tutor", "Signature", "Paid", "Present", "Absent"]
        col_keys = ["nr", "name", "mobile", "country", "erasmus", "other_exch", "tutor", "signature", "paid", "present", "absent"]
        for i, header_text in enumerate(headers): 
            self.cell(COL_WIDTHS[col_keys[i]], 7, header_text, 1, 0, 'C', fill=True)
        self.ln()

    # Teilnehmerzeile zur PDF hinzufügen.   
    def add_participant_row(self, idx, name, mobile, country, p_type, is_paid=False):
        self.set_x(self.page_margin)
        self.set_font(self.current_font_family, '', DEFAULT_FONT_SIZE_TABLE)
        self.set_line_width(0.2)
        
        encoding_to_use = 'latin-1' if self.current_font_family == FALLBACK_FONT_NAME else 'utf-8'

        name_str = sanitize_string_for_pdf(str(name if pd.notna(name) else ""), encoding_to_use)
        mobile_str = sanitize_string_for_pdf(str(mobile if pd.notna(mobile) else ""), encoding_to_use)
        country_str = sanitize_string_for_pdf(str(country if pd.notna(country) else ""), encoding_to_use)
        p_type_str_upper = str(p_type if pd.notna(p_type) else "").upper()
        
        is_erasmus = "X" if "ERASMUS" in p_type_str_upper else ""
        is_other_exchange = "X" if "OTHER" in p_type_str_upper or "FULL-TIME" in p_type_str_upper or "INTERNATIONAL STUDENT" in p_type_str_upper else ""
        is_tutor = "X" if "TUTOR" in p_type_str_upper else ""
        if "ERASMUS" in p_type_str_upper and ("OTHER" in p_type_str_upper or "FULL-TIME" in p_type_str_upper): 
            is_erasmus = ""

        safe_name_for_file = "".join(x for x in name_str if x.isalnum() or x in " _-").strip().replace(" ", "_")
        signature_path = os.path.join("signatures", f"{safe_name_for_file}.png")
        has_signature = os.path.exists(signature_path)
        
        present_val = ""
        absent_val = ""
        
        paid_val = "✔️" if is_paid else ""
        
        row_data_map = {"nr": str(idx), "name": name_str, "mobile": mobile_str, "country": country_str, "erasmus": is_erasmus, "other_exch": is_other_exchange, "tutor": is_tutor, "signature": "", "paid": paid_val, "present": present_val, "absent": absent_val}
        col_keys = list(COL_WIDTHS.keys())
        
        for key in col_keys:
            width = COL_WIDTHS[key]; text_val = row_data_map[key] 
            current_x_cell = self.get_x(); current_y_cell = self.get_y()
            if key == "signature" and has_signature:
                self.cell(width, ROW_HEIGHT_PARTICIPANT, '', 1, 0, 'C') 
                try: 
                    self.image(signature_path, x=current_x_cell + 1, y=current_y_cell + 1, w=width - 2, h=ROW_HEIGHT_PARTICIPANT - 2)
                except Exception:
                    pass 
            else:
                self.multi_cell(width, ROW_HEIGHT_PARTICIPANT, text_val, 1, 'C', fill=False)
                self.set_xy(current_x_cell + width, current_y_cell)
        self.ln(ROW_HEIGHT_PARTICIPANT)

# ENDE DER KLASSE

# Hauptfunktion zum Generieren der Teilnehmer-PDF.
# Ersetzen Sie die komplette Funktion am Ende Ihrer Date
# Ersetzen Sie die komplette Funktion am Ende Ihrer Datei

# Ersetzen Sie die komplette Funktion am Ende Ihrer Datei
# Ersetzen Sie diese komplette Funktion in Ihrer pdf_generator.py

def generate_participant_pdf(participants: list, filename="output/Teilnehmerliste.pdf",
                             event_name=None, event_date=None, event_tutors=None, event_price=None,
                             paid_list: list = None):
    """
    Erzeugt eine PDF-Teilnehmerliste mit korrekten Seitenumbrüchen.
    Kreuzt 'Paid' an für Teilnehmer in der 'paid_list'.
    Trennt 'Nothing of the above' sauber auf eine neue Seite.
    """
    os.makedirs("output", exist_ok=True)

    if paid_list is None:
        paid_list = []
    # Normalisiert die Namen in der "paid_list" für einen robusten Abgleich
    normalized_paid_set = {str(name).strip().lower() for name in paid_list}

    if not participants:
        participants = []

    # Teilnehmer in zwei Gruppen aufteilen
    regular_participants = []
    special_participants = []
    for p in participants:
        # Hier wird der saubere, interne Schlüssel "Type" erwartet
        p_type_val = p.get("Type", "").strip().lower()
        if p_type_val == "nothing of the above":
            special_participants.append(p)
        else:
            regular_participants.append(p)

    # Tutoren-String automatisch generieren, falls nicht manuell übergeben
    final_tutors_string = event_tutors
    if event_tutors is None:
        tutor_names_list = [p.get("Name", "") for p in participants if str(p.get("Type", "")).upper() == "TUTOR"]
        final_tutors_string = ", ".join(filter(None, tutor_names_list)) if tutor_names_list else ""

    pdf = TeilnehmerlistePDF(event_name=event_name, event_date=event_date,
                             event_tutors=final_tutors_string, event_price=event_price)
    
    # --- HILFSFUNKTION FÜR KORREKTES HINZUFÜGEN VON TEILNEHMERGRUPPEN ---
    def add_participant_group_to_pdf(participant_list, start_index=1):
        for i, person_dict in enumerate(participant_list):
            # PRÜFUNG FÜR SEITENUMBRUCH:
            # Passt noch eine weitere Zeile auf die Seite, bevor wir den unteren Rand erreichen?
            # pdf.h = Seitenhöhe, pdf.b_margin = unterer Rand.
            if pdf.get_y() > (pdf.h - pdf.b_margin - ROW_HEIGHT_PARTICIPANT * 2):
                 pdf.add_page() # FPDF fügt automatisch einen neuen Header hinzu.
            
            # Daten aus dem Dictionary extrahieren
            name = person_dict.get("Name", "")
            mobile = person_dict.get("Mobile", "")
            country = person_dict.get("Country", "")
            p_type = person_dict.get("Type", "")
            
            # Prüfen, ob der Teilnehmer bezahlt hat
            has_paid = name.strip().lower() in normalized_paid_set
            
            # Teilnehmerzeile mit korrekter fortlaufender Nummerierung hinzufügen
            pdf.add_participant_row(start_index + i, name, mobile, country, p_type, is_paid=has_paid)

    # --- HAUPTLOGIK FÜR DIE PDF-ERSTELLUNG ---
    pdf.add_page() # Erste Seite explizit starten
    
    if regular_participants:
        add_participant_group_to_pdf(regular_participants, start_index=1)

    if special_participants:
        pdf.add_page() # Neue Seite für die spezielle Gruppe erzwingen
        
        # Titel für die spezielle Gruppe hinzufügen
        pdf.set_font(pdf.current_font_family, 'B', 12)
        pdf.cell(0, 10, 'Weitere Teilnehmer (Kategorie: "Nothing of the above")', 0, 1, 'C')
        pdf.ln(2)
        
        # Y-Position für den Tabellenkopf neu setzen, damit er unter dem Titel erscheint
        pdf.current_y_after_header_block = pdf.get_y()
        pdf.add_table_header() # Den Tabellenkopf manuell neu zeichnen
        
        # Die spezielle Gruppe mit Nummerierung ab 1 hinzufügen
        add_participant_group_to_pdf(special_participants, start_index=1)

    try:
        pdf.output(filename, 'F')
    except Exception as e:
        raise RuntimeError(f"Fehler beim Speichern der PDF '{filename}': {e}") from e

if __name__ == "__main__":
    print("Starte Testlauf für modules/pdf_generator.py...")
    
    test_participants_data = [
        {'Name': 'Max Mustermann PDF', 'Mobile': '0123', 'Country': 'DE', 'Type': 'ERASMUS', 'Email': 'max@pdf.test'},
        {'Name': 'Erika Musterfrau PDF', 'Mobile': '0456', 'Country': 'AT', 'Type': 'TUTOR', 'Email': 'erika@pdf.test'},
    ]

    os.makedirs("signatures", exist_ok=True)
    erika_safe_name = "Erika_Musterfrau_PDF"
    erika_sig_path = os.path.join("signatures", f"{erika_safe_name}.png")
    try:
        from PIL import Image as PILImage
        if not os.path.exists(erika_sig_path):
            dummy_sig_img = PILImage.new('RGB', (100, 50), color = 'white')
            dummy_sig_img.save(erika_sig_path)
            print(f"  INFO: Dummy-Signatur für Erika unter '{erika_sig_path}' erstellt.")
    except ImportError:
        print("  WARNUNG: Pillow nicht installiert, konnte keine Dummy-Signatur erstellen.")
    except Exception as e_img:
        print(f"  WARNUNG: Fehler beim Erstellen der Dummy-Signatur für Erika: {e_img}")

    test_pdf_filename = os.path.join("output", "TEST_Teilnehmerliste_Direkt.pdf")
    test_event_name = "PDF Direktaufruf Test Event"
    test_event_date = pd.Timestamp.now().strftime('%d.%m.%Y')
    test_event_tutors = "Erika Musterfrau"
    test_event_price = "6,50"

    print(f"\nGeneriere Test-PDF: '{test_pdf_filename}'")
    try:
        generate_participant_pdf(
            participants=test_participants_data,
            filename=test_pdf_filename,
            event_name=test_event_name,
            event_date=test_event_date,
            event_tutors=test_event_tutors,
            event_price=test_event_price
        )
        print(f"  TEST ERFOLGREICH: PDF '{test_pdf_filename}' sollte erstellt worden sein.")
        print("  Bitte überprüfe den Inhalt der PDF im 'output'-Ordner.")
    except Exception as e:
        print(f"  FEHLER bei der PDF-Generierung im Test: {e}")

    print("\nTestlauf für modules/pdf_generator.py beendet.")