FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/python ./src/python

ENV PYTHONPATH=/app/src/python
ENV MAX_ASSETS=10

ENTRYPOINT ["python", "src/python/main.py"]
