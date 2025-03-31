## Multi stage build

# Build Package requirements
FROM python:alpine AS builder

# Install system dependencies needed for psutil and other packages
RUN apk add --no-cache gcc musl-dev libffi-dev

# Install python dependencies
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt
RUN rm requirements.txt

# Copy the installed packages to a new image without the build dependencies
FROM python:alpine
COPY --from=builder /usr/local /usr/local
COPY scraper.py .
CMD ["python3", "-u", "scraper.py"]