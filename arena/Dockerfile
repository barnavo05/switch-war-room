FROM python:3.12-slim
WORKDIR /app
COPY app/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir -r /tmp/requirements.txt
# The app folder is mounted as a volume (see docker-compose.yml), so when the
# Blue agent edits app.py, Flask reloads it live. No rebuild needed.
CMD ["flask", "--app", "app", "run", "--host", "0.0.0.0", "--port", "5050", "--reload"]
