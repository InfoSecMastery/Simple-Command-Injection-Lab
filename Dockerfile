# =============================================================================
#  InfoSec Mastery - Command Injection lab ("network tools" ping page).
#  EDUCATIONAL USE ONLY - run only on your own isolated machine.
# =============================================================================
FROM python:3.12-slim

RUN apt-get update \
 && apt-get install -y --no-install-recommends iputils-ping \
 && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY app.py .

# MODE=vuln (injectable) by default; set MODE=secure to see the fix.
ENV MODE=vuln
EXPOSE 8081
CMD ["python", "app.py"]
