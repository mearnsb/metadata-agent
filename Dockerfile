#FROM tiangolo/uvicorn-gunicorn:python3.8-slim
FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app/
COPY *.py /app/
COPY requirements.txt /app/
#RUN pip install -U pip && pip install -r requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

# As an example here we're running the web service with one worker on uvicorn.
#ENTRYPOINT gunicorn --bind :$PORT --workers 1 --threads 2 --timeout 0 main:app
#CMD exec uvicorn main:app --host 0.0.0.0 --port 1234 --workers 1
CMD exec uvicorn main:api --host 0.0.0.0 --port 1234 --workers 1 --log-level warning
#CMD exec uvicorn main:api --reload --port 1234 --log-level warning
