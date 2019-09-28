FROM python:3.6.9-slim
COPY . /app
RUN pip install -r /app/requirements.txt
CMD python /app/main.py --dry-run 1405