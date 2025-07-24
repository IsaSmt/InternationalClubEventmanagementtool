# modules/qr_generator.py
import qrcode
import io
import base64
import os 
from PIL import Image

# --- Hauptfunktion zur QR-Code-Generierung ---
def generate_custom_qr_code_base64(sheet_id: str, base_url: str) -> str:
    """
    'sheet_id' und eine 'base_url' werden der Methode übergeben.
    Ziel ist es, einen QR-Code zu generieren, der auf eine spezifische Seite
    meiner Streamlit-App verlinkt und dabei die 'sheet_id' als Parameter mitgibt.
    Das Ergebnis ist ein Base64-String, den Streamlit direkt als Bild anzeigen kann.
    """

    # Überprüfung
    if not sheet_id:
        raise ValueError("Sheet ID darf nicht leer sein.")
    if not base_url:
        raise ValueError("Base URL darf nicht leer sein.")
        
    # URL bauen
    target_url = f"{base_url}?page=sign&sheet_id={sheet_id}"

    # QRCode-Objekt initialisieren
    qr = qrcode.QRCode(
        version=None,
        error_correction=qrcode.constants.ERROR_CORRECT_M, 
        box_size=10,
        border=4,
    )
    
    # URL wird QR-Code als Daten übergeben
    qr.add_data(target_url)
    qr.make(fit=True)

    # Bildobjekt erstellen.
    img = qr.make_image(fill_color="black", back_color="white")

    # Bild über 'io.BytesIO' als Datenstrom weitergeben.
    buffered = io.BytesIO()
    img.save(buffered, format="PNG")
    img_bytes = buffered.getvalue()
    
    # Bild-Bytes in Base64-String umwandeln
    return base64.b64encode(img_bytes).decode('utf-8')

# --- Testblock für die direkte Ausführung des Moduls ---
if __name__ == "__main__":
    # Zur Ausführung mit 'python modules/qr_generator.py' und isolierter Testung der Funktion.

    print("Starte Testlauf für modules/qr_generator.py...")

    # Testwerte definieren.
    test_sheet_id = "1a0v1_UqtKVNEfH9oikzBYMtayPsIZHh8Hw4j-ZUCJTEST" 
    test_base_url = "http://localhost:8501" #localhost für lokale Tests ohne Streamlit-Server.
    
    print(f"\nGeneriere QR-Code für:")
    print(f"  Sheet ID: {test_sheet_id}")
    print(f"  Base URL: {test_base_url}")
    expected_target_url = f"{test_base_url}?page=sign&sheet_id={test_sheet_id}"
    print(f"  Erwartete Ziel-URL im QR-Code: {expected_target_url}")

    try:
        # Hauptfunktion mit Testdaten aufrufen.
        base64_string = generate_custom_qr_code_base64(test_sheet_id, test_base_url)
        
        # Ergebnis prüfen (nicht leer und ein String).
        if base64_string and isinstance(base64_string, str) and len(base64_string) > 50:
            print("\nTEST ERFOLGREICH: QR-Code als Base64-String generiert.")
            # print(f"  Base64 String (erste 50 Zeichen): {base64_string[:50]}...")

            # Mit Pillow-Bibliothek (PIL) Base64-String in ein Bild umzuwandeln und als PNG-Datei speichern.
            try:
                image_data = base64.b64decode(base64_string) # Base64 zurück zu Bytes
                image = Image.open(io.BytesIO(image_data))   # Bytes in ein Pillow-Bildobjekt laden
                
                output_dir = "output" # Im output-Ordner speichern.
                if not os.path.exists(output_dir):
                    os.makedirs(output_dir) # Ordner erstellen, falls er nicht da ist.
                
                filename = os.path.join(output_dir, "test_qr_code_from_qr_generator.png")
                image.save(filename) # Bild speichern
                print(f"  INFO: QR-Code wurde erfolgreich als '{filename}' gespeichert.")
                print("  Bitte öffne diese Datei, um den QR-Code mit einer Scanner-App zu überprüfen.")
                print(f"  Er sollte auf die URL '{expected_target_url}' verlinken.")
            except Exception as e_save:
                # Falls das Speichern fehlschlägt (z.B. Pillow nicht installiert), gibt's eine Warnung.
                print(f"  WARNUNG: Konnte den generierten QR-Code nicht als Bilddatei speichern: {e_save}")
        else:
            print("\nFEHLER im Test: Generierter Base64-String ist ungültig oder zu kurz.")

    except ValueError as ve: # Fängt die ValueErrors ab, die meine Funktion werfen kann.
        print(f"\nVALIDIERUNGSFEHLER im Test: {ve}")
    except Exception as e_global: # Fängt alle anderen unerwarteten Fehler ab.
        print(f"\nEIN UNERWARTETER FEHLER ist im Test aufgetreten: {type(e_global).__name__} - {e_global}")

    print("\nTestlauf für modules/qr_generator.py beendet.")