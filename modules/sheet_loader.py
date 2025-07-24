# modules/sheet_loader.py

import pandas as pd
import streamlit as st 
import os

@st.cache_data 

def load_participants_from_csv(filepath: str = os.path.join("data", "teilnehmer.csv")) -> pd.DataFrame:
    """
    Lädt Teilnehmerdaten aus einer CSV-Datei und verarbeitet sie für die Standardanzeige.
    Gibt einen DataFrame mit den Spalten ['Name', 'Mobile', 'Country', 'Type', 'Email'] zurück.
    Wirft FileNotFoundError, wenn die Datei nicht existiert.
    Gibt einen leeren DataFrame zurück, wenn die Datei leer ist oder ein Lesefehler auftritt.
    """
    final_expected_cols_after_processing = ['Name', 'Mobile', 'Country', 'Type', 'Email'] 

    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Datei '{filepath}' nicht gefunden.")
    
    try:
        df = pd.read_csv(filepath, dtype=str) 
    except pd.errors.EmptyDataError:
        print(f"INFO (sheet_loader): Datei '{filepath}' ist leer.")
        return pd.DataFrame(columns=final_expected_cols_after_processing)
    except Exception as e:
        raise IOError(f"Fehler beim Lesen der CSV-Datei '{filepath}': {e}") from e
    
    df = df.fillna('') 
    df_processed = process_dataframe_for_display(df.copy()) 
    return df_processed

@st.cache_data 
def process_dataframe_for_display(input_df: pd.DataFrame) -> pd.DataFrame:
    """
    Nimmt einen rohen DataFrame, kombiniert Namen, wählt relevante Spalten aus, 
    benennt sie um und stellt sicher, dass die finalen Spalten 
    ['Name', 'Mobile', 'Country', 'Type', 'Email'] existieren.
    """
    final_return_cols = ['Name', 'Mobile', 'Country', 'Type', 'Email'] 

    if not isinstance(input_df, pd.DataFrame):
        raise TypeError("Eingabe muss ein Pandas DataFrame sein.")

    if input_df.empty:
        return pd.DataFrame(columns=final_return_cols)

    df = input_df.copy() 
    
    source_to_target_map = {
        'First Name': 'First Name', 
        'Last Name': 'Last Name',   
        'Phone Number': 'Mobile', 
        'Country of Origin': 'Country',
        'Exchange Type': 'Type',
        'E-Mail-Adresse': 'Email'  
    }

    for source_col in source_to_target_map.keys():
        if source_col in df.columns:
            df[source_col] = df[source_col].astype(str).fillna('')
        else:
            df[source_col] = pd.Series([''] * len(df), dtype=str, index=df.index)

    df_processed = pd.DataFrame(index=df.index)
    df_processed['Name'] = (df['First Name'] + " " + df['Last Name']).str.strip()
    
    df_processed['Mobile'] = df.get('Phone Number', df.get('Phone Number', pd.Series([''] * len(df), dtype=str, index=df.index))).astype(str).fillna('') # Handhabt beide Varianten
    df_processed['Country'] = df['Country of Origin']
    df_processed['Type'] = df['Exchange Type']
    df_processed['Email'] = df['E-Mail-Adresse'] 
    
    for col in final_return_cols:
        if col not in df_processed.columns:
            df_processed[col] = pd.Series([''] * len(df_processed) if not df_processed.empty else [''] * len(df), dtype=str, index=df_processed.index)
            
    return df_processed[final_return_cols]


if __name__ == "__main__":
    print("Starte Testlauf für modules/sheet_loader.py...")

    test_raw_data = {
        'First Name': ['Max', 'Erika', 'Ohnevorname', 'John', 'Test'],
        'Last Name': ['Mustermann', 'Musterfrau', 'Ohnenachname', 'Doe', 'Name'],
        'Phone Number ': ['+49123', '', '+49789', '12345', '43432'], 
        # 'Phone Number': ['+49123', '', '+49789', '12345', ''],
        'Country of Origin': ['Germany', 'Austria', 'NoCountry', 'USA', 'Spain'],
        'Exchange Type': ['ERASMUS', 'TUTOR', 'OTHER', None, ''],
        'E-Mail-Adresse': ['max@test.com', 'erika@test.de', 'test@test.ch', 'john@doe.com', 'test@test.de'],
        'Zusatzspalte': ['info1', 'info2', 'info3', 'info4', 'info5']
    }
    raw_df_for_process = pd.DataFrame(test_raw_data)
    print("\n--- Teste process_dataframe_for_display ---")
    print("Roh-DataFrame für process_dataframe_for_display:")
    print(raw_df_for_process)
    
    processed_df = process_dataframe_for_display(raw_df_for_process.copy())
    print("\nVerarbeiteter DataFrame von process_dataframe_for_display:")
    print(processed_df)
    expected_cols = ['Name', 'Mobile', 'Country', 'Type', 'Email']
    print(f"Erwartete Spalten im Ergebnis: {expected_cols}")
    print(f"Tatsächliche Spalten im Ergebnis: {processed_df.columns.tolist()}")
    
    all_expected_cols_present = all(col in processed_df.columns for col in expected_cols)
    correct_number_of_rows = len(processed_df) == len(raw_df_for_process)

    if all_expected_cols_present and correct_number_of_rows:
        print("  Test für process_dataframe_for_display scheint erfolgreich (Strukturprüfung).")
    else:
        if not all_expected_cols_present:
            print("  FEHLER: Nicht alle erwarteten Spalten im Ergebnis von process_dataframe_for_display!")
        if not correct_number_of_rows:
            print("  FEHLER: Anzahl der Zeilen hat sich unerwartet geändert in process_dataframe_for_display!")

    temp_csv_dir = "output" 
    os.makedirs(temp_csv_dir, exist_ok=True)
    temp_csv_filepath = os.path.join(temp_csv_dir, "temp_test_participants_for_sheet_loader.csv")
    
    raw_df_for_process.to_csv(temp_csv_filepath, index=False)
    print(f"\nTest-CSV-Datei für Inspektion erstellt: '{temp_csv_filepath}'")
    input(f"Überprüfe die Datei '{temp_csv_filepath}'. Drücke Enter, um load_participants_from_csv zu testen...")

    print("\n--- Teste load_participants_from_csv ---")
    try:
        df_from_csv_load = load_participants_from_csv(filepath=temp_csv_filepath)
        print("\nVerarbeiteter DataFrame von load_participants_from_csv:")
        print(df_from_csv_load)
        print(f"Erwartete Spalten im Ergebnis: {expected_cols}")
        print(f"Tatsächliche Spalten im Ergebnis: {df_from_csv_load.columns.tolist()}")
        
        all_expected_cols_present_csv = all(col in df_from_csv_load.columns for col in expected_cols)
        correct_number_of_rows_csv = len(df_from_csv_load) == len(raw_df_for_process)

        if all_expected_cols_present_csv and correct_number_of_rows_csv:
            print("  Test für load_participants_from_csv scheint erfolgreich.")
        else:
            if not all_expected_cols_present_csv:
                print("  FEHLER: Nicht alle erwarteten Spalten im Ergebnis von load_participants_from_csv!")
            if not correct_number_of_rows_csv:
                print("  FEHLER: Anzahl der Zeilen beim CSV-Laden unerwartet geändert!")
                
    except Exception as e:
        print(f"  FEHLER im Test für load_participants_from_csv: {e}")
    
    print(f"\nDie Test-CSV-Datei '{temp_csv_filepath}' bleibt für die Inspektion erhalten.")
    print("Bitte lösche sie manuell, wenn sie nicht mehr benötigt wird.")
    print("\nTestlauf für modules/sheet_loader.py beendet.")