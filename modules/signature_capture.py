# modules/signature_capture.py

import streamlit as st
from streamlit_drawable_canvas import st_canvas
import os
from PIL import Image 
import pandas as pd 
import time 
import shutil 

def get_unsigned_participants(participants_df: pd.DataFrame, signatures_dir: str = "signatures") -> list:
    """
    Filtert die Teilnehmerliste und gibt eine sortierte Liste von Namen zurück,
    für die noch keine Unterschrift im angegebenen signatures_dir existiert.
    """
    unsigned_names = []
    if not isinstance(participants_df, pd.DataFrame) or "Name" not in participants_df.columns:
        return [] 
        
    os.makedirs(signatures_dir, exist_ok=True)

    all_names = sorted(list(participants_df["Name"].dropna().unique()))
    for name in all_names:
        safe_name_for_check = "".join(x for x in name if x.isalnum() or x in " _-").strip().replace(" ", "_")
        if not safe_name_for_check: 
            continue 
        signature_filename = f"{safe_name_for_check}.png"
        signature_path = os.path.join(signatures_dir, signature_filename)
        if not os.path.exists(signature_path):
            unsigned_names.append(name)
    return unsigned_names

def capture_signature(participants_df: pd.DataFrame):
    """
    Ermöglicht die Erfassung und Speicherung digitaler Unterschriften für Teilnehmer,
    die noch nicht unterschrieben haben.
    """
    if not isinstance(participants_df, pd.DataFrame) or participants_df.empty:
        st.warning("Teilnehmerliste ist leer oder ungültig.")
        return

    selection_key = "signature_capture_selected_name_module_v2" 
    force_redraw_key = "signature_capture_force_redraw_module_v2"

    if force_redraw_key not in st.session_state:
        st.session_state[force_redraw_key] = False
    
    if 'signature_just_saved_for' in st.session_state:
        del st.session_state.signature_just_saved_for
        st.session_state[force_redraw_key] = False 

    unsigned_names_list = get_unsigned_participants(participants_df)

    if not unsigned_names_list and not st.session_state[force_redraw_key]:
        st.success("🎉 Alle Teilnehmer auf der aktuellen Liste haben bereits unterschrieben!")
        st.balloons()
        return

    if st.session_state[force_redraw_key] and \
       selection_key in st.session_state and \
       st.session_state[selection_key] not in unsigned_names_list:
        st.session_state[force_redraw_key] = False

    current_selection = st.session_state.get(selection_key)
    default_index = 0
    options_for_selectbox = unsigned_names_list
    
    if st.session_state[force_redraw_key] and current_selection and current_selection not in unsigned_names_list:
        options_for_selectbox = sorted(list(set(unsigned_names_list + [current_selection]))) 
        if current_selection in options_for_selectbox:
            default_index = options_for_selectbox.index(current_selection)
    elif current_selection in unsigned_names_list:
        default_index = unsigned_names_list.index(current_selection)
    elif unsigned_names_list: 
        current_selection = unsigned_names_list[0]
        st.session_state[selection_key] = current_selection 
        default_index = 0
    
    if not options_for_selectbox and not current_selection: 
        st.info("Keine Namen zur Auswahl verfügbar.")
        return

    selected_name = st.selectbox(
        "Bitte Namen auswählen:", 
        options=options_for_selectbox, 
        key=selection_key,
        index=default_index 
    )

    if not selected_name: 
        return

    safe_selected_name_check = "".join(x for x in selected_name if x.isalnum() or x in " _-").strip().replace(" ", "_")
    signature_filename_check = f"{safe_selected_name_check}.png"
    signature_path_check_for_display = os.path.join("signatures", signature_filename_check)
    signature_actually_exists = os.path.exists(signature_path_check_for_display)


    if signature_actually_exists and not st.session_state[force_redraw_key]:
        st.info(f"✅ {selected_name} hat bereits unterschrieben.")
        try:
            st.image(signature_path_check_for_display, width=300)
        except Exception as e:
            st.warning(f"Konnte gespeicherte Unterschrift nicht anzeigen: {e}")
        if st.button(f"Unterschrift für {selected_name} erneut erfassen", key=f"btn_overwrite_{safe_selected_name_check}_module_v3"):
            st.session_state[force_redraw_key] = True
            st.session_state[selection_key] = selected_name 
            st.rerun() 
    else:
        st.markdown(f"### Unterschrift für: **{selected_name}**")
        stroke_width = 3
        stroke_color = "#000000"
        bg_color = "#FFFFFF"
        
        canvas_result = st_canvas(
            fill_color="rgba(255, 255, 255, 0)", 
            stroke_width=stroke_width,
            stroke_color=stroke_color,
            background_color=bg_color,
            update_streamlit=True, 
            height=250, 
            width=550,  
            drawing_mode="freedraw", 
            key=f"canvas_{safe_selected_name_check}_module_v3",
        )

        if canvas_result.image_data is not None:
            if st.button(f"Unterschrift für {selected_name} speichern", key=f"btn_save_{safe_selected_name_check}_module_v3", type="primary", use_container_width=True):
                signatures_dir_prod = "signatures"
                os.makedirs(signatures_dir_prod, exist_ok=True)
                safe_name_for_save = "".join(x for x in selected_name if x.isalnum() or x in " _-").strip().replace(" ", "_")
                signature_filename = f"{safe_name_for_save}.png"
                signature_path_prod = os.path.join(signatures_dir_prod, signature_filename)
                try:
                    img = Image.fromarray(canvas_result.image_data.astype('uint8'), 'RGBA')
                    final_img = Image.new("RGB", img.size, (255, 255, 255)) 
                    if img.mode == 'RGBA': final_img.paste(img, mask=img.split()[3]) 
                    else: final_img.paste(img)
                    final_img.save(signature_path_prod, "PNG")

                    st.session_state.signature_just_saved_for = selected_name 
                    st.session_state[force_redraw_key] = False 
                    st.success(f"✅ Unterschrift für {selected_name} gespeichert!")
                    st.balloons()
                    time.sleep(2.0) 
                    st.rerun() 
                except Exception as e:
                    st.error(f"Fehler beim Speichern: {e}")
        
        if st.session_state[force_redraw_key]:
             if st.button("Abbrechen (erneut erfassen)", key=f"btn_cancel_overwrite_{safe_selected_name_check}_module_v3"):
                 st.session_state[force_redraw_key] = False
                 st.rerun()

if __name__ == "__main__":
    print("Starte Testlauf für modules/signature_capture.py...")
    print("Teste primär die Funktion 'get_unsigned_participants'.")

    names_with_existing_signatures = ["Isabel Simmet", "Moritz Waldmann"]

    test_data = {
        'Name': ['Max Mustermann', 'Erika Musterfrau', 'John Doe', 'Jane Smith', 'Peter Pan'],
        'Mobile': ['111', '222', '333', '444', '555'],
        'Country': ['DE', 'AT', 'US', 'UK', 'DE'],
        'Type': ['ERASMUS', 'TUTOR', 'OTHER', 'ERASMUS', 'TUTOR'],
        'Email': ['max@test.com', 'erika@test.de', 'john@test.io', 'jane@test.co.uk', 'peter@test.com']
    }
    participants_test_df = pd.DataFrame(test_data)
    print("\n--- Test-Teilnehmerliste ---")
    print(participants_test_df)
    
    output_dir_for_tests = "output" 
    test_signatures_dir_for_inspection = os.path.join(output_dir_for_tests, "temp_test_signatures_for_inspection")
    
    print(f"\nErstelle/Verwende Test-Signaturordner: {test_signatures_dir_for_inspection}")
    if os.path.exists(test_signatures_dir_for_inspection):
        shutil.rmtree(test_signatures_dir_for_inspection)
    os.makedirs(test_signatures_dir_for_inspection, exist_ok=True)

    input(f"Test-Signaturordner '{test_signatures_dir_for_inspection}' wurde (neu) erstellt. Drücke Enter, um existierende Signaturen zu kopieren...")

    actual_signatures_source_dir = "signatures"
    copied_signatures_count = 0
    if os.path.exists(actual_signatures_source_dir):
        for name in names_with_existing_signatures:
            safe_name = "".join(x for x in name if x.isalnum() or x in " _-").strip().replace(" ", "_")
            source_signature_path = os.path.join(actual_signatures_source_dir, f"{safe_name}.png")
            destination_signature_path = os.path.join(test_signatures_dir_for_inspection, f"{safe_name}.png")
            
            if os.path.exists(source_signature_path):
                try:
                    shutil.copy2(source_signature_path, destination_signature_path)
                    print(f"  INFO: Existierende Signatur für '{name}' nach '{test_signatures_dir_for_inspection}' kopiert.")
                    copied_signatures_count +=1
                except Exception as e_copy:
                    print(f"  FEHLER beim Kopieren der Signatur für '{name}': {e_copy}")
            else:
                print(f"  WARNUNG: Existierende Signatur für '{name}' nicht in '{actual_signatures_source_dir}' gefunden (Pfad: {source_signature_path}).")
    else:
        print(f"WARNUNG: Quellordner für Signaturen '{actual_signatures_source_dir}' nicht gefunden. Es werden keine Signaturen kopiert.")

    if copied_signatures_count > 0:
        print(f"\n  {copied_signatures_count} existierende Signatur(en) in den Testordner kopiert.")
    else:
        print("\n  Keine existierenden Signaturen in den Testordner kopiert (oder Quellordner/Dateien nicht gefunden).")

    print("\n  Inhalt des Test-Signatur-Ordners:")
    for item in os.listdir(test_signatures_dir_for_inspection):
        print(f"    - {item}")

    input(f"Drücke Enter, um 'get_unsigned_participants' mit dem Ordner '{test_signatures_dir_for_inspection}' zu testen...")

    print(f"\n--- Teste get_unsigned_participants (Signaturen in '{test_signatures_dir_for_inspection}') ---")
    unsigned_list = get_unsigned_participants(participants_test_df, signatures_dir=test_signatures_dir_for_inspection)
    
    print(f"  Teilnehmer, für die Signaturen kopiert/simuliert wurden: {names_with_existing_signatures}")
    all_test_names_set = set(participants_test_df['Name'].tolist())
    signed_test_names_set = set(names_with_existing_signatures)
    expected_unsigned_set = all_test_names_set - signed_test_names_set
    print(f"  Erwartet nicht unterschrieben: {sorted(list(expected_unsigned_set))}")
    print(f"  Tatsächlich nicht unterschrieben laut Funktion: {unsigned_list}")

    if set(unsigned_list) == expected_unsigned_set:
        print("  TEST ERFOLGREICH: get_unsigned_participants funktioniert wie erwartet.")
    else:
        print("  TEST FEHLGESCHLAGEN: get_unsigned_participants liefert falsche Ergebnisse.")
    
    print(f"\n--- Test-Signaturordner '{test_signatures_dir_for_inspection}' bleibt für Inspektion bestehen. ---")
    input("Drücke Enter, um den Testlauf zu beenden (Ordner bleibt bestehen).")

    print("\nTestlauf für modules/signature_capture.py beendet.")