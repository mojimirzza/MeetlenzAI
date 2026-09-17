FROM python:3.12-slim
WORKDIR /app
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
COPY pyproject.toml ./
RUN pip install --no-cache-dir --upgrade pip && pip install --no-cache-dir .
COPY app ./app
COPY prompts ./prompts
COPY configs ./configs
COPY scripts ./scripts
RUN mkdir -p data
EXPOSE 8000
CMD ["python", "-m", "app.main"]
