# Stage 1: Base build
# Based on https://www.docker.com/blog/how-to-dockerize-django-app/
FROM python:3.13-slim AS builder

RUN mkdir /talkshowguests
WORKDIR /talkshowguests

RUN pip install --upgrade pip

COPY requirements.txt /talkshowguests
RUN pip install --no-cache-dir -r requirements.txt

# Stage 2
FROM python:3.13-slim

# Install cron
RUN apt-get update && \
    apt-get install -y cron bsdmainutils && \
    rm -rf /var/lib/apt/lists/*

# Copy the Python dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.13/site-packages/ /usr/local/lib/python3.13/site-packages/
COPY --from=builder /usr/local/bin/ /usr/local/bin/

WORKDIR /talkshowguests

# Copy application code (excluding what's in .dockerignore)
COPY . .
RUN pip install .

RUN echo "#!/usr/bin/env bash" >> /run.sh && echo '\
. /etc/talkshowguests_env\n\
printenv\n\
echo\n\
cd /talkshowguests\n\
/usr/local/bin/talkshowguests \\\n\
    --report-telegram \\\n\
    --crawler-results /data/latest-result.jsonlines \\\n\
    --history-file /data/history.json'\
>> /run.sh
RUN chmod +x /run.sh

RUN chmod +x container-entrypoint.sh
ENTRYPOINT ["/talkshowguests/container-entrypoint.sh"]
