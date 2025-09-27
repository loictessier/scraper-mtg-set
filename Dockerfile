FROM mcr.microsoft.com/playwright/python:v1.49.1-jammy

ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN playwright install chromium

CMD ["gunicorn", "-b", "0.0.0.0:5000", "mtg_scraper_ui.app:app"]
