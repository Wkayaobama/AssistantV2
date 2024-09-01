import streamlit as st
from assistant_manager import load_all_assistant_info, get_assistant_info_by_id

def display_select_assistant_ui(assistant_manager):
    """Displays a UI component in Streamlit to select an assistant."""
    assistants = assistant_manager.load_all_assistant_info()
    if not assistants:
        st.write("No assistants available. Please create an assistant first.")
        return None

    assistant_options = {f"{assistant['name']} (ID: {assistant['id']}": assistant['id'] for assistant in assistants}
    selected_id = st.selectbox("Select an Assistant", options=list(assistant_options.keys()), format_func=lambda x: x)
    return assistant_options[selected_id]