# International Club Eventtool

Das Eventmanagement Tool für den International Club der Hochschule München ist eine Streamlit-Anwendung zur Unterstützung bei der Organisation und Verwaltung von Events des Clubs. Es umfasst Funktionen zur Erstellung von Google Forms für Anmeldungen, Generierung von QR-Codes für die Teilnehmererfassung, Erstellung von Teilnehmerlisten als PDF und einen Workflow zur Abrechnung von Events inklusive KI-gestützter Berichterstellung.

## Inhaltsverzeichnis
1.  [Voraussetzungen](#voraussetzungen)
2.  [Setup und Installation](#setup-und-installation)
    *   [Google Cloud Projekt und OAuth 2.0 (Erforderlich)](#google-cloud-projekt-und-oauth-20-erforderlich)
    *   [Ollama (Optional für KI-Berichtsfunktion)](#ollama-optional-für-ki-berichtsfunktion)
    *   [E-Mail-Benachrichtigung (Vorkonfiguriert)](#e-mail-benachrichtigung-vorkonfiguriert)
    *   [Lokales Setup](#lokales-setup)
3.  [Starten der Streamlit-Anwendung](#starten-der-streamlit-anwendung)
4.  [Funktionsübersicht der Streamlit-Anwendung](#funktionsübersicht-der-streamlit-anwendung)
5.  [Separates Testen der Module im Terminal](#separates-testen-der-module-im-terminal)
6.  [Projektstruktur](#projektstruktur)
7.  [Verwendete externe Bibliotheken](#verwendete-externe-bibliotheken)


## Voraussetzungen

*   Python 3.10 oder höher (entwickelt und getestet mit Python 3.12).
*   `pip` (Python package installer).
*   Ein moderner Webbrowser.
*   Ein Google Cloud Account und ein dediziertes Google-Konto (z.B. für den I-Club).
*   Ollama lokal installiert (optional, nur für die KI-Berichtsfunktion).

## Setup und Installation

### Google Cloud Projekt und OAuth 2.0 (Erforderlich)

Für die Interaktion mit Google Forms, Google Drive und Google Sheets verwendet die Anwendung **OAuth 2.0** und agiert im Namen eines echten Google-Kontos. Der alte Ansatz mit Service Accounts wurde aufgrund von API-Fehlern verworfen. Die folgende Einrichtung ist einmalig erforderlich.

1.  **Google Cloud Projekt:** Erstellen Sie ein neues Projekt in der [Google Cloud Console](https://console.cloud.google.com/) oder verwenden Sie ein bestehendes.

2.  **APIs aktivieren:** Aktivieren Sie die folgenden drei APIs für Ihr Projekt:
    *   **Google Forms API**
    *   **Google Drive API**
    *   **Google Sheets API**

3.  **OAuth-Zustimmungsbildschirm konfigurieren:**
    *   Navigieren Sie zu "APIs & Dienste" -> "OAuth-Zustimmungsbildschirm".
    *   **User Type:** Wählen Sie **"Extern"**.
    *   Füllen Sie die erforderlichen Felder aus (App-Name, E-Mail-Adressen).
    *   **Testnutzer:** Klicken Sie auf "+ ADD USERS" und fügen Sie die E-Mail-Adresse des Google-Kontos hinzu, das die App verwenden soll (z.B. die I-Club-Gmail-Adresse).

4.  **OAuth 2.0-Client-ID erstellen:**
    *   Navigieren Sie zu "APIs & Dienste" -> "Anmeldedaten".
    *   Klicken Sie auf "+ ANMELDEDATEN ERSTELLEN" -> "OAuth-Client-ID".
    *   **Anwendungstyp:** Wählen Sie **"Webanwendung"**.
    *   **Autorisierte Weiterleitungs-URIs:** Fügen Sie `http://localhost:8501` für die lokale Entwicklung hinzu.
    *   Klicken Sie auf "ERSTELLEN".
    *   Laden Sie die **JSON-Datei** herunter.

5.  **`client_secrets.json` platzieren:** Benennen Sie die heruntergeladene JSON-Datei in `client_secrets.json` um und platzieren Sie sie **im Hauptverzeichnis dieses Projekts.**

6.  **Google Drive Ordner-IDs anpassen:**
    *   Erstellen Sie eigene Ordner im Google Drive des authentifizierten Kontos und passen Sie deren IDs im Code an.
    *   In `modules/form_creator.py`: Passen Sie `GOOGLE_DRIVE_FOLDER_ID` an.
    *   In `modules/submission_handler.py`: Passen Sie `TARGET_DRIVE_FOLDER_ID` an.

### Ollama (Optional für KI-Berichtsfunktion)
Diese Funktion ist optional. Wenn Sie sie nutzen möchten:
1.  Installieren Sie Ollama von [https://ollama.com/](https://ollama.com/).
2.  Starten Sie die Ollama-Anwendung.
3.  Laden Sie das verwendete Sprachmodell herunter (Standard: `phi3:mini`):
    ```bash
    ollama pull phi3:mini
    ```

### E-Mail-Benachrichtigung (Vorkonfiguriert)
Erstellen Sie eine `.env`-Datei im Hauptverzeichnis für E-Mail-Zugangsdaten und die Basis-URL für QR-Codes:
GMAIL_APP_SENDER_EMAIL="e-mail"
GMAIL_APP_PASSWORD="passwort"
STREAMLIT_SERVER_BASE_URL="http://DEINE_LOKALE_IP:8501"

*Hinweis: Für Gmail ist ein [App-Passwort](https://support.google.com/accounts/answer/185833) erforderlich.*

### Lokales Setup
1.  **Virtuelle Umgebung erstellen und aktivieren:**
    ```bash
    cd /pfad/zum/projekt
    python3 -m venv .venv
    source .venv/bin/activate
    ```
2.  **Abhängigkeiten installieren:**
    ```bash
    pip install --upgrade pip
    pip install -r requirements.txt
    ```

## Starten der Streamlit-Anwendung
1.  Aktivieren Sie die virtuelle Umgebung: `source .venv/bin/activate`.
2.  Starten Sie die App:
    ```bash
    streamlit run main.py
    ```
3.  **Einmalige Authentifizierung:** Beim ersten Aufruf einer Google-Funktion (z.B. "Einladung erstellen") werden Sie im Browser zur Anmeldung weitergeleitet. Melden Sie sich mit dem Konto an, das Sie als Testnutzer hinzugefügt haben. Nach erfolgreicher Anmeldung wird eine `token.json`-Datei erstellt, die zukünftige Logins automatisiert.

## Funktionsübersicht der Streamlit-Anwendung
Die Navigation erfolgt über die Sidebar.

*   **🏠 Start:** Willkommensseite und Vorschau der geladenen Teilnehmer.
*   **📝 Einladung erstellen:** Erstellt Google Formulare für Event-Anmeldungen.
*   **✍️ Unterschriften sammeln & QR:** Generiert QR-Codes für die digitale Unterschriftenseite.
*   **📄 Teilnehmerliste & PDF Management:** Lädt Teilnehmerlisten und generiert PDFs.
*   **🧾 Abrechnung & Bericht einreichen:** Workflow zum Hochladen und Bündeln von Abrechnungsdokumenten.

## Separates Testen der Module im Terminal

Jedes Modul im `modules`-Ordner enthält einen `if __name__ == "__main__":`-Block für isolierte Tests.

### Allgemeine Vorbereitung für Modultests
1.  Aktivieren Sie die virtuelle Umgebung: `source .venv/bin/activate`.
2.  **Für Google-API-abhängige Module:** Führen Sie mindestens einmal den Anmeldevorgang in der Streamlit-App aus, damit eine gültige `token.json` im Hauptverzeichnis existiert.

### Modul: `form_creator.py`
*   **Voraussetzungen:** `client_secrets.json` und eine gültige `token.json`.
*   **Ausführung:** `python modules/form_creator.py`
*   **Erwartung:** Erstellt ein Test-Formular im Google Drive des authentifizierten Nutzers. (Hinweis: Der Test-Block muss ggf. angepasst werden, um die Authentifizierung zu laden).

### Modul: `google_sheets_reader.py`
*   **Voraussetzungen:** `client_secrets.json` und `token.json`. Passen Sie die `test_sheet_url` im Skript an.
*   **Ausführung:** `python modules/google_sheets_reader.py`
*   **Erwartung:** Liest Daten aus dem angegebenen Google Sheet. (Hinweis: Der Test-Block muss ggf. angepasst werden).

### Modul: `qr_generator.py`
*   **Voraussetzungen:** Keine externen Dienste für den Basistest.
*   **Ausführung:** `python modules/qr_generator.py`
*   **Erwartung:** Speichert `output/test_qr_code_from_qr_generator.png`.

### Modul: `sheet_loader.py`
*   **Voraussetzungen:** Keine externen Dienste.
*   **Ausführung:** `python modules/sheet_loader.py`
*   **Erwartung:** Erstellt `output/temp_test_participants_for_sheet_loader.csv`.

### Modul: `signature_capture.py`
*   **Voraussetzungen:** Keine externen Dienste für den Logiktest.
*   **Ausführung:** `python modules/signature_capture.py`
*   **Erwartung:** Verwendet `output/temp_test_signatures_for_inspection` für Dummy-Signaturen.

### Modul: `pdf_generator.py`
*   **Voraussetzungen:** Schriftarten, Logo.
*   **Ausführung:** `python modules/pdf_generator.py`
*   **Erwartung:** Erzeugt `output/TEST_Teilnehmerliste_Direkt.pdf`.

### Modul: `report_ai_generator.py`
*   **Voraussetzungen:** Ollama + Modell.
*   **Ausführung:** `python modules/report_ai_generator.py`
*   **Erwartung:** Erstellt eine `.docx`-Datei im `output`-Ordner.

### Modul: `submission_handler.py`
*   **Voraussetzungen:** Testdateien im `output`-Ordner. Für Drive/E-Mail sind Credentials (`client_secrets.json`, `token.json`, `.env`) nötig.
*   **Ausführung:** `python modules/submission_handler.py`
*   **Erwartung:** Erstellt Test-ZIP. Fragt interaktiv nach Drive-Upload und E-Mail-Versand. (Hinweis: Der Test-Block muss ggf. angepasst werden).

## Projektstruktur
[INTERNATIONAL_CLUB_EVENTMANAGEMENT]/
├── .venv/
├── data/
│ └── I-CLUB_LOGO.png
├── fonts/
│ └── DejaVuSans.ttf
│ └── ...
├── modules/
│ ├── auth.py
│ ├── form_creator.py
│ └── ...
├── output/
├── signatures/
├── .env
├── .gitignore
├── client_secrets.json # OAuth 2.0 Anmeldedaten
├── main.py
├── README.md
├── requirements.txt
└── token.json # Gespeicherter User-Login


## Verwendete externe Bibliotheken
Die Hauptabhängigkeiten sind in `requirements.txt` aufgelistet und umfassen unter anderem:
*   streamlit
*   pandas
*   google-api-python-client
*   google-auth-oauthlib
*   google-auth-httplib2
*   fpdf2
*   qrcode
*   Pillow
*   ollama
*   python-docx
*   streamlit-drawable-canvas
*   python-dotenv
