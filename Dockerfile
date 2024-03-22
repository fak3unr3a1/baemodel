# Use Python 3.11 base image
FROM python:3.11

# Set working directory in the container
WORKDIR /app

# Copy requirements.txt file
COPY requirements.txt .

# Install Python dependencies
RUN pip install -r requirements.txt

# Download the English language model for spaCy
RUN python -m spacy download en_core_web_sm

# Copy your Python server file (assuming it's named server.py)
COPY server.py .

# Expose port 8000
EXPOSE 8000

# Command to run the Python server
CMD ["python", "server.py"]
