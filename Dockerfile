FROM python:3.10.6
MAINTAINER ALERT <alexey.rubasheff@gmail.com>

# RUN apt-get update && apt-get -y install cron vim && apt-get -y clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY rozetka/requirements/requirements.txt /app/
RUN pip install --progress-bar=off --no-cache-dir -U pip setuptools wheel && pip install --progress-bar=off --no-cache-dir -r /app/requirements.txt

# COPY crontab /etc/cron.d/crontab
# RUN chmod 0644 /etc/cron.d/crontab

COPY entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

COPY rozetka /app/rozetka/

# RUN /usr/bin/crontab /etc/cron.d/crontab

ENV PYTHONIOENCODING=utf-8
ENV LC_ALL=en_US.UTF-8
ENV LANG=en_US.UTF-8
ENV LANGUAGE=en_US.UTF-8
ENV PYTHONUNBUFFERED=1

# run crond as main process of container
# CMD ["cron", "-f"]
CMD ["/app/entrypoint.sh"]