# Use Python 3.11 base image
FROM python:3.11

# Set working directory in the container
WORKDIR /app

# Copy requirements.txt file
COPY requirements.txt .

# Copy the builder.py, bae.py and usertasks directory
COPY builder.py .
COPY bae.py .
COPY usertasks /app/usertasks

# Copy the templates directory containing HTML files
COPY templates /app/templates

# Copy the static directory containing CSS and other static files
COPY static /app/static

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
