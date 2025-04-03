FROM python:3.11-slim

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
RUN rm requirements.txt

COPY monitor.py .

CMD ["uvicorn", "monitor:app", "--host", "0.0.0.0", "--port", "8080"]