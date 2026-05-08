FROM python:3.12-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy worker code
COPY extract.py transform.py load.py handler.py ./

# Run as non-root user
RUN useradd -m worker && chown -R worker:worker /app
USER worker

CMD ["python", "handler.py"]