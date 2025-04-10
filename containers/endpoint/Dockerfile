FROM python:3.13-alpine

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
RUN rm requirements.txt

COPY endpoint.py .

CMD ["uvicorn", "endpoint:app", "--host", "0.0.0.0", "--port", "8000"]

# docker build -t endpoint .
# docker run -d -p <host_port>:8000 --name endpoint<host_port> endpoint