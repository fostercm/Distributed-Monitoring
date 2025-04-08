# Copy the installed packages to a new image without the build dependencies
FROM python:3.11-slim
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
COPY dashboard.py .

EXPOSE 8501
CMD ["streamlit", "run", "dashboard.py"]