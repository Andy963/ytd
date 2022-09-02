FROM ubuntu:latest
WORKDIR /opt
ADD . /opt/ytd
RUN apt update && \
    apt install -y python3 &&  \
    apt install -y python3-pip && \
    pip3 install --no-cache --upgrade pip && \
    pip3 install -r /opt/ytd/requirements.txt && \
    apt-get clean
CMD ["python3", "/opt/ytd/main.py"]