FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .
RUN mkdir -p /app/uploads

# FastAPI runs on port 8000 by default
EXPOSE 8000

# Use Uvicorn to run the FastAPI app
CMD ["uvicorn", "main:app", "--host=0.0.0.0", "--port=8000", "--reload"]
