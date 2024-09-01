from openai import OpenAI
import config
import os
import time
import json
import tempfile
import shutil
import asyncio
client = OpenAI(api_key=config.API_KEY)
def createAssistant(file_ids, title):
    #Create the OpenAI Client Instance
    client = OpenAI(api_key=config.API_KEY)

    #GET Instructions saved in the Settings.py File (We save the instructions there for easy access when modifying)
    instructions = """
    You are a helpful assistant. Use your knowledge base to answer user questions.
    """

    #The GPT Model for the Assistant (This can also be updated in the settings )
    model = "gpt-4-turbo"

    #Only Retireval Tool is relevant for our use case
    tools = [{"type": "file_search"}]

    ##CREATE VECTOR STORE
    vector_store = client.beta.vector_stores.create(name=title,file_ids=file_ids)
    tool_resources = {"file_search": {"vector_store_ids": [vector_store.id]}}

    #Create the Assistant
    assistant = client.beta.assistants.create(
    name=title,
    instructions=instructions,
    model=model,
    tools=tools,
    tool_resources=tool_resources
    )

    #Return the Assistant ID
    return assistant.id,vector_store.id



def saveFileOpenAI(location):
    #Create OpenAI Client
    client = OpenAI(api_key=config.API_KEY)

    #Send File to OpenAI
    file = client.files.create(file=open(location, "rb"),purpose='assistants')

    # Delete the temporary file
    os.remove(location)

    #Return FileID
    return file.id




def startAssistantThread(prompt,vector_id):
    #Initiate Messages
    messages = [{"role": "user", "content": prompt}]
    #Create the OpenAI Client
    client = OpenAI(api_key=config.API_KEY)
    #Create the Thread
    tool_resources = {"file_search": {"vector_store_ids": [vector_id]}}
    thread = client.beta.threads.create(messages=messages,tool_resources=tool_resources)

    return thread.id



def runAssistant(thread_id, assistant_id):
    #Create the OpenAI Client
    client = OpenAI(api_key=config.API_KEY)
    run = client.beta.threads.runs.create(thread_id=thread_id,assistant_id=assistant_id)
    return run.id



def checkRunStatus(thread_id, run_id):
    client = OpenAI(api_key=config.API_KEY)
    run = client.beta.threads.runs.retrieve(thread_id=thread_id,run_id=run_id)
    return run.status



def retrieveThread(thread_id):
    client = OpenAI(api_key=config.API_KEY)
    thread_messages = client.beta.threads.messages.list(thread_id)
    list_messages = thread_messages.data
    thread_messages = []
    for message in list_messages:
        obj = {}
        obj['content'] = message.content[0].text.value
        obj['role'] = message.role
        thread_messages.append(obj)
    return thread_messages[::-1]



def addMessageToThread(thread_id, prompt):
    """Adds a message to an existing thread and returns True if successful."""
    try:
        client = OpenAI(api_key=config.API_KEY)
        client.beta.threads.messages.create(thread_id=thread_id, role="user", content=prompt)
        return True
    except Exception as e:
        print(f"Error adding message to thread: {e}")
        return False



## Update assistant

def update_assistant(assistant_id, new_name, new_description):
    """Updates the OpenAI Assistant configuration."""
    try:
        updated_assistant = client.beta.assistants.update(
            assistant_id=assistant_id,
            name=new_name,
            description=new_description,
            model="gpt-4-turbo",  # Assuming you want to keep/update the model as well
        )
        return updated_assistant
    except Exception as e:
        print(f"Failed to update assistant: {str(e)}")
        return None

def create_and_run_thread(assistant_id, user_prompt):
    """Creates a thread and runs the OpenAI Assistant."""
    try:
        chat = client.beta.threads.create(
            messages=[{"role": "user", "content": user_prompt}]
        )
        run = client.beta.threads.runs.create(thread_id=chat.id, assistant_id=assistant_id)
        print(f"Run Created: {run.id}")

        # Wait for the run to complete
        while run.status != "completed":
            run = client.beta.threads.runs.retrieve(thread_id=chat.id, run_id=run.id)
            print(f"Run Status: {run.status}")
            time.sleep(0.5)  # Adjust as necessary

        if run.status == "completed":
            print("Run Completed!")

        # Retrieve and print the latest message from the assistant
        message_response = client.beta.threads.messages.list(thread_id=chat.id)
        messages = message_response.data
        if messages and messages[-1].role == 'assistant':
            print("Response:", messages[-1].content[0].text.value)
        else:
            print("No response found.")
    except Exception as e:
        print(f"Error during thread creation or execution: {str(e)}")


import json

def save_thread_details(thread_id, assistant_id):
    """Atomically save thread and assistant details to a JSON file."""
    temp_fd, temp_path = tempfile.mkstemp()
    try:
        with os.fdopen(temp_fd, 'w') as tmp_file:
            json.dump({"thread_id": thread_id, "assistant_id": assistant_id}, tmp_file, indent=4)
        shutil.move(temp_path, "thread_details.json")  # Atomically replace the old file
    except Exception as e:
        os.unlink(temp_path)
        print(f"Failed to save thread details: {e}")

def load_thread_details():
    """Load thread and assistant details from a JSON file with retries for robustness."""
    retry_attempts = 3
    while retry_attempts > 0:
        try:
            with open("thread_details.json", "r") as file:
                return json.load(file)
        except json.JSONDecodeError:
            print("Error decoding JSON from the file, retrying...")
            retry_attempts -= 1
        except FileNotFoundError:
            print("The file doesn't exist.")
            return None
        except Exception as e:
            print(f"An error occurred: {e}")
            return None
    print("Failed to load thread details after several attempts.")
    return None



def create_vector_store(vector_store_name):
    """Create a new vector store in OpenAI."""
    response = client.VectorStore.create(name=vector_store_name)
    return response['id']

def upload_files_to_openai(file_locations):
    file_ids = []
    for location in file_locations:
        with open(location, "rb") as file:
            response = client.files.create(file=file, purpose='fine-tune')  # Adjust purpose as needed
            file_ids.append(response['id'])
    return file_ids

def add_files_to_vector_store(vector_store_id, file_ids):
    """Add files to the specified vector store."""
    response = client.VectorStore.add_files(vector_store_id=vector_store_id, file_ids=file_ids)
    return response['id'], response['status']

def get_vector_store_by_name(vector_store_name):
    """Retrieve a vector store by name or create if it doesn't exist."""
    try:
        # List all vector stores and find by name
        response = client.beta.vector_stores.list()
        for vector_store in response.data:
            if vector_store.name == vector_store_name:
                return vector_store.id
        
        # If not found, create a new vector store
        new_vector_store = client.beta.vector_stores.create(name=vector_store_name)
        return new_vector_store.id
    except Exception as e:
        print(f"Error managing vector store: {e}")
        return None
# Example usage
#thread_id = "thread_XoO7X1cBQHyMuj9qcj2rtXms"
#assistant_id = "asst_xjtt9zGAk6Rszk6UQ3HN1Cfr"

def update_assistant_file_ids(assistant_id, new_file_ids, json_file="assistant_details.json"):
    """
    Update the assistant with new file IDs and save the updated details to a JSON file.
    """
    try:
        # Load the existing assistant details from the JSON file
        if os.path.exists(json_file):
            with open(json_file, "r") as file:
                assistant_details = json.load(file)
        else:
            assistant_details = {}

        # Get the existing file IDs or initialize an empty list if none exist
        existing_file_ids = assistant_details.get("file_ids", [])

        # Append the new file IDs to the existing ones
        updated_file_ids = existing_file_ids + new_file_ids

        # Update the assistant details
        client.beta.assistants.update(assistant_id, {
            "file_ids": updated_file_ids
        })

        # Save the updated assistant details back to the JSON file
        assistant_details["assistant_id"] = assistant_id
        assistant_details["file_ids"] = updated_file_ids
        with open(json_file, "w") as file:
            json.dump(assistant_details, file, indent=4)

        return True
    except Exception as e:
        print(f"Failed to update assistant or save details: {e}")
        return False


async def wait_for_file_release(file_path, timeout=10):
    """Waits for the file to be released by any process."""
    start_time = time.time()
    while True:
        try:
            with open(file_path, 'a'):  # Try opening the file for appending
                break  # If successful, break the loop
        except IOError:
            if time.time() - start_time > timeout:
                raise TimeoutError(f"File {file_path} is still in use after {timeout} seconds.")
            await asyncio.sleep(0.5)  # Wait a bit before trying again 
    
# Example usage:
""" assistant_id = "asst_xjtt9zGAk6Rszk6UQ3HN1Cfr"
new_name = "SEALCOINV3"
new_description = "Hi How Are You?" """




# Update Assistant Configuration
# update_assistant(assistant_id, new_name, new_description)

# Create and Run Thread
#user_prompt = "tell me about the best jobs in AI"
#create_and_run_thread(assistant_id, user_prompt)