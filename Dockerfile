FROM python:3.8-slim

RUN mkdir -p /code
ADD . /code
WORKDIR /code
RUN apt update && \
    apt install -y ffmpeg && \
    pip3 install --no-cache --upgrade pip && \
    pip3 install -r requirements.txt && \
    apt-get clean && rm -rf /root/.cache && \
    apt-get autoclean && \
    rm -rf /tmp/* /var/lib/apt/* /var/cache/* /var/log/*
CMD ["python3", "main.py"]
