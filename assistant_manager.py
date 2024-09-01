import streamlit as st
import config
from openai import OpenAI
import os
import json
from assistant_api import (load_thread_details)
import time
import embedchain_rag
from embedchain_rag import create_embedchain_app,add_url_to_embedchain,add_file_to_embedchain,process_embedchain_data
from embedchain import App
# Initialize OpenAI client



client = OpenAI(api_key=config.API_KEY)


assistant_details = {
    "assistantId": "asst_xjtt9zGAk6Rszk6UQ3HN1Cfr",  # Use the existing assistant ID
}



# Function to save the assistant details to a JSON file

# def load_assistant_details(json_file="assistant.json"):
#     """Load the assistant details from the JSON file."""
#     if os.path.exists(json_file):
#         with open(json_file, "r") as file:
#             return json.load(file)
#     else:
#         return {"assistantId": "", "file_ids": []}

def save_assistant_details(assistant_details, json_file="assistant.json"):
    """Save the assistant details to the JSON file."""
    with open(json_file, "w") as file:
        json.dump(assistant_details, file, indent=4)

def update_assistant_with_files(assistant_id, new_file_id):
    try:
        # Retrieve the existing assistant details
        assistant_details = client.beta.assistants.retrieve(assistant_id=assistant_id)

        # Access existing file IDs
        existing_file_ids = assistant_details.file_ids if hasattr(assistant_details, 'file_ids') else []

        # Update the assistant with the new file ID
        updated_file_ids = existing_file_ids + [new_file_id]
        client.beta.assistants.update(
            assistant_id=assistant_id,
            file_ids=updated_file_ids
        )
        st.success(f"File attached to assistant with file ID: {new_file_id}")
    except Exception as e:
        st.error(f"Failed to update assistant with the new file: {e}")
  
            

def upload_file_and_update_assistant(assistant_id, file, assistant_details):
    try:
        # Upload the file to OpenAI
        response = client.files.create(file=file, purpose="assistants")
        new_file_id = response.id
        st.success(f"File '{file.name}' uploaded successfully with ID: {new_file_id}")

        # Append the new file ID to existing file IDs
        existing_file_ids = assistant_details.get("file_ids", [])
        assistant_details["file_ids"] = existing_file_ids + [new_file_id]

        # Save updated assistant details back to JSON
        save_assistant_details(assistant_details)

        st.success(f"File attached to assistant with file ID: {new_file_id}")
    except Exception as e:
        st.error(f"Failed to update assistant with the new file: {e}")


def handle_file_upload(assistant_id):
    # Simulate file upload and get the file IDs
    uploaded_files = st.file_uploader("Upload Files for the Assistant", accept_multiple_files=True, key="uploader")
    
    if uploaded_files:
        file_ids = []
        for uploaded_file in uploaded_files:
            # Read file as bytes and upload to OpenAI
            with st.spinner(f'Uploading {uploaded_file.name}...'):
                openai_client = OpenAI(api_key="your-api-key")
                response = openai_client.files.create(file=uploaded_file, purpose="assistants")
                file_ids.append(response.id)
        
        # Update the assistant with the new file IDs
        update_assistant_with_files(assistant_id, file_ids)
## Assistant config


def saveFileOpenAI(location):
    #Create OpenAI Client
    client = OpenAI(api_key=config.API_KEY)

    #Send File to OpenAI
    file = client.files.create(file=open(location, "rb"),purpose='assistants')

    # Delete the temporary file
    os.remove(location)

    #Return FileID
    return file.id


def load_details():
    with open('thread_details.json', 'r') as file:
        data = json.load(file)
    return data['assistant_id'], data['thread_id']









# Create a Streamlit app title and description


from embedchain.store.assistants import OpenAIAssistant

def load_assistant_details(json_file="assistant_details.json"):
    """Load assistant details from a JSON file."""
    try:
        with open(json_file, "r") as file:
            return json.load(file)
    except FileNotFoundError:
        print("JSON file not found.")
        return {}
    except json.JSONDecodeError:
        print("Error decoding JSON.")
        return {}

def initialize_app():
    # Load assistant details from JSON
    details = load_assistant_details()
    assistant_id = details.get('assistant_id', '')
    thread_id = details.get('thread_id', '')

    # Check if both IDs are present
    if not assistant_id or not thread_id:
        raise ValueError("Assistant ID or Thread ID missing from JSON file.")

    # Initialize the OpenAIAssistant with the fetched IDs
    assistant = OpenAIAssistant(assistant_id=assistant_id, thread_id=thread_id)
    return assistant

# Example usage
try:
    assistant = initialize_app()
    print("Assistant initialized successfully.")
except ValueError as e:
    print(e)

def add_url_to_assistant(assistant, url):
    if url:
        # This function would interact with the assistant to add the URL
        # Placeholder for adding a URL to an Embedchain assistant
        print(f"URL added to assistant: {url}")

def add_file_to_assistant(assistant, file_data):
    if file_data:
        # This function would handle file data and interact with the assistant
        # Placeholder for adding file data to an Embedchain assistant
        print("File data added to assistant")




def main():
    st.title("🪙 SealCoin Assistant")

    # Load thread details from file
    thread_details = load_thread_details()
    assistant_id = thread_details.get('assistant_id', '')

    # Input fields prepopulated with data from JSON
    assistant_id = st.text_input("Enter the Assistant ID if known:", value=assistant_id)

    # Create a thread if it's not already defined
    if 'thread' not in st.session_state:
        st.session_state['thread'] = client.beta.threads.create()

    # Get user input
    user_question = st.text_input("What is your question?")

    # Ensure assistant_id and user_question are provided
    if assistant_id and user_question:
        if st.button("Ask Assistant"):
            # Add the user's question to the thread
            client.beta.threads.messages.create(
                thread_id=st.session_state['thread'].id, 
                role="user", 
                content=user_question
            )

            # Run the assistant in the thread
            run = client.beta.threads.runs.create(
                thread_id=st.session_state['thread'].id, 
                assistant_id=assistant_id
            )

            # Show a spinner while waiting for the assistant's response
            with st.spinner('Waiting for the assistant\'s response...'):
                run_status = client.beta.threads.runs.retrieve(
                    thread_id=st.session_state['thread'].id,
                    run_id=run.id
                )
                while run_status.status != "completed":
                    time.sleep(1)
                    run_status = client.beta.threads.runs.retrieve(
                        thread_id=st.session_state['thread'].id,
                        run_id=run.id
                    )

            # Retrieve the messages from the thread
            messages = client.beta.threads.messages.list(st.session_state['thread'].id)
            last_message = next((m for m in messages.data if m.role == "assistant"), None)

            # Display the assistant's response
            if last_message:
                st.write(f"Assistant: {last_message.content[0].text.value}")
            else:
                st.write("No response received from the assistant.")
    
    st.title("EmbedChain Resource Aggregator")

    # Initialize the app (or assistant in a real scenario)
    assistant = initialize_app()

    # User input for the number of URLs they want to add
    num_links = st.number_input("Enter the number of URLs:", min_value=1, value=1, step=1)

    # Generate text input fields for each URL
    urls = []
    for i in range(num_links):
        url = st.text_input(f"Enter URL {i + 1}:", key=f'url_{i}')
        if url:  # Check if the URL is entered
            urls.append(url)

    # Button to add all URLs to the assistant
    if st.button("Add URLs to Assistant"):
        for url in urls:
            if url:  # Check again to avoid adding empty strings
                add_url_to_assistant(assistant, url)  # Adding each URL to the assistant
                st.success(f"URL added: {url}")

    # File upload and handling
    uploaded_file = st.file_uploader("Upload a file")
    if uploaded_file:
        file_data = uploaded_file.getvalue()
        if st.button("Upload File"):
            add_file_to_assistant(assistant, file_data)
            st.success("File uploaded and added successfully!")







if __name__ == "__main__":
    main()
