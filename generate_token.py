# generate_token.py
import os
from google_auth_oauthlib.flow import InstalledAppFlow

CLIENT_SECRETS_FILE = "client_secrets_desktop.json" 
SCOPES = ["https://www.googleapis.com/auth/drive", "https://www.googleapis.com/auth/forms.body", "https://www.googleapis.com/auth/spreadsheets.readonly"]
TOKEN_FILE = "token.json"

def generate_token():
    print(f"--- Starte die Erstellung von '{TOKEN_FILE}' ---")
    if not os.path.exists(CLIENT_SECRETS_FILE):
        print(f"FEHLER: '{CLIENT_SECRETS_FILE}' nicht gefunden.")
        return
    flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRETS_FILE, SCOPES)
    creds = flow.run_local_server(port=0)
    with open(TOKEN_FILE, 'w') as token:
        token.write(creds.to_json())
    print(f"\n--- ERFOLG! '{TOKEN_FILE}' wurde erstellt. ---")

if __name__ == "__main__":
    generate_token()