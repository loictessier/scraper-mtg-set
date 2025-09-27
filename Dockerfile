FROM mcr.microsoft.com/playwright/python:v1.49.1-jammy

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN playwright install chromium

CMD ["python", "main.py"]
