FROM python:3.7-alpine

RUN mkdir /opt/slata
WORKDIR /opt/slata

COPY requirements.txt .
COPY *.py ./
COPY config/secrets.cfg /etc/service/secrets.cfg
RUN pip install --no-cache-dir -r requirements.txt
RUN mkdir -p /usr/src/app/log

ENV SECRETS_CONFIG /etc/service/secrets.cfg
ENV DEBUG 1

CMD ["python3", "./app.py"]
