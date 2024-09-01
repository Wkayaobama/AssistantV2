import streamlit as st
import os
import time
import asyncio
from assistant_api import (
    createAssistant, saveFileOpenAI, startAssistantThread, runAssistant,
    checkRunStatus, retrieveThread, addMessageToThread,save_thread_details,load_thread_details,create_vector_store,upload_files_to_openai,
    add_files_to_vector_store,get_vector_store_by_name,update_assistant_file_ids,wait_for_file_release
)
import time

def display_thread_messages(thread_messages):
    """Display messages from the thread based on visibility state."""
    if st.session_state.get('show_messages', True):
        for message in thread_messages:
            role = 'User' if message['role'] == 'user' else 'Assistant'
            st.write(f"{role} Message: {message['content']}")

def process_run(thread_id, assistant_id):
    """Process the thread and continuously check the status until completion."""
    run_id = runAssistant(thread_id, assistant_id)
    status = 'running'
    while status != 'completed':
        with st.spinner('Waiting for assistant response...'):
            time.sleep(10)
            status = checkRunStatus(thread_id, run_id)
    thread_messages = retrieveThread(thread_id)
    display_thread_messages(thread_messages)

async def main():
    st.title("🪙 SealCoin Assistant")

    # Load thread details from file
    thread_details = load_thread_details()
    thread_id = ""
    assistant_id = ""
    if thread_details:
        thread_id = thread_details.get('thread_id', '')
        assistant_id = thread_details.get('assistant_id', '')

    # Input fields prepopulated with data from JSON
    thread_id = st.text_input("Enter existing Thread ID to continue the conversation:", value=thread_id)
    assistant_id = st.text_input("Enter the Assistant ID if known:", value=assistant_id)

    if st.button('Load Conversation'):
        if thread_id:
            thread_messages = retrieveThread(thread_id)
            if thread_messages:
                display_thread_messages(thread_messages)
                st.session_state['thread_id'] = thread_id
                st.session_state['assistant_id'] = assistant_id
            else:
                st.error("Failed to load messages or no messages in the thread.")
        else:
            st.error("Please provide a Thread ID.")

    if st.button('Initialize New Assistant'):
        title = st.text_input("Enter the title for a new Assistant", key='new_title')
        initiation = st.text_input("Enter the first question to start a new conversation", key='new_initiation')

        uploaded_files = st.file_uploader("Upload Files for the Assistant", accept_multiple_files=True, key="uploader")
        file_locations = []
        if uploaded_files and title and initiation:
            for uploaded_file in uploaded_files:
                location = f"temp_file_{uploaded_file.name}"
                with open(location, "wb") as f:
                    f.write(uploaded_file.getvalue())
                file_locations.append(location)
                st.success(f'File {uploaded_file.name} has been uploaded successfully.')

            # Upload file and create assistant
            with st.spinner('Processing your file and setting up the assistant...'):
                file_ids = []
                for location in file_locations:
                    await wait_for_file_release(location)
                    file_id = saveFileOpenAI(location)
                    file_ids.append(file_id)
                assistant_id, vector_id = createAssistant(file_ids, title)

            # Start the Thread
            thread_id = startAssistantThread(initiation, assistant_id)

    if 'thread_id' in st.session_state:
        follow_up = st.text_input("Enter your follow-up question")
        if st.button("Send Follow-up"):
            success = addMessageToThread(st.session_state['thread_id'], follow_up)
            if success:
                st.success("Message added to the conversation.")
                process_run(st.session_state['thread_id'], st.session_state['assistant_id'])
            else:
                st.error("Failed to add message to the conversation.")

    if st.button('Clear Conversation'):
        st.session_state.pop('thread_id', None)
        st.session_state.pop('assistant_id', None)
        save_thread_details(None, None)  # Clear the file
        st.write("Conversation cleared.")

    # File Upload Management
    uploaded_files = st.file_uploader("Upload Files to Assistant", accept_multiple_files=True, key="uploader_assistant")
    if uploaded_files and assistant_id:
        file_locations = []
        for uploaded_file in uploaded_files:
            location = f"temp_file_{uploaded_file.name}"
            with open(location, "wb") as f:
                f.write(uploaded_file.getvalue())
            file_locations.append(location)
            st.success(f'File {uploaded_file.name} has been uploaded successfully.')

        if st.button("Upload and Attach Files to Assistant"):
            try:
                file_ids = []
                for location in file_locations:
                    await wait_for_file_release(location)
                    file_id = saveFileOpenAI(location)
                    file_ids.append(file_id)
                success = update_assistant_file_ids(assistant_id, file_ids)
                if success:
                    st.success("Files uploaded and attached to the assistant successfully!")
                else:
                    st.error("Failed to upload files to the assistant.")
            except Exception as e:
                st.error(f"Error during file upload: {e}")
            finally:
                await asyncio.sleep(2)  # Additional delay to ensure the file is fully released
                for location in file_locations:
                    try:
                        os.remove(location)
                    except Exception as e:
                        st.error(f"Failed to remove temporary file {location}: {e}")

if __name__ == "__main__":
    asyncio.run(main())