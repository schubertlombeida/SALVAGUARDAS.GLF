FROM python:3.11-slim
WORKDIR /app
COPY requirements-web.txt ./
RUN pip install --no-cache-dir -r requirements-web.txt && useradd -m -u 1000 appuser
COPY --chown=appuser:appuser app ./app
COPY --chown=appuser:appuser src ./src
USER appuser
ENV GLF_HOST=0.0.0.0 PORT=7860 PYTHONUNBUFFERED=1
EXPOSE 7860
CMD ["python", "-m", "app.wsgi"]
