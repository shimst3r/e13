FROM python:3.7.6-slim-buster as base

FROM base as builder
RUN apt-get update && apt-get install -y gcc build-essential
RUN mkdir /install
WORKDIR /install
COPY requirements.txt /requirements.txt
RUN pip install --install-option="--prefix=/install" -r /requirements.txt

FROM base
COPY --from=builder /install /usr/local
COPY e13_server /app
COPY postings.db postings.db
WORKDIR /app
EXPOSE 8000
CMD ["gunicorn", "server:APP", "-w", "4", "-k", "uvicorn.workers.UvicornWorker"]