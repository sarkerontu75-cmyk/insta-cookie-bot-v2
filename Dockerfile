FROM python:3.9
RUN apt-get update && apt-get install -y chromium chromium-driver && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY . .
RUN pip install -r requirements.txt
CMD ["python", "main.py"]
