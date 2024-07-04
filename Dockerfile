FROM python:3.9

LABEL authors="Barat Ali Hassanzada, Joma Mohammadi"

WORKDIR /app

# Copy and install requirements first for efficient caching
COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire application
COPY . .

# Expose the port where FastAPI app will run
EXPOSE 8000

# Command to run the FastAPI application using Uvicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
