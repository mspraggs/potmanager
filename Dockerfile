FROM python:3.6.9-slim
COPY requirements.txt requirements.txt
RUN pip install -r requirements.txt
VOLUME ["/app/"]
WORKDIR /app/
ENTRYPOINT python main.py 1405