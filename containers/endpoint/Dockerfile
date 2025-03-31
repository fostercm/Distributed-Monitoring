FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    python3 python3-pip \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
RUN rm requirements.txt

COPY endpoint.py .

CMD ["uvicorn", "endpoint:app", "--host", "0.0.0.0", "--port", "8000"]