# Use an official Python runtime as a parent image
FROM python:3.10-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file into the container
COPY requirements.txt .

# Install all the packages from the requirements list we just perfected
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your project (api, scripts, etc.) into the container
COPY . .

# By default, run the API server on port 8000
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]