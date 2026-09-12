FROM python:3.11-slim

RUN useradd --create-home --shell /usr/sbin/nologin appuser
WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py ./

USER appuser

EXPOSE 9002

CMD ["python", "app.py"]
