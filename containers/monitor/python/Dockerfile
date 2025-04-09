FROM python:3.13-alpine

COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
RUN rm requirements.txt

COPY monitor.py .

CMD ["uvicorn", "monitor:app", "--host", "0.0.0.0", "--port", "8080"]

# docker build -t python_monitor .
# docker container run -v /var/run/docker.sock:/var/run/docker.sock -p 8080:8080 --name python_monitor python_monitor