FROM python:3.12-slim
WORKDIR /srv/taiba
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
ENV TAIBA_DATA_DIR=/srv/taiba/data
EXPOSE 8000
# Mount a volume on /srv/taiba/data so uploaded documents survive restarts.
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
