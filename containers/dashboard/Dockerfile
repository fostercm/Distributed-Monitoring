FROM python:3.13-slim-bullseye
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY dashboard.py .

CMD ["streamlit", "run", "dashboard.py"]