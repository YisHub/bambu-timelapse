FROM python:3.12-slim

WORKDIR /app

COPY requirements_timelapse.txt .
RUN pip install --no-cache-dir -r requirements_timelapse.txt

COPY bambu_timelapse.py .

CMD ["python", "-u", "bambu_timelapse.py"]
