import config
from embedchain import App
import os


os.environ["OPENAI_API_KEY"] = "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"

def create_embedchain_app():
    return App

def add_url_to_embedchain(app, url):
    if url:
        app.add("web_page", url)

def add_file_to_embedchain(app, file_content):
    app.add("file_type", file_content)  # Replace 'file_type' with actual supported type

def process_embedchain_data(app):
    return app.process()  # Assuming there is a process method
