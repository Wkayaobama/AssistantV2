# Use the official lightweight Python image
FROM python:3.8-slim

# Set environment variables
ENV PYTHONUNBUFFERED True

# Create a directory for the app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . .

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
# Create config.py during the build
RUN echo "API_KEY = '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'" > /app/config.py

# Make port 8080 available to the world outside this container
EXPOSE 8080

# Define the command to run your app
CMD ["streamlit", "run", "assistant_manager.py", "--server.port=8080", "--server.enableCORS=false"]
